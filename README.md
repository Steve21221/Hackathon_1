# Promptly - Python local AI feedback website

Promptly is a Python website for uploading a document, transcript, or PowerPoint and receiving feedback from a locally running language model. The interface uses HTML and CSS, and all application logic runs in Python with Flask. No client-side JavaScript is used.

## Supported files

- Documents: `.pdf`, `.docx`, and `.txt`
- Transcripts: `.txt`, `.srt`, `.vtt`, and `.docx`
- PowerPoint: `.pptx`

Uploads are read in memory and are not saved by the website. The maximum file size is 20 MB.

## Run it on Windows

1. Install [Python 3.11 or newer](https://www.python.org/downloads/). During installation, select **Add Python to PATH**.
2. Open PowerShell in this project folder.
3. Create a private Python environment:

```powershell
py -m venv .venv
```

4. Install the required Python packages:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

5. Start the website:

```powershell
.\.venv\Scripts\python.exe app.py
```

6. Open <http://127.0.0.1:5000> in your browser. Press `Ctrl+C` in PowerShell to stop the website.

The website works in demo mode without a model.

## Connect the local model

Copy `.env.example` to `.env`, then set `MODEL_API_URL` to the local HTTP endpoint provided by the model team.

Promptly extracts the uploaded file's text, identifies its content type, includes the optional feedback focus, and sends the complete request as:

```json
{ "prompt": "Feedback instructions followed by the extracted content" }
```

The model service can return its answer in `output`, `response`, or `text`:

```json
{ "output": "The model feedback" }
```

The model server and this website must both be running while you use the application.
