"""DesktopCommanderMCP MIT-adapted exact editing behavior, no ambiguous fuzzing."""
import importlib.util
from pathlib import Path
import sys
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "src" / "orbit_rc_text_ops.py"
spec = importlib.util.spec_from_file_location("orbit_rc_text_ops_test", SOURCE)
ops = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ops)


class TextOpsTests(unittest.TestCase):
    def test_detect_and_normalize_preserves_windows_crlf(self):
        self.assertEqual(ops.detect_line_ending("alpha\r\nbeta\n"), "\r\n")
        self.assertEqual(ops.normalize_line_endings("x\ny\rz\r\n", "\r\n"), "x\r\ny\r\nz\r\n")

    def test_detect_cr_only(self):
        self.assertEqual(ops.detect_line_ending("alpha\rbeta"), "\r")
        self.assertEqual(ops.normalize_line_endings("a\nb", "\r"), "a\rb")

    def test_exact_replacement_crlf_multiline(self):
        result = ops.exact_block_replacement("a\r\nb\r\nc", "a\nb", "x\ny")
        self.assertEqual(result["updated"], "x\r\ny\r\nc")
        self.assertEqual(result["replacements"], 1)
        self.assertEqual(result["newline_style"], "CRLF")

    def test_multiple_exact_occurrences(self):
        result = ops.exact_block_replacement("a a a", "a", "b", expected_replacements=3)
        self.assertEqual(result["updated"], "b b b")
        self.assertEqual(result["replacements"], 3)

    def test_refuse_ambiguous_count(self):
        with self.assertRaisesRegex(ops.BlockEditError, "expected 1, found 2"):
            ops.exact_block_replacement("same same", "same", "new")
        with self.assertRaisesRegex(ops.BlockEditError, "expected 1, found 0"):
            ops.exact_block_replacement("hello", "other", "new")

    def test_no_fuzzy_guess(self):
        with self.assertRaises(ops.BlockEditError):
            ops.exact_block_replacement("different", "diferent", "new")

    def test_refuse_empty_search_and_invalid_expected(self):
        for query, replacements in [("", 1), ("x", 0), ("x", 9), ("x", True), ("x", "1")]:
            with self.subTest(query=query, replacements=replacements):
                with self.assertRaises(ops.BlockEditError):
                    ops.exact_block_replacement("x", query, "new", replacements)

    def test_size_bound_and_output_bound(self):
        with self.assertRaises(ops.BlockEditError):
            ops.exact_block_replacement("a", "a", "x" * 1200, max_bytes=100)
        with self.assertRaises(ops.BlockEditError):
            ops.exact_block_replacement("a" * 102, "a", "b", max_bytes=100)

    def test_unicode_and_preview_bounded(self):
        result = ops.exact_block_replacement("x" * 400 + "café" + "x" * 400, "café", "tea")
        self.assertEqual(result["updated"].count("tea"), 1)
        self.assertTrue(result["preview_truncated"])
        self.assertLess(len(result["preview"]), 250)


if __name__ == "__main__":
    unittest.main()
