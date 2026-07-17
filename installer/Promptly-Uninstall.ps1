param(
    [string]$InstallDirectory = "$env:LOCALAPPDATA\Promptly",
    [string]$ShortcutPath = "",
    [switch]$KeepOllama,
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

function Get-DesktopPath {
    $desktop = [Environment]::GetFolderPath("Desktop")
    if (-not [string]::IsNullOrWhiteSpace($desktop)) {
        return Get-NormalizedPath $desktop
    }

    $fallbacks = @()
    if (-not [string]::IsNullOrWhiteSpace($env:OneDrive)) {
        $fallbacks += Join-Path $env:OneDrive "Desktop"
    }
    if (-not [string]::IsNullOrWhiteSpace($env:USERPROFILE)) {
        $fallbacks += Join-Path $env:USERPROFILE "Desktop"
    }
    foreach ($fallback in $fallbacks) {
        if (Test-Path -LiteralPath $fallback -PathType Container) {
            return Get-NormalizedPath $fallback
        }
    }
    if ($fallbacks.Count -gt 0) {
        return Get-NormalizedPath $fallbacks[0]
    }
    throw "The Windows desktop folder could not be located. Pass -ShortcutPath explicitly."
}

function Assert-SafeRemovalPath([string]$Path, [string]$Label) {
    $candidate = Get-NormalizedPath $Path
    $protectedRoots = @(
        [System.IO.Path]::GetPathRoot($candidate),
        $env:USERPROFILE,
        $env:LOCALAPPDATA,
        $env:APPDATA,
        $env:TEMP,
        $env:SystemRoot,
        $env:ProgramFiles,
        ${env:ProgramFiles(x86)}
    ) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }

    foreach ($protectedRoot in $protectedRoots) {
        if ((Test-SamePath $candidate $protectedRoot) -or
            (Test-PathWithin $protectedRoot $candidate)) {
            throw "Refusing to remove unsafe $Label path: $candidate"
        }
    }
    return $candidate
}

