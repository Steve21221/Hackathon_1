# Promptly - Python local AI feedback website

Promptly is a Python website for uploading work and receiving category-specific, mentor-style feedback from an OpenAI model. The interface uses HTML and CSS, and all application logic runs in Python with Flask. No client-side JavaScript is used.

## Supported files

- Papers and proposals: `.pdf`, `.docx`, and `.txt`
- Research ideas: `.pdf`, `.docx`, and `.txt`
- Talks and slides: `.pptx`, `.pdf`, `.docx`, `.txt`, `.srt`, and `.vtt`

Uploads are read in memory and are not saved by the website. The maximum file size is 20 MB.

## Feedback mentors

Users select a mentor before uploading their file. The application combines the selected mentor's contributor-maintained style prompt with category-specific review instructions and the extracted file content.

Currently available:

- **Dr. Nanshu Lu** (`dr-nanshu-lu`)

The current general prompt is stored in `mentor_prompts/dr-nanshu-lu.txt`. It is intentionally easy to replace when the prompt contributor supplies a validated version. Additional mentors can be added to the `MENTORS` configuration and `mentor_prompts` folder.

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

The website works in demo mode without an OpenAI API key.

## Connect OpenAI

This integration uses the OpenAI API. A ChatGPT subscription is separate from API usage, and API calls may cost money.

1. Create an API key in your OpenAI API account.
2. In the project folder, create your private `.env` file:

```powershell
Copy-Item .env.example .env
```

3. Open `.env` and add the key after `OPENAI_API_KEY=`. Do not put the key in GitHub, screenshots, chat messages, or shared documents.
4. Keep the cost-conscious default model or change it as a team decision:

```text
OPENAI_API_KEY=your-private-key-here
OPENAI_MODEL=gpt-5-mini
```

5. Restart the website after changing `.env`.

The application extracts text from the upload in memory, then sends the extracted content—not the original file—to OpenAI. The request asks OpenAI not to store the response (`store=False`) and caps generated output at 2,000 tokens. Review your organization's OpenAI data and retention requirements before using confidential or unpublished work.

## Mentor prompt contributor workflow

The prompt contributor does not need to edit the Flask routes or file extraction code.

1. Open `mentor_prompts/dr-nanshu-lu.txt`.
2. Replace the temporary general profile with the validated mentor-style prompt.
3. Keep the prompt focused on review priorities, tone, critical questions, response organization, and examples of desired feedback behavior.
4. Do not include an API key or private research content in the prompt file.
5. Run the tests, then submit the change on a separate branch and pull request.

## How feedback is generated

Promptly extracts the uploaded file's text, identifies the selected feedback category, includes the optional focus, and calls the OpenAI Responses API with:

```python
client.responses.create(
    model="gpt-5-mini",
    instructions="Base safety rules plus the selected mentor style prompt",
    input="Category guidance, filename, requested focus, and extracted content",
    max_output_tokens=2000,
    store=False,
)
```

The API key stays on the Python server and is never sent to the browser. The generated text is returned to the Mentor feedback panel.
