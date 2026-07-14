import os
import time
from typing import Any

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

load_dotenv()

app = Flask(__name__)
MAX_PROMPT_LENGTH = 4_000


def generate_response(prompt: str) -> str:
    """Send a prompt to the configured model, or return a local demo response."""
    model_url = os.getenv("MODEL_API_URL", "").strip()

    if not model_url:
        time.sleep(0.4)
        return (
            f'This is a demo response for: “{prompt}”\n\n'
            "Your Python website is working. When the model team provides a local "
            "API address, add it to .env as MODEL_API_URL."
        )

    headers = {"Content-Type": "application/json"}
    api_key = os.getenv("MODEL_API_KEY", "").strip()
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    response = requests.post(
        model_url,
        json={"prompt": prompt},
        headers=headers,
        timeout=60,
    )
    response.raise_for_status()
    data: dict[str, Any] = response.json()

    for field in ("output", "response", "text"):
        value = data.get(field)
        if isinstance(value, str):
            return value

    raise ValueError("The model response did not include output text.")


def validate_prompt(value: Any) -> tuple[str, str]:
    prompt = value.strip() if isinstance(value, str) else ""
    if not prompt:
        return "", "Please enter a prompt."
    if len(prompt) > MAX_PROMPT_LENGTH:
        return prompt, "Prompt must be 4,000 characters or fewer."
    return prompt, ""


@app.route("/", methods=["GET", "POST"])
def home():
    prompt = request.args.get("prompt", "") if request.method == "GET" else request.form.get("prompt", "")
    output = ""
    error = ""

    if request.method == "POST":
        prompt, error = validate_prompt(prompt)
        if not error:
            try:
                output = generate_response(prompt)
            except (requests.RequestException, ValueError) as exc:
                app.logger.exception("Model request failed: %s", exc)
                error = "We couldn't reach the model. Check that it is running, then try again."

    return render_template(
        "index.html",
        prompt=prompt,
        output=output,
        error=error,
        max_prompt_length=MAX_PROMPT_LENGTH,
    )


@app.post("/api/generate")
def api_generate():
    body = request.get_json(silent=True) or {}
    prompt, error = validate_prompt(body.get("prompt"))
    if error:
        return jsonify({"error": error}), 400

    try:
        return jsonify({"output": generate_response(prompt)})
    except (requests.RequestException, ValueError) as exc:
        app.logger.exception("Model request failed: %s", exc)
        return jsonify({"error": "We couldn't reach the model."}), 502


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
