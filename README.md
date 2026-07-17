# Promptly - Python local AI feedback website

Promptly is a local-first Python website for uploading work and receiving category-specific, mentor-style feedback. It can use Qwen 3.5 or Phi-4 Mini through Ollama entirely on the user's computer, with OpenAI or Anthropic Claude available as optional paid API alternatives. The project does not train or fine-tune models; it only sends extracted text to a selected inference provider. Application logic runs in Python with Flask, while a small JavaScript enhancement displays selected PI-style reference files.

## Supported files

- Papers and proposals: `.pdf`, `.docx`, and `.txt`
- Research ideas: `.pdf`, `.docx`, and `.txt`
- Talks and slides: `.pptx`, `.pdf`, `.docx`, `.txt`, `.srt`, and `.vtt`

Feedback uploads are read in memory and are not saved by the website. The maximum file size is 20 MB.

When local Ollama is selected, Promptly can extract up to approximately 120,000 characters from a feedback file. Long reviews are divided into at most three bounded sections and synthesized into one final mentor response. Local requests use a dynamically sized context, concise output budgets, and non-thinking generation so laptop-class hardware responds substantially faster. OpenAI, Claude, and demo mode retain the 100,000-character extraction limit.

Promptly calibrates response-time estimates separately for each selected model and computer. The first successful review displays **Calibrating...** while Promptly measures the request. Later file selections show an estimated response-time range based on that model's recent local history and the selected document size. Up to eight measurements per model are stored locally in `model_performance.json`; uploaded document contents are not stored in the timing history.

## Build a PI-style prompt library

The feedback workspace is the homepage. Use the boxed **Modify a review style** link to open the separate `/prompt-library` workspace, where you can upload prior PI comments or examples in any of these groups:

- Research ideas and meeting minutes
- Talks, presentations, and slides
- Papers and proposals

Reference uploads support `.pdf`, `.docx`, `.pptx`, `.txt`, and `.md`. Create a named prompt library for a mentor or select an existing one; Promptly keeps that library's reference files together, extracts useful review units, identifies recurring concerns and review patterns, and builds one reusable prompt per uploaded category. Libraries can be refreshed with more files or deleted from the page.

When `MODEL_PROVIDER=ollama`, `MODEL_PROVIDER=openai`, or `MODEL_PROVIDER=claude`, the configured model performs a two-step process: it first distills reusable advisor moves without copying project-specific details, then writes a general-purpose prompt. Demo mode uses the deterministic local builder so the workflow remains usable without a model connection.

Each run saves TXT files locally under:

```text
outputs/pi_style_prompts_<mentor-slug>_<run-id>/
```

The stable prompt files for each library are updated under `mentor_files/<library-slug>/`, while the run folder provides individual downloads and a combined `all_pi_style_prompts.txt` file. Reference libraries and generated outputs are ignored by Git.

## Feedback mentors

Users select a mentor before uploading their file. The application combines the selected mentor's contributor-maintained style prompt with category-specific review instructions and the extracted file content.

Currently available:

- **Dr. Nanshu Lu** (`dr-nanshu-lu`)

Dr. Lu's version-controlled starting profile contains three category-specific files under `Mentor_Data/dr-nanshu-lu/`: `meeting_research_pi.txt`, `paper_proposal_pi.txt`, and `slides_talk_pi.txt`. Promptly automatically loads the file matching the selected feedback category. Additional built-in mentors can be added with the same three-file structure and a corresponding `MENTORS` entry.

Built-in mentors also appear in **Modify a review style**. When local reference files are uploaded for a built-in mentor, Promptly saves the learned prompt under `mentor_files/<mentor-slug>/` and uses it in the feedback workspace for that matching category. Categories without a local update continue using the version-controlled `Mentor_Data` starting prompt. Locally created mentor libraries use the same registry and automatically appear in the feedback workspace after a prompt is generated.

Any mentor can be deleted from **Modify a review style** after selecting their card. Promptly asks for confirmation, removes the mentor from both workspaces, and deletes its stored reference files, locally generated prompts, metadata, and associated downloadable run copies. For a bundled mentor, Promptly retains the version-controlled starting files but records the removal locally so the mentor stays hidden after normal app updates. Creating a new library with the same mentor name restores that bundled starting profile.

## Contributors

- Steve21221
- Xianke Feng (`XKfeng111`)

## Run it on Windows

### Easy setup (recommended)

The downloadable setup script installs Promptly in `%LOCALAPPDATA%\Promptly`, prepares its private Python environment, installs Ollama when needed, downloads the selected Qwen model and optional Phi-4 Mini model, and creates a branded **Promptly** desktop shortcut.