function Remove-SafeDirectory([string]$Path, [string]$Label) {
    $safePath = Assert-SafeRemovalPath $Path $Label
    if (-not (Test-Path -LiteralPath $safePath)) {
        return
    }
    if (Test-PathWithin (Get-Location).Path $safePath) {
        Set-Location $env:TEMP
    }

    for ($attempt = 1; $attempt -le 3; $attempt++) {
        try {
            Remove-Item -LiteralPath $safePath -Recurse -Force -ErrorAction Stop
            break
        }
        catch {
            if ($attempt -eq 3) {
                throw "Could not completely remove $Label at ${safePath}: $($_.Exception.Message)"
            }
            Start-Sleep -Milliseconds 750
        }
    }
    if (Test-Path -LiteralPath $safePath) {
        throw "$Label files could not be completely removed from $safePath."
    }
    Write-Host "Removed ${Label}: $safePath"
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
    $expectedDirectory = Split-Path -Parent $ExpectedTarget
    $targetMatches = $shortcut.TargetPath -and (Test-SamePath $shortcut.TargetPath $ExpectedTarget)
    $descriptionMatches = $shortcut.Description -eq "Start the local Promptly mentor-feedback website"
    $workingDirectoryMatches = (
        $shortcut.WorkingDirectory -and
        (Test-SamePath $shortcut.WorkingDirectory $expectedDirectory)
    )
    if ($targetMatches -or ($descriptionMatches -and $workingDirectoryMatches)) {
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
$ollamaLocalDataPath = Get-NormalizedPath (Join-Path $env:LOCALAPPDATA "Ollama")
$ollamaRoamingDataPath = Get-NormalizedPath (Join-Path $env:APPDATA "Ollama")
$customOllamaModelPath = $null
if (-not $KeepOllama -and -not [string]::IsNullOrWhiteSpace($env:OLLAMA_MODELS)) {
    $customOllamaModelPath = Assert-SafeRemovalPath $env:OLLAMA_MODELS "custom Ollama model"
    if ((Test-Path -LiteralPath $customOllamaModelPath -PathType Container) -and
        -not (Test-Path -LiteralPath (Join-Path $customOllamaModelPath "blobs") -PathType Container) -and
        -not (Test-Path -LiteralPath (Join-Path $customOllamaModelPath "manifests") -PathType Container)) {
        throw "Refusing to remove custom Ollama model path because it does not look like an Ollama model store: $customOllamaModelPath"
    }
}
$driveRoot = Get-NormalizedPath ([System.IO.Path]::GetPathRoot($installPath))

if ([string]::IsNullOrWhiteSpace($ShortcutPath)) {
    $ShortcutPath = Join-Path (Get-DesktopPath) "Promptly.lnk"
}
$shortcutPathResolved = Get-NormalizedPath $ShortcutPath
$runCommandPath = Get-NormalizedPath (Join-Path $installPath "Run-Promptly.cmd")

$unsafeTargets = @($driveRoot, $localAppDataPath, $userProfilePath)
foreach ($unsafeTarget in $unsafeTargets) {
    if (Test-SamePath $installPath $unsafeTarget) {
        throw "Refusing to remove unsafe path: $installPath"
    }
}

$separateOllamaPaths = @($ollamaProgramPath, $ollamaModelPath, $ollamaLocalDataPath)
foreach ($ollamaPath in $separateOllamaPaths) {
    if ((Test-PathWithin $ollamaPath $installPath) -or (Test-PathWithin $installPath $ollamaPath)) {
        throw "Refusing to remove a Promptly path that overlaps separate Ollama data: $installPath"
    }
}

$promptlyInstalled = Test-Path -LiteralPath $installPath -PathType Container
if ($promptlyInstalled) {
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
}
else {
    Write-Host "Promptly is not installed at $installPath."
}

Write-Host "Promptly and local-model uninstaller" -ForegroundColor Green
Write-Host "Website installation: $installPath"
Write-Host ""
Write-Warning "This removes Promptly's website files, private Python environment, settings, mentor libraries, uploaded references, and generated outputs."
if ($KeepOllama) {
    Write-Host "Ollama and its downloaded models will be kept because -KeepOllama was specified." -ForegroundColor Yellow
}
else {
    Write-Warning "This also uninstalls Ollama and permanently deletes EVERY downloaded Ollama model, including Qwen, Phi, and models not installed by Promptly."
    Write-Host "Ollama program: $ollamaProgramPath"
    Write-Host "Ollama models and user data: $ollamaModelPath"
    if ($customOllamaModelPath) {
        Write-Host "Custom Ollama model directory: $customOllamaModelPath"
    }
}

if (-not $Force) {
    $confirmationText = if ($KeepOllama) { "UNINSTALL" } else { "UNINSTALL ALL" }
    $confirmation = Read-Host "Type $confirmationText to continue"
    if ($confirmation -cne $confirmationText) {
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

if (-not $KeepOllama) {
    Write-Step "Stopping Ollama and local model processes"
    $stoppedOllamaProcessIds = @()
    foreach ($process in @(Get-Process -ErrorAction SilentlyContinue)) {
        $processPath = $null
        try {
            $processPath = $process.Path
        }
        catch {
            continue
        }
        if ($processPath -and (Test-PathWithin $processPath $ollamaProgramPath)) {
            & $taskkill /PID $process.Id /T /F *> $null
            $stoppedOllamaProcessIds += $process.Id
        }
    }
    if ($stoppedOllamaProcessIds.Count -gt 0) {
        Start-Sleep -Milliseconds 750
        Write-Host "Stopped Ollama process(es): $($stoppedOllamaProcessIds -join ', ')"
    }
    else {
        Write-Host "Ollama was not running."
    }

    $ollamaUninstaller = Join-Path $ollamaProgramPath "unins000.exe"
    if (Test-Path -LiteralPath $ollamaUninstaller -PathType Leaf) {
        Write-Step "Running the Ollama application uninstaller"
        try {
            $uninstallProcess = Start-Process `
                -FilePath $ollamaUninstaller `
                -ArgumentList "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART" `
                -WindowStyle Hidden `
                -Wait `
                -PassThru
            if ($uninstallProcess.ExitCode -ne 0) {
                Write-Warning "Ollama's application uninstaller returned exit code $($uninstallProcess.ExitCode). Residual files will still be removed."
            }
        }
        catch {
            Write-Warning "Ollama's application uninstaller could not run. Residual files will still be removed: $($_.Exception.Message)"
        }
    }
}

Write-Step "Removing Promptly website files"
Remove-OwnedShortcut $shortcutPathResolved $runCommandPath
if ($promptlyInstalled) {
    Remove-SafeDirectory $installPath "Promptly installation"
}

if (-not $KeepOllama) {
    Write-Step "Removing Ollama, downloaded models, and local data"
    $ollamaRemovalTargets = @(
        @{ Path = $ollamaProgramPath; Label = "Ollama application" },
        @{ Path = $ollamaLocalDataPath; Label = "Ollama local data" },
        @{ Path = $ollamaRoamingDataPath; Label = "Ollama roaming data" },
        @{ Path = $ollamaModelPath; Label = "Ollama models and user data" }
    )
    if ($customOllamaModelPath -and -not (Test-SamePath $customOllamaModelPath $ollamaModelPath)) {
        $ollamaRemovalTargets += @{
            Path = $customOllamaModelPath
            Label = "custom Ollama model directory"
        }
    }
    foreach ($target in $ollamaRemovalTargets) {
        Remove-SafeDirectory $target.Path $target.Label
    }
    [Environment]::SetEnvironmentVariable("OLLAMA_MODELS", $null, "User")
    Remove-Item Env:OLLAMA_MODELS -ErrorAction SilentlyContinue
}

Write-Host "`nPromptly was uninstalled successfully." -ForegroundColor Green
if ($KeepOllama) {
    Write-Host "Ollama and downloaded models were kept." -ForegroundColor Yellow
}
else {
    Write-Host "Ollama and all downloaded Ollama models were removed." -ForegroundColor Green
}
