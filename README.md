# Promptly — Python local AI website

Promptly is a small Python website for sending prompts to a locally running language model. The browser interface uses HTML and CSS, and all application logic runs in Python with Flask. No client-side JavaScript is used.

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

Copy `.env.example` to `.env`, then set `MODEL_API_URL` to the local HTTP endpoint provided by the model team. Promptly sends:

```json
{ "prompt": "The user's input" }
```

The model service can return its answer in `output`, `response`, or `text`:

```json
{ "output": "The model response" }
```

The model server and this website must both be running while you use the application.
