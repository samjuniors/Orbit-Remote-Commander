import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile

SOURCE = Path(__file__).resolve().parents[1] / "scripts" / "build_candidate.py"
spec = importlib.util.spec_from_file_location("orbit_candidate", SOURCE)
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)


class BuildTests(unittest.TestCase):
    def test_candidate_is_deterministic_and_scope_bounded(self):
        with tempfile.TemporaryDirectory() as d:
            a = Path(d) / "a.zip"
            b = Path(d) / "b.zip"
            candidate.build(a)
            candidate.build(b)
            self.assertEqual(a.read_bytes(), b.read_bytes())
            with zipfile.ZipFile(a) as f:
                self.assertEqual(sorted(f.namelist()), sorted(candidate.PAYLOAD))
                self.assertFalse(any(name.startswith("/") or ".." in Path(name).parts
                                     or name.endswith(".env") for name in f.namelist()))
                self.assertIn("src/run_orbit_rc.py", f.namelist())
                self.assertIn("Orbit Remote Setup.cmd", f.namelist())
            sha = a.with_name("a.zip.sha256").read_text()
            self.assertEqual(len(sha.split()[0]), 64)

    def test_all_inputs_are_existing_regular_files(self):
        for path in candidate.PAYLOAD:
            self.assertTrue((candidate.ROOT / path).is_file(), path)


if __name__ == "__main__":
    unittest.main()
