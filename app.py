import os
import time
from io import BytesIO
from pathlib import Path
from typing import Any

import requests
from docx import Document
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from pptx import Presentation
from pypdf import PdfReader

load_dotenv()

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024

MAX_PROMPT_LENGTH = 4_000
MAX_EXTRACTED_TEXT = 100_000

UPLOAD_TYPES = {
    "document": {
        "label": "Document",
        "extensions": {".pdf", ".docx", ".txt"},
        "formats": "PDF · DOCX · TXT",
        "accept": ".pdf,.docx,.txt",
        "description": "Reports, proposals, essays, plans, and other written work.",
        "focus": "e.g. clarity and structure",
    },
    "transcript": {
        "label": "Transcript",
        "extensions": {".txt", ".srt", ".vtt", ".docx"},
        "formats": "TXT · SRT · VTT · DOCX",
        "accept": ".txt,.srt,.vtt,.docx",
        "description": "Meetings, interviews, conversations, captions, and recorded sessions.",
        "focus": "e.g. key themes and actions",
    },
    "powerpoint": {
        "label": "PowerPoint",
        "extensions": {".pptx"},
        "formats": "PPTX",
        "accept": ".pptx",
        "description": "Presentation slides, speaker notes, pitch decks, and briefings.",
        "focus": "e.g. story flow and messaging",
    },
}


def call_model(prompt: str, demo_feedback: str | None = None) -> str:
    """Send a prompt to the configured model, or return local demo feedback."""
    model_url = os.getenv("MODEL_API_URL", "").strip()
    if not model_url:
        time.sleep(0.4)
        return demo_feedback or (
            "This is a demo response. Your Python website is working. Add the "
            "local model address to .env as MODEL_API_URL when it is ready."
        )

    headers = {"Content-Type": "application/json"}
    api_key = os.getenv("MODEL_API_KEY", "").strip()
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    response = requests.post(model_url, json={"prompt": prompt}, headers=headers, timeout=60)
    response.raise_for_status()
    data: dict[str, Any] = response.json()
    for field in ("output", "response", "text"):
        value = data.get(field)
        if isinstance(value, str):
            return value
    raise ValueError("The model response did not include output text.")


def extract_plain_text(file_bytes: bytes) -> str:
    try:
        return file_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        return file_bytes.decode("windows-1252")


def extract_docx(file_bytes: bytes) -> str:
    document = Document(BytesIO(file_bytes))
    sections = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]
    for table in document.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells]
            if any(cells):
                sections.append(" | ".join(cells))
    return "\n".join(sections)


def extract_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(file_bytes))
    pages = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            pages.append(f"[Page {page_number}]\n{text}")
    return "\n\n".join(pages)


def extract_powerpoint(file_bytes: bytes) -> str:
    presentation = Presentation(BytesIO(file_bytes))
    slides = []
    for slide_number, slide in enumerate(presentation.slides, start=1):
        slide_text = []
        for shape in slide.shapes:
            text = getattr(shape, "text", "")
            if text and text.strip():
                slide_text.append(text.strip())
        try:
            notes = slide.notes_slide.notes_text_frame.text.strip()
            if notes:
                slide_text.append(f"Speaker notes: {notes}")
        except (AttributeError, ValueError):
            pass
        if slide_text:
            slides.append(f"[Slide {slide_number}]\n" + "\n".join(slide_text))
    return "\n\n".join(slides)


def extract_text(file_bytes: bytes, extension: str) -> str:
    if extension in {".txt", ".srt", ".vtt"}:
        text = extract_plain_text(file_bytes)
    elif extension == ".docx":
        text = extract_docx(file_bytes)
    elif extension == ".pdf":
        text = extract_pdf(file_bytes)
    elif extension == ".pptx":
        text = extract_powerpoint(file_bytes)
    else:
        raise ValueError("Unsupported file type.")

    text = text.strip()
    if not text:
        raise ValueError("No readable text was found in the uploaded file.")
    return text[:MAX_EXTRACTED_TEXT]


def build_feedback_prompt(kind: str, filename: str, content: str, focus: str) -> str:
    label = UPLOAD_TYPES[kind]["label"]
    focus_instruction = focus or "Provide comprehensive feedback."
    return (
        f"Provide clear, constructive, and actionable feedback on this {label.lower()}.\n"
        f"File name: {filename}\nRequested focus: {focus_instruction}\n\n"
        "Organize the feedback into strengths, improvements, and recommended next steps.\n\n"
        f"{label} content:\n{content}"
    )


def render_home(**context: Any):
    defaults = {"output": "", "error": "", "filename": "", "selected_type": ""}
    defaults.update(context)
    return render_template("index.html", upload_types=UPLOAD_TYPES, **defaults)


@app.get("/")
def home():
    selected_type = request.args.get("type", "").strip().lower()
    if selected_type not in UPLOAD_TYPES:
        selected_type = ""
    return render_home(selected_type=selected_type)


@app.post("/feedback")
def feedback():
    kind = request.form.get("content_type", "").strip().lower()
    focus = request.form.get("focus", "").strip()[:500]
    uploaded_file = request.files.get("file")

    if kind not in UPLOAD_TYPES:
        return render_home(error="Please choose an upload type."), 400
    if not uploaded_file or not uploaded_file.filename:
        return render_home(error="Please choose a file.", selected_type=kind), 400

    filename = Path(uploaded_file.filename).name
    extension = Path(filename).suffix.lower()
    if extension not in UPLOAD_TYPES[kind]["extensions"]:
        allowed = ", ".join(sorted(UPLOAD_TYPES[kind]["extensions"]))
        return render_home(
            error=f"That file type is not supported for {UPLOAD_TYPES[kind]['label']}. Use: {allowed}.",
            filename=filename,
            selected_type=kind,
        ), 400

    try:
        content = extract_text(uploaded_file.read(), extension)
        prompt = build_feedback_prompt(kind, filename, content, focus)
        demo_feedback = (
            f"Demo feedback for {filename}\n\n"
            f"Your {UPLOAD_TYPES[kind]['label'].lower()} was uploaded and read successfully "
            f"({len(content):,} characters extracted). Connect MODEL_API_URL to replace this "
            "message with feedback from your team's model."
        )
        output = call_model(prompt, demo_feedback)
        return render_home(output=output, filename=filename, selected_type=kind)
    except (OSError, ValueError, requests.RequestException) as exc:
        app.logger.exception("Feedback generation failed: %s", exc)
        message = str(exc) if isinstance(exc, ValueError) else "We couldn't reach the model. Check that it is running."
        return render_home(error=message, filename=filename, selected_type=kind), 422


@app.errorhandler(413)
def file_too_large(_error: Exception):
    return render_home(error="The file is too large. The maximum upload size is 20 MB."), 413


@app.post("/api/generate")
def api_generate():
    body = request.get_json(silent=True) or {}
    prompt = body.get("prompt", "")
    prompt = prompt.strip() if isinstance(prompt, str) else ""
    if not prompt:
        return jsonify({"error": "Please enter a prompt."}), 400
    if len(prompt) > MAX_PROMPT_LENGTH:
        return jsonify({"error": "Prompt must be 4,000 characters or fewer."}), 400
    try:
        return jsonify({"output": call_model(prompt)})
    except (requests.RequestException, ValueError) as exc:
        app.logger.exception("Model request failed: %s", exc)
        return jsonify({"error": "We couldn't reach the model."}), 502


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
