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
    def run_uninstaller(
        self,
        install_directory: Path,
        shortcut_path: Path,
        env: dict[str, str],
        *,
        keep_ollama: bool = False,
    ):
        command = [
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
        ]
        if keep_ollama:
            command.append("-KeepOllama")
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
            check=False,
        )

    def test_removes_promptly_ollama_and_every_model(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            local_app_data = root / "LocalAppData"
            app_data = root / "AppData"
            user_profile = root / "User"
            install_directory = local_app_data / "Promptly"
            ollama_directory = local_app_data / "Programs" / "Ollama"
            ollama_local_data = local_app_data / "Ollama"
            ollama_roaming_data = app_data / "Ollama"
            model_directory = user_profile / ".ollama" / "models"
            shortcut_path = root / "Desktop" / "Promptly.lnk"

            install_directory.mkdir(parents=True)
            (install_directory / ".promptly-install").write_text(
                "Promptly local website installation\n", encoding="ascii"
            )
            (install_directory / "website.txt").write_text("remove me", encoding="utf-8")
            ollama_directory.mkdir(parents=True)
            ollama_local_data.mkdir(parents=True)
            ollama_roaming_data.mkdir(parents=True)
            model_directory.mkdir(parents=True)
            ollama_sentinel = ollama_directory / "ollama.exe"
            model_sentinel = model_directory / "qwen-model"
            ollama_sentinel.write_text("keep", encoding="utf-8")
            model_sentinel.write_text("keep", encoding="utf-8")
            (ollama_local_data / "server.log").write_text("remove", encoding="utf-8")
            (ollama_roaming_data / "state.json").write_text("remove", encoding="utf-8")

            env = os.environ.copy()
            env["LOCALAPPDATA"] = str(local_app_data)
            env["APPDATA"] = str(app_data)
            env["USERPROFILE"] = str(user_profile)
            env.pop("OLLAMA_MODELS", None)
            result = self.run_uninstaller(install_directory, shortcut_path, env)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertFalse(install_directory.exists())
            self.assertFalse(ollama_sentinel.exists())
            self.assertFalse(model_sentinel.exists())
            self.assertFalse(ollama_local_data.exists())
            self.assertFalse(ollama_roaming_data.exists())
            self.assertIn("all downloaded Ollama models were removed", result.stdout)

    def test_keep_ollama_switch_removes_only_promptly(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            local_app_data = root / "LocalAppData"
            app_data = root / "AppData"
            user_profile = root / "User"
            install_directory = local_app_data / "Promptly"
            ollama_sentinel = local_app_data / "Programs" / "Ollama" / "ollama.exe"
            model_sentinel = user_profile / ".ollama" / "models" / "qwen-model"
            shortcut_path = root / "Desktop" / "Promptly.lnk"

            install_directory.mkdir(parents=True)
            (install_directory / ".promptly-install").write_text(
                "Promptly local website installation\n", encoding="ascii"
            )
            ollama_sentinel.parent.mkdir(parents=True)
            model_sentinel.parent.mkdir(parents=True)
            ollama_sentinel.write_text("keep", encoding="utf-8")
            model_sentinel.write_text("keep", encoding="utf-8")

            env = os.environ.copy()
            env["LOCALAPPDATA"] = str(local_app_data)
            env["APPDATA"] = str(app_data)
            env["USERPROFILE"] = str(user_profile)
            env.pop("OLLAMA_MODELS", None)
            result = self.run_uninstaller(
                install_directory,
                shortcut_path,
                env,
                keep_ollama=True,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertFalse(install_directory.exists())
            self.assertTrue(ollama_sentinel.is_file())
            self.assertTrue(model_sentinel.is_file())
            self.assertIn("Ollama and downloaded models were kept", result.stdout)

    def test_removes_custom_ollama_model_store(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            local_app_data = root / "LocalAppData"
            app_data = root / "AppData"
            user_profile = root / "User"
            install_directory = local_app_data / "Promptly"
            custom_models = root / "LargeModelDrive" / "ollama-models"
            shortcut_path = root / "Desktop" / "Promptly.lnk"

            install_directory.mkdir(parents=True)
            (install_directory / ".promptly-install").write_text(
                "Promptly local website installation\n", encoding="ascii"
            )
            (custom_models / "blobs").mkdir(parents=True)
            (custom_models / "manifests").mkdir()
            (custom_models / "blobs" / "sha256-model").write_text(
                "remove", encoding="utf-8"
            )

            env = os.environ.copy()
            env["LOCALAPPDATA"] = str(local_app_data)
            env["APPDATA"] = str(app_data)
            env["USERPROFILE"] = str(user_profile)
            env["OLLAMA_MODELS"] = str(custom_models)
            result = self.run_uninstaller(install_directory, shortcut_path, env)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertFalse(custom_models.exists())
            self.assertIn("custom Ollama model directory", result.stdout)

    def test_refuses_unsafe_custom_model_path(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            local_app_data = root / "LocalAppData"
            app_data = root / "AppData"
            user_profile = root / "User"
            install_directory = local_app_data / "Promptly"
            shortcut_path = root / "Desktop" / "Promptly.lnk"

            install_directory.mkdir(parents=True)
            (install_directory / ".promptly-install").write_text(
                "Promptly local website installation\n", encoding="ascii"
            )
            user_profile.mkdir(exist_ok=True)
            sentinel = user_profile / "keep.txt"
            sentinel.write_text("keep", encoding="utf-8")

            env = os.environ.copy()
            env["LOCALAPPDATA"] = str(local_app_data)
            env["APPDATA"] = str(app_data)
            env["USERPROFILE"] = str(user_profile)
            env["OLLAMA_MODELS"] = str(user_profile)
            result = self.run_uninstaller(install_directory, shortcut_path, env)

            self.assertNotEqual(result.returncode, 0)
            self.assertTrue(sentinel.is_file())
            self.assertTrue(install_directory.is_dir())
            self.assertIn("Refusing to remove unsafe custom Ollama model path", result.stdout + result.stderr)

    def test_removes_owned_shortcut_with_virtualized_target(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            local_app_data = root / "LocalAppData"
            app_data = root / "AppData"
            user_profile = root / "User"
            install_directory = local_app_data / "Promptly"
            shortcut_path = root / "Desktop" / "Promptly.lnk"

            install_directory.mkdir(parents=True)
            shortcut_path.parent.mkdir(parents=True)
            (install_directory / ".promptly-install").write_text(
                "Promptly local website installation\n", encoding="ascii"
            )
            shortcut_literal = str(shortcut_path).replace("'", "''")
            install_literal = str(install_directory).replace("'", "''")
            virtual_target = str(
                root / "VirtualizedUser" / "Promptly" / "Run-Promptly.cmd"
            ).replace("'", "''")
            create_shortcut = rf"""
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut('{shortcut_literal}')
$shortcut.TargetPath = '{virtual_target}'
$shortcut.WorkingDirectory = '{install_literal}'
$shortcut.Description = 'Start the local Promptly mentor-feedback website'
$shortcut.Save()
"""
            created = subprocess.run(
                [POWERSHELL, "-NoProfile", "-Command", create_shortcut],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            self.assertEqual(created.returncode, 0, created.stdout + created.stderr)
            self.assertTrue(shortcut_path.is_file())

            env = os.environ.copy()
            env["LOCALAPPDATA"] = str(local_app_data)
            env["APPDATA"] = str(app_data)
            env["USERPROFILE"] = str(user_profile)
            env.pop("OLLAMA_MODELS", None)
            result = self.run_uninstaller(
                install_directory,
                shortcut_path,
                env,
                keep_ollama=True,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertFalse(shortcut_path.exists())

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
            env["APPDATA"] = str(root / "AppData")
            env["USERPROFILE"] = str(user_profile)
            env.pop("OLLAMA_MODELS", None)
            result = self.run_uninstaller(local_app_data, root / "Promptly.lnk", env)

            self.assertNotEqual(result.returncode, 0)
            self.assertTrue(sentinel.is_file())
            self.assertIn("Refusing to remove unsafe path", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