1. On the repository page, select **Code**, then **Download ZIP**.
2. Extract the ZIP file in Downloads. The setup script will be inside the extracted repository folder at `Hackathon_1-main\installer\Promptly-Setup.ps1`.
3. Open PowerShell and run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$HOME\Downloads\Hackathon_1-main\installer\Promptly-Setup.ps1"
```

If the extracted folder has a different name, replace `Hackathon_1-main` with the folder name shown in Downloads.

Alternatively, download only [`installer/Promptly-Setup.ps1`](installer/Promptly-Setup.ps1) using GitHub's **Download raw file** button. When the script itself is saved directly in Downloads, run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$HOME\Downloads\Promptly-Setup.ps1"
```

4. First choose one Qwen model based on the computer:

   - Qwen 3.5 4B: approximately 3.4 GB; start here for a computer with 16 GB RAM.
   - Qwen 3.5 9B: approximately 6.6 GB; recommended default for 32 GB RAM.
   - Qwen 3.5 27B: approximately 17 GB; strongest offered setup option, recommended for 64 GB RAM.

   The installer then separately asks whether to add Phi-4 Mini (approximately 2.5 GB) as a faster optional model. If installed, users can switch between the selected Qwen model and Phi-4 Mini in **Model settings**.

5. After setup, double-click **Promptly** on the desktop. Keep the opened command window running while using the website; close it or press `Ctrl+C` to stop Promptly.

The setup needs internet access to download the code, Python packages, Ollama, and the model. After installation, feedback generation runs locally without an API key or per-token fee.

The published setup downloads the `main` branch. Contributors testing a pull-request branch before it is merged can pass its name explicitly, for example:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$HOME\Downloads\Hackathon_1-main\installer\Promptly-Setup.ps1" -RepositoryBranch "codex/separate-review-style"
```

### Uninstall Promptly without removing Ollama

Use [`installer/Promptly-Uninstall.ps1`](installer/Promptly-Uninstall.ps1) to remove only the Promptly website. Close Promptly, download the uninstaller, and run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$HOME\Downloads\Promptly-Uninstall.ps1"
```

The script asks you to type `UNINSTALL`, stops only Promptly's Python processes, removes the Promptly desktop shortcut, and deletes `%LOCALAPPDATA%\Promptly`. This also deletes Promptly settings, mentor libraries, uploaded references, and generated outputs. It does **not** uninstall Ollama, stop the Ollama server, or delete models stored under `%USERPROFILE%\.ollama`.

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

The recommended local provider is Ollama with Qwen 3.5 for critique quality or Phi-4 Mini for faster responses. Copy `.env.example` to `.env`, then use:

```text
MODEL_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen3.5:9b
```

The application sends the mentor instructions and extracted file text to Ollama's local API. Thinking mode is disabled for lower latency. Promptly dynamically sizes the working context between 8,192 and 16,384 tokens and limits a direct final response to 1,800 tokens.

Ollama and the selected model must be installed and running. To install the default model manually:

```powershell
ollama pull qwen3.5:9b
```

For the faster local option, use `ollama pull phi4-mini`, then select **Phi-4 Mini** under **Model settings**.

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

## Optional: connect Claude (Anthropic)

This integration uses the Anthropic Messages API. API usage may cost money.

1. Create an API key in your [Anthropic Console](https://console.anthropic.com/).
2. In the project folder, create your private `.env` file if it does not already exist:

```powershell
Copy-Item .env.example .env
```

3. Open `.env` and set:

```text
MODEL_PROVIDER=claude
ANTHROPIC_API_KEY=your-private-key-here
CLAUDE_MODEL=claude-sonnet-4-5
```

`MODEL_PROVIDER=anthropic` is also accepted. Change `CLAUDE_MODEL` if you prefer another Claude model available on your account.

4. Restart the website after changing `.env`.

The application extracts text from the upload in memory, then sends the extracted content—not the original file—to Anthropic. Generated output is capped at 2,000 tokens. Review your organization's Anthropic data and retention requirements before using confidential or unpublished work.

## Mentor prompt contributor workflow

The prompt contributor does not need to edit the Flask routes or file extraction code.

1. Open the appropriate file under `Mentor_Data/dr-nanshu-lu/` for research ideas, papers and proposals, or talks and slides.
2. Update only the category whose reviewed mentor-style evidence has changed.
3. Keep each file standalone and focused on review priorities, reasoning sequence, tone, critical questions, and response organization.
4. Do not include an API key, source quotations, or private research content in any prompt file.
5. Run the tests, then submit the change on a separate branch and pull request.

Run the complete test suite from the project folder with:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## How feedback is generated

Promptly extracts the uploaded file's text, identifies the selected feedback category, includes the optional focus, and combines it with the mentor prompt. It then sends that request to the provider selected in `.env`:

- `ollama`: a local Qwen or Phi model; no API key or per-token charge.
- `openai`: the OpenAI Responses API; requires an API key and incurs API usage charges.
- `claude` (or `anthropic`): the Anthropic Messages API; requires an API key and incurs API usage charges.
- `demo`: no model request; returns a local confirmation message.

Secrets stay on the Python server and are never sent to the browser. The generated final answer is returned to the Mentor feedback panel.
