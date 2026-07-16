param(
    [string]$InstallDirectory = "$env:LOCALAPPDATA\Promptly",
    [string]$ShortcutPath = "",
    [switch]$Force
)

$ErrorActionPreference = "Stop"

function Write-Step([string]$Message) {
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function Get-NormalizedPath([string]$Path) {
    if ([string]::IsNullOrWhiteSpace($Path)) {
        throw "A non-empty path is required."
    }

    $expanded = [Environment]::ExpandEnvironmentVariables($Path)
    if (-not [System.IO.Path]::IsPathRooted($expanded)) {
        $expanded = Join-Path (Get-Location).Path $expanded
    }

    $fullPath = [System.IO.Path]::GetFullPath($expanded)
    $root = [System.IO.Path]::GetPathRoot($fullPath)
    if ($fullPath.Length -gt $root.Length) {
        return $fullPath.TrimEnd([char[]]@('\', '/'))
    }
    return $fullPath
}

function Test-SamePath([string]$Left, [string]$Right) {
    return [string]::Equals(
        (Get-NormalizedPath $Left),
        (Get-NormalizedPath $Right),
        [System.StringComparison]::OrdinalIgnoreCase
    )
}

function Test-PathWithin([string]$Candidate, [string]$Parent) {
    $candidatePath = Get-NormalizedPath $Candidate
    $parentPath = Get-NormalizedPath $Parent
    if (Test-SamePath $candidatePath $parentPath) {
        return $true
    }

    $prefix = $parentPath.TrimEnd([char[]]@('\', '/')) + [System.IO.Path]::DirectorySeparatorChar
    return $candidatePath.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)
}

function Remove-OwnedShortcut([string]$Path, [string]$ExpectedTarget) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return
    }
    if ([System.IO.Path]::GetExtension($Path) -ine ".lnk") {
        Write-Warning "The shortcut path is not a .lnk file, so it was left untouched: $Path"
        return
    }

    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($Path)
    if ($shortcut.TargetPath -and (Test-SamePath $shortcut.TargetPath $ExpectedTarget)) {
        Remove-Item -LiteralPath $Path -Force
        Write-Host "Removed desktop shortcut: $Path"
    }
    else {
        Write-Warning "The shortcut does not point to this Promptly installation, so it was left untouched: $Path"
    }
}

$installPath = Get-NormalizedPath $InstallDirectory
$localAppDataPath = Get-NormalizedPath $env:LOCALAPPDATA
$userProfilePath = Get-NormalizedPath $env:USERPROFILE
$ollamaProgramPath = Get-NormalizedPath (Join-Path $env:LOCALAPPDATA "Programs\Ollama")
$ollamaModelPath = Get-NormalizedPath (Join-Path $env:USERPROFILE ".ollama")
$driveRoot = Get-NormalizedPath ([System.IO.Path]::GetPathRoot($installPath))

if ([string]::IsNullOrWhiteSpace($ShortcutPath)) {
    $ShortcutPath = Join-Path ([Environment]::GetFolderPath("Desktop")) "Promptly.lnk"
}
$shortcutPathResolved = Get-NormalizedPath $ShortcutPath
$runCommandPath = Get-NormalizedPath (Join-Path $installPath "Run-Promptly.cmd")

$unsafeTargets = @($driveRoot, $localAppDataPath, $userProfilePath)
foreach ($unsafeTarget in $unsafeTargets) {
    if (Test-SamePath $installPath $unsafeTarget) {
        throw "Refusing to remove unsafe path: $installPath"
    }
}

$protectedOllamaPaths = @($ollamaProgramPath, $ollamaModelPath)
foreach ($protectedPath in $protectedOllamaPaths) {
    if ((Test-PathWithin $protectedPath $installPath) -or (Test-PathWithin $installPath $protectedPath)) {
        throw "Refusing to remove a path that overlaps protected Ollama data: $installPath"
    }
}

if (-not (Test-Path -LiteralPath $installPath -PathType Container)) {
    Remove-OwnedShortcut $shortcutPathResolved $runCommandPath
    Write-Host "Promptly is not installed at $installPath. Nothing was removed."
    Write-Host "Ollama and downloaded models remain installed."
    exit 0
}

$installMarker = Join-Path $installPath ".promptly-install"
$legacyMarkers = @(
    "app.py",
    "run_promptly.py",
    "Run-Promptly.cmd",
    "requirements.txt",
    "static",
    "templates"
)
$hasLegacyMarkers = $true
foreach ($marker in $legacyMarkers) {
    if (-not (Test-Path -LiteralPath (Join-Path $installPath $marker))) {
        $hasLegacyMarkers = $false
        break
    }
}
if (-not (Test-Path -LiteralPath $installMarker -PathType Leaf) -and -not $hasLegacyMarkers) {
    throw "Refusing to remove $installPath because it does not look like a Promptly installation."
}

Write-Host "Promptly website uninstaller" -ForegroundColor Green
Write-Host "Website installation: $installPath"
Write-Host ""
Write-Warning "This removes Promptly's website files, private Python environment, settings, mentor libraries, uploaded references, and generated outputs."
Write-Host "Ollama will NOT be uninstalled." -ForegroundColor Green
Write-Host "Downloaded models under $ollamaModelPath will NOT be removed." -ForegroundColor Green

if (-not $Force) {
    $confirmation = Read-Host "Type UNINSTALL to remove Promptly"
    if ($confirmation -cne "UNINSTALL") {
        Write-Host "Uninstall cancelled. Nothing was removed."
        exit 0
    }
}

Write-Step "Stopping Promptly"
$runScriptPath = Get-NormalizedPath (Join-Path $installPath "run_promptly.py")
$venvPath = Get-NormalizedPath (Join-Path $installPath ".venv")
$stoppedProcessIds = @()
$taskkill = Join-Path $env:SystemRoot "System32\taskkill.exe"
foreach ($process in @(Get-Process -Name "python" -ErrorAction SilentlyContinue)) {
    $processPath = $null
    try {
        $processPath = $process.Path
    }
    catch {
        continue
    }
    if ($processPath -and (Test-PathWithin $processPath $venvPath)) {
        & $taskkill /PID $process.Id /T /F *> $null
        $stoppedProcessIds += $process.Id
    }
}

# A previous failed shutdown can leave the system Python child without its
# private-environment parent. Command-line inspection catches that case when
# Windows permits it, but uninstall remains usable without administrator rights.
try {
    $pythonProcesses = @(Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" -ErrorAction Stop)
    foreach ($process in $pythonProcesses) {
        $runsPromptly = (
            $process.CommandLine -and
            $process.CommandLine.IndexOf($runScriptPath, [System.StringComparison]::OrdinalIgnoreCase) -ge 0
        )
        if ($runsPromptly -and $stoppedProcessIds -notcontains $process.ProcessId) {
            Stop-Process -Id $process.ProcessId -Force -ErrorAction SilentlyContinue
            $stoppedProcessIds += $process.ProcessId
        }
    }
}
catch {
    Write-Verbose "Command-line process inspection was unavailable: $($_.Exception.Message)"
}
if ($stoppedProcessIds.Count -gt 0) {
    Start-Sleep -Milliseconds 500
    Write-Host "Stopped Promptly process(es): $($stoppedProcessIds -join ', ')"
}
else {
    Write-Host "Promptly was not running."
}

Write-Step "Removing Promptly website files"
Remove-OwnedShortcut $shortcutPathResolved $runCommandPath
if (Test-PathWithin (Get-Location).Path $installPath) {
    Set-Location $env:TEMP
}
Remove-Item -LiteralPath $installPath -Recurse -Force
if (Test-Path -LiteralPath $installPath) {
    throw "Promptly files could not be completely removed from $installPath."
}

Write-Host "`nPromptly was uninstalled successfully." -ForegroundColor Green
Write-Host "Ollama is still installed at: $ollamaProgramPath"
Write-Host "Downloaded models are still stored at: $ollamaModelPath"
