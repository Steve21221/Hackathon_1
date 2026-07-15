# Promptly - Python local AI feedback website

Promptly is a local-first Python website for uploading work and receiving category-specific, mentor-style feedback. It can use a DeepSeek reasoning model through Ollama entirely on the user's computer, with OpenAI available as an optional paid alternative. The interface uses HTML and CSS, and all application logic runs in Python with Flask. No client-side JavaScript is used.

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

### Easy setup (recommended)

The downloadable setup script installs Promptly in `%LOCALAPPDATA%\Promptly`, prepares its private Python environment, installs Ollama when needed, downloads the selected DeepSeek model, and creates a **Promptly** desktop shortcut.

1. Download [`installer/Promptly-Setup.ps1`](installer/Promptly-Setup.ps1) from GitHub using the **Download raw file** button.
2. Open PowerShell and run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$HOME\Downloads\Promptly-Setup.ps1"
```

3. Choose a model based on the computer:

   - DeepSeek R1 8B: approximately 5.2 GB; start here for a computer with 16 GB RAM.
   - DeepSeek R1 14B: approximately 9 GB; recommended default for 32 GB RAM.
   - DeepSeek R1 32B: approximately 20 GB; strongest offered setup option, recommended for 64 GB RAM.

4. After setup, double-click **Promptly** on the desktop. Keep the opened command window running while using the website; close it or press `Ctrl+C` to stop Promptly.

The setup needs internet access to download the code, Python packages, Ollama, and the model. After installation, feedback generation runs locally without an API key or per-token fee.

### Manual setup

#### First-time setup

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

#### Run it again later

You only need to create the environment and install packages once. On later visits, open PowerShell and run:

```powershell
cd "C:\path\to\Hackathon_1"
.\.venv\Scripts\python.exe app.py
```

Replace `C:\path\to\Hackathon_1` with the actual project location on that computer. Then open <http://localhost:5000>.

If PowerShell says that `py`, `git`, or `.\.venv\Scripts\python.exe` is not recognized, confirm that the required software is installed, reopen PowerShell, and verify that you are inside the `Hackathon_1` folder.

Without a `.env` file, the website works in demo mode and makes no model request.

## Run a local reasoning model with Ollama

The recommended local provider is Ollama with DeepSeek R1. Copy `.env.example` to `.env`, then use:

```text
MODEL_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=deepseek-r1:14b
```

The application sends the mentor instructions and extracted file text to Ollama's local API. Thinking mode is enabled so the model can reason before answering, but only the final feedback is displayed. The request uses a 32,768-token working context and limits the final response to 2,000 tokens.

Ollama and the selected model must be installed and running. To install the default model manually:

```powershell
ollama pull deepseek-r1:14b
```

No content is sent to OpenAI when `MODEL_PROVIDER=ollama`.

## Optional: connect OpenAI

This integration uses the OpenAI API. A ChatGPT subscription is separate from API usage, and API calls may cost money.

1. Create an API key in your OpenAI API account.
2. In the project folder, create your private `.env` file:

```powershell
Copy-Item .env.example .env
```

3. Open `.env` and add the key after `OPENAI_API_KEY=`. Do not put the key in GitHub, screenshots, chat messages, or shared documents.
4. Keep the cost-conscious default model or change it as a team decision:

```text
MODEL_PROVIDER=openai
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

Promptly extracts the uploaded file's text, identifies the selected feedback category, includes the optional focus, and combines it with the mentor prompt. It then sends that request to the provider selected in `.env`:

- `ollama`: a local DeepSeek reasoning model; no API key or per-token charge.
- `openai`: the OpenAI Responses API; requires an API key and incurs API usage charges.
- `demo`: no model request; returns a local confirmation message.

Secrets stay on the Python server and are never sent to the browser. The generated final answer is returned to the Mentor feedback panel.
