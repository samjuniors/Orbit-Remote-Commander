"""Disposable cross-platform tests of preview-first local setup."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SETUP = Path(__file__).resolve().parents[1] / "tools" / "windows_setup.py"
spec = importlib.util.spec_from_file_location("orbit_windows_setup", SETUP)
setup = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = setup
spec.loader.exec_module(setup)


class SetupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.project = self.base / "safe project"
        self.project.mkdir()
        (self.project / "example.txt").write_text("hello", encoding="utf-8")
        self.home = self.base / "install"

    def tearDown(self):
        self.tmp.cleanup()

    def test_preview_does_not_write(self):
        result = setup.install(self.home, str(self.project), apply=False)
        self.assertEqual(result["status"], "PREVIEW_ONLY")
        self.assertFalse(self.home.exists())
        self.assertFalse(result["auto_start"])
        self.assertFalse(result["network_listener"])

    def test_install_and_status_is_local_only(self):
        result = setup.install(self.home, str(self.project), apply=True)
        self.assertEqual(result["status"], "INSTALLED_LOCAL_ONLY")
        self.assertEqual(setup.status(self.home)["status"], "LOCAL_FILES_VERIFIED")
        self.assertFalse(setup.status(self.home)["remote_connected"])
        self.assertFalse(setup.status(self.home)["chatgpt_connected"])
        self.assertTrue((self.home / "run_orbit_rc.py").is_file())
        self.assertTrue((self.home / "orbit_rc_gateway.py").is_file())
        self.assertTrue((self.home / "orbit_rc_remote_config.py").is_file())
        self.assertTrue((self.home / "requirements-remote.txt").is_file())
        self.assertIn("Eduard Ruzga", (self.home / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8"))

    def test_resinstall_preserves_config(self):
        setup.install(self.home, str(self.project), apply=True)
        before = (self.home / "config.json").read_bytes()
        setup.install(self.home, None, apply=True)
        self.assertEqual((self.home / "config.json").read_bytes(), before)

    def test_launcher_disallows_write_even_if_config_claims_enabled(self):
        setup.install(self.home, str(self.project), apply=True)
        data = json.loads((self.home / "config.json").read_text())
        data["allow_write"] = True
        data["allow_checks"] = True
        (self.home / "config.json").write_text(json.dumps(data))
        requests = [
            {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
             "params": {"name": "orbit_rc_status", "arguments": {}}},
        ]
        proc = subprocess.run(
            [sys.executable, str(self.home / "run_orbit_rc.py")],
            input="\n".join(map(json.dumps, requests)) + "\n",
            text=True, capture_output=True, timeout=7,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        status = json.loads(json.loads(proc.stdout.strip())["result"]["content"][0]["text"])
        self.assertTrue(status["read_only"])
        self.assertFalse(status["checks_enabled"])
        self.assertEqual(status["remote_relay"], "NOT_CONFIGURED")

    def test_uninstall_keeps_config_and_unrelated_files(self):
        setup.install(self.home, str(self.project), apply=True)
        other = self.home / "user-notes.txt"
        other.write_text("keep")
        self.assertEqual(setup.uninstall(self.home, apply=False)["status"], "PREVIEW_ONLY")
        self.assertTrue((self.home / "run_orbit_rc.py").is_file())
        self.assertEqual(setup.uninstall(self.home, apply=True)["status"], "UNINSTALLED")
        self.assertTrue((self.home / "config.json").exists())
        self.assertEqual(other.read_text(), "keep")
        self.assertFalse((self.home / "orbit_remote_commander.py").exists())

    def test_uninstall_remove_config_is_separate_opt_in(self):
        setup.install(self.home, str(self.project), apply=True)
        setup.uninstall(self.home, apply=True, remove_config=True)
        self.assertFalse((self.home / "config.json").exists())
        self.assertFalse(self.home.exists())

    def test_refuse_modified_program_file_on_update_or_removal(self):
        setup.install(self.home, str(self.project), apply=True)
        (self.home / "orbit_remote_commander.py").write_text("custom")
        self.assertEqual(setup.status(self.home)["status"], "FILES_MODIFIED")
        with self.assertRaises(ValueError): setup.install(self.home, None, apply=True)
        with self.assertRaises(ValueError): setup.uninstall(self.home, apply=True)

    def test_refuse_unowned_program_file(self):
        self.home.mkdir()
        (self.home / "orbit_remote_commander.py").write_text("unowned")
        with self.assertRaises(ValueError): setup.install(self.home, str(self.project), apply=True)

    def test_refuse_unowned_config(self):
        self.home.mkdir()
        (self.home / "config.json").write_text('{"root":"elsewhere"}')
        with self.assertRaises(ValueError): setup.install(self.home, str(self.project), apply=True)

    def test_invalid_project_rejected(self):
        with self.assertRaises(Exception):
            setup.install(self.home, str(self.base / "not_found"), apply=True)
        self.assertFalse(self.home.exists())

    def test_home_symlink_denied(self):
        target = self.base / "other"
        target.mkdir()
        try: self.home.symlink_to(target, target_is_directory=True)
        except (OSError, NotImplementedError): self.skipTest("symlinks unavailable")
        with self.assertRaises(ValueError): setup.install(self.home, str(self.project), apply=True)


if __name__ == "__main__":
    unittest.main()
