param(
    [string]$InstallDirectory = "$env:LOCALAPPDATA\Promptly",
    [string]$RepositoryBranch = "main"
)

$ErrorActionPreference = "Stop"
$RepositoryArchive = "https://github.com/Steve21221/Hackathon_1/archive/refs/heads/$RepositoryBranch.zip"
$OllamaInstallerUrl = "https://ollama.com/download/OllamaSetup.exe"

function Write-Step([string]$Message) {
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function Test-PythonCommand([string]$Executable, [string[]]$Arguments = @()) {
    try {
        & $Executable @Arguments -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" *> $null
        return $LASTEXITCODE -eq 0
    }
    catch {
        return $false
    }
}

function Find-Python {
    $launcher = Get-Command py -ErrorAction SilentlyContinue
    if ($launcher -and (Test-PythonCommand $launcher.Source @("-3.12"))) {
        return [pscustomobject]@{
            Executable = $launcher.Source
            Arguments = @("-3.12")
        }
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if (
        $python -and
        $python.Source -notlike "*WindowsApps*" -and
        (Test-PythonCommand $python.Source)
    ) {
        return [pscustomobject]@{
            Executable = $python.Source
            Arguments = @()
        }
    }

    $candidate = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
    if ((Test-Path $candidate) -and (Test-PythonCommand $candidate)) {
        return [pscustomobject]@{
            Executable = $candidate
            Arguments = @()
        }
    }
    return $null
}

function Find-Ollama {
    $command = Get-Command ollama -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    $candidate = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
    if (Test-Path $candidate) {
        return $candidate
    }
    return $null
}

function Test-OllamaServer {
    try {
        Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/version" -TimeoutSec 2 | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

function Wait-ForOllama([int]$TimeoutSeconds = 600) {
    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    do {
        $ollamaCommand = Find-Ollama
        if ($ollamaCommand -and (Test-OllamaServer)) {
            return $ollamaCommand
        }
        Start-Sleep -Seconds 2
    } while ([DateTime]::UtcNow -lt $deadline)
    return $null
}

Write-Host "Promptly local setup" -ForegroundColor Green
Write-Host "This installs the website and downloads a local reasoning model."
Write-Host "No OpenAI API key or per-token payment is required."

$pythonCommand = Find-Python
if (-not $pythonCommand) {
    Write-Step "Installing Python 3.12"
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if (-not $winget) {
        throw "Python is required. Install Python 3.12 from https://www.python.org/downloads/ and run this setup again."
    }
    & $winget.Source install --id Python.Python.3.12 --exact --scope user --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) {
        throw "Python installation did not complete. Check the winget message above, then run this setup again."
    }
    $pythonCommand = Find-Python
    if (-not $pythonCommand) {
        throw "Python was installed but could not be found. Restart Windows, then run this setup again."
    }
}

$temporaryDirectory = Join-Path $env:TEMP ("PromptlySetup-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $temporaryDirectory | Out-Null

try {
    Write-Step "Downloading Promptly"
    $archivePath = Join-Path $temporaryDirectory "Promptly.zip"
    Invoke-WebRequest -Uri $RepositoryArchive -OutFile $archivePath
    Expand-Archive -LiteralPath $archivePath -DestinationPath $temporaryDirectory
    $sourceDirectory = Get-ChildItem -Path $temporaryDirectory -Directory | Where-Object { $_.Name -like "Hackathon_1-*" } | Select-Object -First 1
    if (-not $sourceDirectory) {
        throw "The downloaded Promptly package could not be read."
    }

    New-Item -ItemType Directory -Path $InstallDirectory -Force | Out-Null
    Copy-Item -Path (Join-Path $sourceDirectory.FullName "*") -Destination $InstallDirectory -Recurse -Force

    $requiredPaths = @(
        "app.py",
        "run_promptly.py",
        "requirements.txt",
        "Mentor_Data",
        "raw_materials",
        "static",
        "templates"
    )
    foreach ($requiredPath in $requiredPaths) {
        if (-not (Test-Path (Join-Path $InstallDirectory $requiredPath))) {
            throw "The downloaded Promptly package is missing $requiredPath. Please download a published release and run setup again."
        }
    }
    "Promptly local website installation" | Set-Content -Path (Join-Path $InstallDirectory ".promptly-install") -Encoding ASCII

    Write-Step "Creating Promptly's private Python environment"
    $pythonExecutable = $pythonCommand.Executable
    $pythonArguments = @($pythonCommand.Arguments)
    & $pythonExecutable @pythonArguments -m venv (Join-Path $InstallDirectory ".venv")
    $venvPython = Join-Path $InstallDirectory ".venv\Scripts\python.exe"
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $venvPython)) {
        throw "Promptly could not create its private Python environment."
    }
    & $venvPython -m pip install --disable-pip-version-check -r (Join-Path $InstallDirectory "requirements.txt")
    if ($LASTEXITCODE -ne 0) {
        throw "Promptly's Python packages could not be installed. Check the internet connection, then run setup again."
    }

    $ollama = Find-Ollama
    if (-not $ollama) {
        Write-Step "Installing Ollama"
        $ollamaInstaller = Join-Path $temporaryDirectory "OllamaSetup.exe"
        Invoke-WebRequest -Uri $OllamaInstallerUrl -OutFile $ollamaInstaller
        Start-Process -FilePath $ollamaInstaller -Wait
        $ollama = Find-Ollama
        if (-not $ollama) {
            throw "Ollama was not found after installation. Restart Windows, then run this setup again."
        }
    }

    if (-not (Test-OllamaServer)) {
        Write-Step "Starting Ollama's local server"
        Start-Process -FilePath $ollama -ArgumentList "serve" -WindowStyle Hidden | Out-Null
        $ollama = Wait-ForOllama -TimeoutSeconds 60
        if (-not $ollama) {
            throw "Ollama is installed but its local server could not start. Restart Windows, open Ollama, then run this setup again."
        }
    }

    Write-Step "Choose the local reasoning model"
    Write-Host "1. Qwen 3.5 4B  - about 3.4 GB; best scientific critique on laptop hardware"
    Write-Host "2. Qwen 3.5 9B  - about 6.6 GB; recommended for 32 GB RAM (default)"
    Write-Host "3. Qwen 3.5 27B - about 17 GB; recommended for 64 GB RAM"
    Write-Host "4. Phi-4 Mini     - about 2.5 GB; faster responses on laptop hardware"
    Write-Host "5. Qwen 4B + Phi - about 5.9 GB; install both and switch in the website"
    $choice = Read-Host "Enter 1, 2, 3, 4, or 5"
    $models = @(switch ($choice) {
        "1" { @("qwen3.5:4b") }
        "3" { @("qwen3.5:27b") }
        "4" { @("phi4-mini") }
        "5" { @("qwen3.5:4b", "phi4-mini") }
        default { @("qwen3.5:9b") }
    })
    $model = $models[0]

    Write-Step "Downloading selected local model(s)"
    Write-Host "This is the largest part of setup and may take a while."
    foreach ($downloadModel in $models) {
        Write-Host "Downloading $downloadModel"
        & $ollama pull $downloadModel
        if ($LASTEXITCODE -ne 0) {
            throw "The $downloadModel download did not complete. Run this setup again when the internet connection is stable."
        }
    }

    $environmentContents = @"
MODEL_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=$model

# Optional paid OpenAI alternative
OPENAI_API_KEY=
OPENAI_MODEL=gpt-5-mini

# Optional paid Anthropic Claude alternative
ANTHROPIC_API_KEY=
CLAUDE_MODEL=claude-sonnet-4-5
"@
    # Windows PowerShell 5.1's UTF8 encoding adds a byte-order mark. That mark
    # becomes part of the first variable name when python-dotenv reads the file.
    $utf8WithoutBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText(
        (Join-Path $InstallDirectory ".env"),
        $environmentContents,
        $utf8WithoutBom
    )

    $runCommandPath = Join-Path $InstallDirectory "Run-Promptly.cmd"
    @"
@echo off
cd /d "$InstallDirectory"
"$venvPython" "$InstallDirectory\run_promptly.py"
if errorlevel 1 pause
"@ | Set-Content -Path $runCommandPath -Encoding ASCII

    Write-Step "Creating a desktop shortcut"
    $desktop = [Environment]::GetFolderPath("Desktop")
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut((Join-Path $desktop "Promptly.lnk"))
    $shortcut.TargetPath = $runCommandPath
    $shortcut.WorkingDirectory = $InstallDirectory
    $shortcut.Description = "Start the local Promptly mentor-feedback website"
    $shortcut.Save()

    Write-Host "`nPromptly is installed successfully." -ForegroundColor Green
    Write-Host "Installed at: $InstallDirectory"
    Write-Host "Installed model(s): $($models -join ', ')"
    Write-Host "Default model: $model"
    Write-Host "Double-click Promptly on the desktop to start the website."
}
finally {
    if (Test-Path $temporaryDirectory) {
        Remove-Item -LiteralPath $temporaryDirectory -Recurse -Force
    }
}
