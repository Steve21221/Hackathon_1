# Hackathon — Local PI Style Prompt Workspace

Hackathon is a local Flask web app for building reusable PI-style review prompts from your own reference materials. It helps you upload previous meeting notes, slide feedback, manuscript comments, and related documents, then generates mode-specific prompt files that can be reused for future research feedback.

The current workflow is designed for **local-first** use:

- The web app runs on `http://127.0.0.1:5000/`.
- Uploaded files are read locally by the Flask app.
- PI-style prompt generation can run locally through Ollama/Llama.
- Generated prompt `.txt` files are saved locally under `outputs/<run_id>/`.
- `.env` and generated outputs are ignored by git.

## Main features

### 1. Build Your PI Style Library

Upload reference materials into three PI-review modes:

| Mode | What to upload | What the app learns |
| --- | --- | --- |
| Research Ideas / Meeting Minutes | Meeting notes, research ideas, experiment plans, lab discussion records | How the PI reframes ideas, grounds them in context, decomposes variables, compares mechanisms, prioritizes roadmap items, and turns discussion into action items |
| Talks / Presentations / Slides | Slide drafts, talk feedback, presentation notes, figure sets | Audience-first storytelling, title/significance framing, citation discipline, labels/annotations, visual consistency, takeaway messages, deletion of weak visuals, and concrete slide-level edits |
| Papers / Proposals | Manuscript feedback, proposal comments, figure-set feedback, paper drafts | Practical value, central claim, coherent argument, evidence/context support, figures proving claims, claim-evidence alignment, and concrete manuscript revisions |

After clicking **Generate PI-Style Prompts**, the app shows concise prompt cards in the browser and saves prompt files locally.

### 2. Local prompt TXT outputs

Every prompt-generation run creates a folder like:

```text
outputs/<run_id>/
```

For example:

```text
outputs/pi_style_library_pi_prompts_ab12cd34/
```

Inside that folder you will find:

```text
meeting_research_pi_prompt.txt
slides_talk_pi_prompt.txt
paper_proposal_pi_prompt.txt
all_pi_style_prompts.txt
```

The result page also displays the exact local path after generation:

```text
TXT files saved locally in ...\outputs\<run_id>
```

### 3. Review a document/transcript/PowerPoint

The lower part of the page keeps a simple local upload flow for:

- Document
- Transcript
- PowerPoint

This reads a target file locally and returns mentor-style feedback. By default, if no external model endpoint is configured, this feedback route uses local demo feedback so the app remains runnable without paid APIs.

## What runs locally?

The app is local-first:

| Component | Local? | Notes |
| --- | --- | --- |
| Flask web app | Yes | Runs at `127.0.0.1:5000` |
| File upload and text extraction | Yes | Files are processed by local Python code |
| PI prompt generation | Yes, when Ollama is enabled | Uses local Ollama at `127.0.0.1:11434` |
| Generated prompt TXT files | Yes | Saved under `outputs/<run_id>/` |
| Feedback demo route | Yes | Returns local demo feedback when no `MODEL_API_URL` is set |
| External model feedback | Optional | Only used if you explicitly set `MODEL_API_URL` |

## Supported file formats

For the PI Style Library upload cards:

```text
.pdf, .docx, .pptx, .txt, .md
```

For the lower review-upload flow:

- Document: `.pdf`, `.docx`, `.txt`
- Transcript: `.txt`, `.srt`, `.vtt`, `.docx`
- PowerPoint: `.pptx`

The default Flask upload limit is 20 MB per request.

## Quick start on Windows

### 1. Clone the repository

```powershell
git clone https://github.com/XKfeng111/Hackathon.git
cd Hackathon
```

### 2. Create a virtual environment

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If `py` is not available, install Python 3.11+ from <https://www.python.org/downloads/> and enable **Add Python to PATH**.

### 3. Optional but recommended: enable local Ollama/Llama

Install Ollama from <https://ollama.com/> and pull a local model:

```powershell
ollama pull llama3.1:8b
```

Copy `.env.example` to `.env`:

```powershell
Copy-Item .env.example .env
```

The `.env` file should contain:

```env
PROMPT_LLM_PROVIDER=ollama
OLLAMA_URL=http://127.0.0.1:11434
OLLAMA_MODEL=llama3.1:8b
```

If Ollama is not configured, the app still runs and falls back to deterministic prompt generation.

### 4. Start the app

```powershell
.\.venv\Scripts\python.exe -m flask --app app run --host 127.0.0.1 --port 5000
```

Open:

```text
http://127.0.0.1:5000/
```

## How to use the PI Style Library

1. Open `http://127.0.0.1:5000/`.
2. Go to **Build Your PI Style Library**.
3. Upload one or more reference files in any of the three categories:
   - Research Ideas / Meeting Minutes
   - Talks / Presentations / Slides
   - Papers / Proposals
4. Click **Generate PI-Style Prompts**.
5. Review the generated prompt cards on the page.
6. Look for the line `TXT files saved locally in ...` to find the prompt folder.
7. Open the generated `.txt` files from `outputs/<run_id>/` and copy them into your downstream feedback workflow.

You can upload multiple files per category. There is no fixed file-count limit in code, but the total request size is limited to 20 MB. In practice, 3–10 modest files per category is a good starting point.

## Refresh behavior

After prompt generation or feedback generation, the result is shown once. If you refresh the browser, the page resets to the clean home view so old `PI Style Prompts Ready` results do not stay on screen or get accidentally resubmitted.

## Development

Install dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Run tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

At the time of this update, the test suite contains route, reader, prompt-generation, UI-rendering, and local-output tests.

## Project structure

```text
app.py                         Flask app, upload routes, local/Ollama prompt generation, downloads
raw_materials/reader.py        Extract text from PDF/DOCX/PPTX/TXT/MD uploads
raw_materials/chunker.py       Split extracted text into chunks
raw_materials/jsonl_builder.py Build structured JSONL-style records for legacy workflow
raw_materials/prompt_builder.py Build deterministic fallback PI prompts
templates/index.html           Main web UI
static/style.css               UI styling
static/library_uploads.js      Multi-file upload card behavior
tests/                         Unit and route tests
outputs/                       Local generated prompt/output files; ignored by git except .gitkeep
```

## Privacy and local data notes

- Uploaded files are processed locally during the request.
- Generated outputs are written to `outputs/<run_id>/`.
- `outputs/`, `.env`, `.venv`, caches, and temporary reference folders are ignored by git.
- Do not commit private reference files, API keys, or generated prompt-output folders.

## Acknowledgements

- Xianke Feng — project owner and workflow design.
- ChatGPT/Codex — AI coding assistant for implementation, testing, and documentation support.
