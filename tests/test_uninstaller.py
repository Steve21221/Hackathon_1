import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
UNINSTALLER = PROJECT_ROOT / "installer" / "Promptly-Uninstall.ps1"
POWERSHELL = shutil.which("powershell")


@unittest.skipUnless(POWERSHELL, "Windows PowerShell is required")
class PromptlyUninstallerTestCase(unittest.TestCase):
    def run_uninstaller(self, install_directory: Path, shortcut_path: Path, env: dict[str, str]):
        return subprocess.run(
            [
                POWERSHELL,
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(UNINSTALLER),
                "-InstallDirectory",
                str(install_directory),
                "-ShortcutPath",
                str(shortcut_path),
                "-Force",
            ],
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
            check=False,
        )

    def test_removes_promptly_but_preserves_ollama_and_models(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            local_app_data = root / "LocalAppData"
            user_profile = root / "User"
            install_directory = local_app_data / "Promptly"
            ollama_directory = local_app_data / "Programs" / "Ollama"
            model_directory = user_profile / ".ollama" / "models"
            shortcut_path = root / "Desktop" / "Promptly.lnk"

            install_directory.mkdir(parents=True)
            (install_directory / ".promptly-install").write_text(
                "Promptly local website installation\n", encoding="ascii"
            )
            (install_directory / "website.txt").write_text("remove me", encoding="utf-8")
            ollama_directory.mkdir(parents=True)
            model_directory.mkdir(parents=True)
            ollama_sentinel = ollama_directory / "ollama.exe"
            model_sentinel = model_directory / "qwen-model"
            ollama_sentinel.write_text("keep", encoding="utf-8")
            model_sentinel.write_text("keep", encoding="utf-8")

            env = os.environ.copy()
            env["LOCALAPPDATA"] = str(local_app_data)
            env["USERPROFILE"] = str(user_profile)
            result = self.run_uninstaller(install_directory, shortcut_path, env)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertFalse(install_directory.exists())
            self.assertTrue(ollama_sentinel.is_file())
            self.assertTrue(model_sentinel.is_file())
            self.assertIn("Ollama is still installed", result.stdout)

    def test_refuses_to_remove_local_app_data_root(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            local_app_data = root / "LocalAppData"
            user_profile = root / "User"
            local_app_data.mkdir(parents=True)
            (local_app_data / ".promptly-install").write_text("unsafe", encoding="ascii")
            sentinel = local_app_data / "keep.txt"
            sentinel.write_text("keep", encoding="utf-8")

            env = os.environ.copy()
            env["LOCALAPPDATA"] = str(local_app_data)
            env["USERPROFILE"] = str(user_profile)
            result = self.run_uninstaller(local_app_data, root / "Promptly.lnk", env)

            self.assertNotEqual(result.returncode, 0)
            self.assertTrue(sentinel.is_file())
            self.assertIn("Refusing to remove unsafe path", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
