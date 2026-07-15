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

function Find-Python {
    $launcher = Get-Command py -ErrorAction SilentlyContinue
    if ($launcher) {
        return @($launcher.Source, "-3.12")
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python -and $python.Source -notlike "*WindowsApps*") {
        return @($python.Source)
    }

    $candidate = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
    if (Test-Path $candidate) {
        return @($candidate)
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

    Write-Step "Creating Promptly's private Python environment"
    $pythonExecutable = $pythonCommand[0]
    $pythonArguments = @()
    if ($pythonCommand.Count -gt 1) {
        $pythonArguments += $pythonCommand[1..($pythonCommand.Count - 1)]
    }
    & $pythonExecutable @pythonArguments -m venv (Join-Path $InstallDirectory ".venv")
    $venvPython = Join-Path $InstallDirectory ".venv\Scripts\python.exe"
    & $venvPython -m pip install --disable-pip-version-check -r (Join-Path $InstallDirectory "requirements.txt")

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

    Write-Step "Choose the local reasoning model"
    Write-Host "1. Qwen 3.5 4B  - about 3.4 GB; recommended for 16 GB RAM"
    Write-Host "2. Qwen 3.5 9B  - about 6.6 GB; recommended for 32 GB RAM (default)"
    Write-Host "3. Qwen 3.5 27B - about 17 GB; recommended for 64 GB RAM"
    $choice = Read-Host "Enter 1, 2, or 3"
    $model = switch ($choice) {
        "1" { "qwen3.5:4b" }
        "3" { "qwen3.5:27b" }
        default { "qwen3.5:9b" }
    }

    Write-Step "Downloading $model"
    Write-Host "This is the largest part of setup and may take a while."
    & $ollama pull $model
    if ($LASTEXITCODE -ne 0) {
        throw "The model download did not complete. Run this setup again when the internet connection is stable."
    }

    @"
MODEL_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=$model

# Optional paid OpenAI alternative
OPENAI_API_KEY=
OPENAI_MODEL=gpt-5-mini

# Optional paid Anthropic Claude alternative
ANTHROPIC_API_KEY=
CLAUDE_MODEL=claude-sonnet-4-5
"@ | Set-Content -Path (Join-Path $InstallDirectory ".env") -Encoding UTF8

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
    Write-Host "Model: $model"
    Write-Host "Double-click Promptly on the desktop to start the website."
}
finally {
    if (Test-Path $temporaryDirectory) {
        Remove-Item -LiteralPath $temporaryDirectory -Recurse -Force
    }
}
