# Promptly - Python local AI feedback website

Promptly is a Python website for uploading a document, transcript, or PowerPoint and receiving feedback from a locally running language model. The interface uses HTML and CSS, and all application logic runs in Python with Flask. No client-side JavaScript is used.

## Supported files

- Documents: `.pdf`, `.docx`, and `.txt`
- Transcripts: `.txt`, `.srt`, `.vtt`, and `.docx`
- PowerPoint: `.pptx`

Uploads are read in memory and are not saved by the website. The maximum file size is 20 MB.

## Feedback mentors

Users select a mentor before uploading their file. Each mentor identifier is passed to the local model so it can apply that mentor's specialty, thinking process, and feedback style.

Currently available:

- **Dr. Nanshu Lu** (`dr-nanshu-lu`)

Additional mentors can be added to the `MENTORS` configuration in `app.py` when their model profiles become available.

## Run it on Windows

### First-time setup

1. Install [Python 3.11 or newer](https://www.python.org/downloads/). During installation, select **Add Python to PATH**.
2. Install [Git for Windows](https://git-scm.com/downloads/win) if it is not already installed.
3. Close and reopen PowerShell after installing Python or Git.
4. In PowerShell, move to the folder where you want to keep the project. For example:

```powershell
cd "$HOME\Documents"
```

5. Download the code from GitHub and enter the project folder:

```powershell
git clone https://github.com/Steve21221/Hackathon_1.git
cd Hackathon_1
```

If the project is already on your computer, skip the clone command and move directly into its folder. On the original development computer, use:

```powershell
cd "C:\Users\ythst\Documents\Codex\2026-07-13\i\Hackathon_1"
```

Do not run the following commands from `C:\Windows\System32`. Confirm that you are in the correct folder by running:

```powershell
Get-Location
Get-ChildItem
```

You should see `app.py`, `requirements.txt`, `templates`, and `static`.

6. Create a private Python environment for the project:

```powershell
py -m venv .venv
```

7. Install the required Python packages:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

8. Start the website:

```powershell
.\.venv\Scripts\python.exe app.py
```

9. Keep PowerShell open and visit <http://127.0.0.1:5000> or <http://localhost:5000> in your browser.
10. When you are finished, return to PowerShell and press `Ctrl+C` to stop the website.

### Run it again later

You only need to create the environment and install packages once. On later visits, open PowerShell and run:

```powershell
cd "C:\path\to\Hackathon_1"
.\.venv\Scripts\python.exe app.py
```

Replace `C:\path\to\Hackathon_1` with the actual project location on that computer. Then open <http://localhost:5000>.

If PowerShell says that `py`, `git`, or `.\.venv\Scripts\python.exe` is not recognized, confirm that the required software is installed, reopen PowerShell, and verify that you are inside the `Hackathon_1` folder.

The website works in demo mode without a model.

## Connect the local model

Copy `.env.example` to `.env`, then set `MODEL_API_URL` to the local HTTP endpoint provided by the model team.

Promptly extracts the uploaded file's text, identifies its content type, includes the optional feedback focus, and sends the complete request as:

```json
{
  "prompt": "Mentor and feedback instructions followed by the extracted content",
  "mentor_id": "dr-nanshu-lu",
  "mentor_name": "Dr. Nanshu Lu"
}
```

The model service can return its answer in `output`, `response`, or `text`:

```json
{ "output": "The model feedback" }
```

The model server and this website must both be running while you use the application.
