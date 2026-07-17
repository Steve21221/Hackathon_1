import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INSTALLER = PROJECT_ROOT / "installer" / "Promptly-Setup.ps1"
POWERSHELL = shutil.which("powershell")


@unittest.skipUnless(POWERSHELL, "Windows PowerShell is required")
class PromptlyInstallerTestCase(unittest.TestCase):
    def test_upgrade_replaces_only_private_environment(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            install_directory = Path(temporary_directory) / "Promptly"
            venv_python = install_directory / ".venv" / "Scripts" / "python.exe"
            settings = install_directory / "user_settings.json"
            mentor_file = install_directory / "mentor_files" / "mentor" / "prompt.txt"
            venv_python.parent.mkdir(parents=True)
            mentor_file.parent.mkdir(parents=True)
            venv_python.write_text("stale environment", encoding="utf-8")
            settings.write_text('{"MODEL_PROVIDER": "ollama"}', encoding="utf-8")
            mentor_file.write_text("preserve mentor", encoding="utf-8")

            installer_path = str(INSTALLER).replace("'", "''")
            command = rf"""
$tokens = $null
$errors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile('{installer_path}', [ref]$tokens, [ref]$errors)
if ($errors.Count -gt 0) {{ throw ($errors | ForEach-Object {{ $_.Message }} | Out-String) }}
$wanted = @('Get-NormalizedPath', 'Test-PathWithin', 'Stop-PromptlyProcesses', 'Remove-ExistingPrivateEnvironment')
$definitions = $ast.FindAll({{ param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $wanted -contains $node.Name }}, $true)
Invoke-Expression (($definitions | ForEach-Object {{ $_.Extent.Text }}) -join "`n")
$installPath = $env:PROMPTLY_TEST_INSTALL
Stop-PromptlyProcesses $installPath
Remove-ExistingPrivateEnvironment $installPath
if (Test-Path -LiteralPath (Join-Path $installPath '.venv')) {{ throw 'Private environment was not removed.' }}
if (-not (Test-Path -LiteralPath (Join-Path $installPath 'user_settings.json'))) {{ throw 'Settings were removed.' }}
if (-not (Test-Path -LiteralPath (Join-Path $installPath 'mentor_files\mentor\prompt.txt'))) {{ throw 'Mentor data was removed.' }}
"""
            environment = os.environ.copy()
            environment["PROMPTLY_TEST_INSTALL"] = str(install_directory)
            result = subprocess.run(
                [
                    POWERSHELL,
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    command,
                ],
                capture_output=True,
                text=True,
                timeout=30,
                env=environment,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertFalse((install_directory / ".venv").exists())
            self.assertTrue(settings.is_file())
            self.assertTrue(mentor_file.is_file())


if __name__ == "__main__":
    unittest.main()
