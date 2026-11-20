import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'src' / 'orbit_remote_commander.py'
sys.path.insert(0, str(SOURCE.parent))
spec = importlib.util.spec_from_file_location('orbit_rc', SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class CommanderTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / 'project'
        self.root.mkdir()
        (self.root / 'hello.txt').write_text('hello', encoding='utf-8')
        (self.root / '.env').write_text('hidden', encoding='utf-8')
        self.com = module.Commander(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_requires_scoped_root(self):
        with self.assertRaises(module.Rejected): module.Commander(None)
        with self.assertRaises(module.Rejected): module.Commander(Path(self.root.anchor))

    def test_status_is_local_not_remote(self):
        self.assertEqual(self.com.status()['remote_relay'], 'NOT_CONFIGURED')
        self.assertTrue(self.com.status()['read_only'])

    def test_read_and_hash(self):
        result = self.com.read_text('hello.txt')
        self.assertEqual(result['text'], 'hello')
        self.assertEqual(result['sha256'], hashlib.sha256(b'hello').hexdigest())

    def test_traversal_and_secret_denials(self):
        for p in ['../other', '..\\\\other', '/etc/passwd', r'C:\\Windows\\system.ini', r'C:relative.txt', r'\\\\server\\share\\file', '.env', '.ssh/key', 'secret.pem', '.env.custom']:
            with self.subTest(p=p):
                with self.assertRaises(module.Rejected): self.com.read_text(p)

    def test_symlink_escape_denied(self):
        outside = Path(self.tmp.name) / 'outside.txt'
        outside.write_text('outside')
        try: (self.root / 'link.txt').symlink_to(outside)
        except (OSError, NotImplementedError): self.skipTest('No symlinks available')
        with self.assertRaises(module.Rejected): self.com.read_text('link.txt')
        self.assertNotIn('link.txt', [x['name'] for x in self.com.list_dir()['entries']])

    def test_secret_symlink_inside_project_is_denied(self):
        alias = self.root / 'public.txt'
        try:
            alias.symlink_to(self.root / '.env')
        except (OSError, NotImplementedError):
            self.skipTest('No symlinks available')
        with self.assertRaises(module.Rejected):
            self.com.read_text('public.txt')
        self.assertNotIn('public.txt', [x['name'] for x in self.com.list_dir()['entries']])

    def test_write_is_default_denied(self):
        expected = hashlib.sha256(b'hello').hexdigest()
        with self.assertRaises(module.Rejected): self.com.write_text('hello.txt', 'changed', expected, True)
        self.assertEqual((self.root / 'hello.txt').read_text(), 'hello')

    def test_stale_and_confirmation_protection(self):
        com = module.Commander(self.root, allow_write=True)
        expected = hashlib.sha256(b'hello').hexdigest()
        with self.assertRaises(module.Rejected): com.write_text('hello.txt', 'changed', expected, False)
        with self.assertRaises(module.Rejected): com.write_text('hello.txt', 'changed', '0' * 64, True)
        out = com.write_text('hello.txt', 'changed', expected, True)
        self.assertTrue(out['written'])
        self.assertEqual((self.root / 'hello.txt').read_text(), 'changed')

    def test_check_is_default_denied(self):
        with self.assertRaises(module.Rejected): self.com.run_check('git-status')
        with self.assertRaises(module.Rejected): module.Commander(self.root, allow_checks=True).run_check('arbitrary')

    def test_nonutf8_and_big_denials(self):
        (self.root / 'binary.bin').write_bytes(b'\xff\xfe')
        (self.root / 'huge.txt').write_bytes(b'x' * (module.MAX_READ_BYTES + 1))
        for p in ['binary.bin', 'huge.txt']:
            with self.assertRaises(module.Rejected): self.com.read_text(p)

    def test_large_directory_inventory_is_bounded(self):
        for i in range(module.MAX_ENTRIES + 9):
            (self.root / f'file-{i:03}.txt').write_text('x', encoding='utf-8')
        result = self.com.list_dir()
        self.assertLessEqual(len(result['entries']), module.MAX_ENTRIES)
        self.assertTrue(result['possibly_truncated'])

    def test_existing_large_file_cannot_be_overwritten(self):
        big = self.root / 'large.txt'
        data = b'x' * (module.MAX_READ_BYTES + 1)
        big.write_bytes(data)
        com = module.Commander(self.root, allow_write=True)
        with self.assertRaises(module.Rejected):
            com.write_text('large.txt', 'small', hashlib.sha256(data).hexdigest(), True)

    def test_project_literal_filename_and_content_search(self):
        (self.root / "notes.txt").write_text("first\nNeedle second\nthird needle\n", encoding="utf-8")
        found = self.com.search_files("needle")
        self.assertEqual([x["line"] for x in found["results"]], [2, 3])
        names = self.com.search_files("NOTES.TXT", mode="filename")
        self.assertEqual(names["results"][0]["path"], "notes.txt")
        exact = self.com.search_files("needle", case_sensitive=True)
        self.assertEqual([x["line"] for x in exact["results"]], [3])

    def test_search_excludes_secret_and_symlink_escape(self):
        (self.root / "allowed.txt").write_text("needle", encoding="utf-8")
        (self.root / ".env").write_text("needle", encoding="utf-8")
        other = Path(self.tmp.name) / "outside.txt"
        other.write_text("needle", encoding="utf-8")
        try:
            (self.root / "pointer.txt").symlink_to(other)
        except (OSError, NotImplementedError):
            pass
        result = self.com.search_files("needle")
        self.assertEqual({x["path"] for x in result["results"]}, {"allowed.txt"})
        names = self.com.search_files(".env", mode="filename")
        self.assertEqual(names["results"], [])

    def test_search_budgets_and_escape(self):
        for pattern, kwargs in [("", {}), ("x\nx", {}), ("x", {"max_results": True}),
                                ("x", {"max_results": 41}), ("x", {"mode": "regex"}),
                                ("x", {"path": "../"})]:
            with self.subTest(pattern=pattern, kwargs=kwargs):
                with self.assertRaises(module.Rejected):
                    self.com.search_files(pattern, **kwargs)
        for i in range(60):
            (self.root / f"search-{i}.txt").write_text("entry", encoding="utf-8")
        result = self.com.search_files("entry", max_results=10)
        self.assertEqual(len(result["results"]), 10)
        self.assertTrue(result["possibly_truncated"])

    def test_preview_and_surgical_edit(self):
        (self.root / "edit.txt").write_bytes(b"head\r\nalpha\r\nend\r\n")
        preview = self.com.preview_edit_block("edit.txt", "alpha\nend", "BETA\nlast")
        self.assertFalse(preview["write_performed"])
        self.assertEqual(preview["newline_style"], "CRLF")
        self.assertEqual((self.root / "edit.txt").read_bytes(), b"head\r\nalpha\r\nend\r\n")
        with self.assertRaises(module.Rejected):
            self.com.edit_block("edit.txt", "alpha", "BETA", preview["expected_sha256"], True)
        writer = module.Commander(self.root, allow_write=True)
        with self.assertRaises(module.Rejected):
            writer.edit_block("edit.txt", "alpha", "BETA", preview["expected_sha256"], False)
        modified = writer.edit_block("edit.txt", "alpha\nend", "BETA\nlast",
                                     preview["expected_sha256"], True)
        self.assertTrue(modified["written"])
        self.assertEqual((self.root / "edit.txt").read_bytes(), b"head\r\nBETA\r\nlast\r\n")
        with self.assertRaises(module.Rejected):
            writer.edit_block("edit.txt", "BETA", "BAD", preview["expected_sha256"], True)

    def test_preview_denies_ambiguous_or_secret_edit(self):
        (self.root / "repeat.txt").write_text("value value", encoding="utf-8")
        with self.assertRaises(module.BlockEditError):
            self.com.preview_edit_block("repeat.txt", "value", "new")
        with self.assertRaises(module.Rejected):
            self.com.preview_edit_block(".env", "hidden", "changed")

    def test_mcp_stdio_handshake(self):
        env = dict(os.environ, ORBIT_RC_ROOT=str(self.root))
        env.pop('ORBIT_RC_ALLOW_WRITE', None)
        env.pop('ORBIT_RC_ALLOW_CHECKS', None)
        messages = [
            {'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {'protocolVersion': module.PROTOCOL}},
            {'jsonrpc': '2.0', 'method': 'notifications/initialized'},
            {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list'},
            {'jsonrpc': '2.0', 'id': 3, 'method': 'tools/call', 'params': {'name': 'orbit_rc_status', 'arguments': {}}},
            {'jsonrpc': '2.0', 'id': 4, 'method': 'tools/call', 'params': {'name': 'orbit_rc_read', 'arguments': {'path': '.env'}}},
        ]
        proc = subprocess.run([sys.executable, str(SOURCE)], input='\n'.join(json.dumps(m) for m in messages) + '\n',
                              capture_output=True, text=True, env=env, timeout=5)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        rows = [json.loads(line) for line in proc.stdout.splitlines()]
        self.assertEqual([r['id'] for r in rows], [1, 2, 3, 4])
        self.assertEqual(len(rows[1]['result']['tools']), 8)
        self.assertTrue(rows[3]['result']['isError'])


if __name__ == '__main__': unittest.main()
