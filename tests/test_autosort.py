"""
Unit tests for AutoSort — stdlib unittest only, zero extra deps.

Run: python3 -m unittest tests/test_autosort.py -v
"""
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from organizer import (
    clean_empty,
    get_category_for_extension,
    get_date_subfolder,
    human_size,
    load_custom_config,
    organize,
    undo_last,
    watch,
)


# ── Helpers ─────────────────────────────────────────────────────────────────

class AutosortTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)


# ── Category + helpers ──────────────────────────────────────────────────────

class TestHelpers(AutosortTestCase):
    def test_extension_known(self):
        self.assertEqual(get_category_for_extension(".pdf"), "Documents")

    def test_extension_unknown(self):
        self.assertEqual(get_category_for_extension(".xyz"), "Others")

    def test_extension_case_insensitive(self):
        self.assertEqual(get_category_for_extension(".PDF"), "Documents")

    def test_custom_categories_override(self):
        from config import FILE_CATEGORIES
        cats = {k: list(v) for k, v in FILE_CATEGORIES.items()}
        cats["Extras"] = [".foo"]
        self.assertEqual(get_category_for_extension(".foo", cats), "Extras")
        self.assertEqual(get_category_for_extension(".pdf", cats), "Documents")

    def test_custom_fallback(self):
        self.assertEqual(get_category_for_extension(".weird", fallback="Unknown"), "Unknown")

    def test_human_size_bytes(self):
        self.assertEqual(human_size(500), "500B")

    def test_human_size_kilobytes(self):
        self.assertEqual(human_size(2048), "2.0KB")

    def test_human_size_megabytes(self):
        self.assertEqual(human_size(5_242_880), "5.0MB")

    def test_get_date_subfolder(self):
        import time
        now_ts = time.time()
        sub = get_date_subfolder(now_ts)
        self.assertRegex(sub, r"\d{4}-\d{2}")


# ── organize ────────────────────────────────────────────────────────────────

class TestOrganize(AutosortTestCase):
    def test_basic_move(self):
        (Path(self.tmp) / "a.pdf").write_text("pdf")
        (Path(self.tmp) / "b.png").write_text("png")

        organize(self.tmp, dry_run=False)

        self.assertTrue((Path(self.tmp) / "Documents" / "a.pdf").exists())
        self.assertTrue((Path(self.tmp) / "Images" / "b.png").exists())

    def test_dry_run_no_move(self):
        (Path(self.tmp) / "x.pdf").write_text("pdf")

        organize(self.tmp, dry_run=True)

        self.assertTrue((Path(self.tmp) / "x.pdf").exists())
        self.assertFalse((Path(self.tmp) / "Documents").exists())

    def test_ignores_dirs_and_dotfiles(self):
        (Path(self.tmp) / ".hidden").write_text("x")
        (Path(self.tmp) / "skipme").mkdir()
        (Path(self.tmp) / "a.pdf").write_text("pdf")

        organize(self.tmp, dry_run=False)

        self.assertTrue((Path(self.tmp) / "Documents" / "a.pdf").exists())
        self.assertTrue((Path(self.tmp) / ".hidden").exists())
        self.assertTrue((Path(self.tmp) / "skipme").exists())

    def test_duplicate_renamed(self):
        (Path(self.tmp) / "a.pdf").write_text("1")
        (Path(self.tmp) / "Documents").mkdir()
        (Path(self.tmp) / "Documents" / "a.pdf").write_text("dup")

        organize(self.tmp, dry_run=False)

        dests = sorted(p.name for p in (Path(self.tmp) / "Documents").iterdir())
        self.assertEqual(dests, ["a.pdf", "a_1.pdf"])

    def test_custom_config(self):
        (Path(self.tmp) / "x.rom").write_text("rom")
        cfg = self.tmp + "/rules.json"
        with open(cfg, "w") as f:
            json.dump({"categories": {"Games": [".rom"]}, "fallback": "Misc"}, f)

        organize(self.tmp, dry_run=False, categories=load_custom_config(cfg)[0])

        self.assertTrue((Path(self.tmp) / "Games" / "x.rom").exists())

    def test_nonexistent_path(self):
        out = []
        with patch("builtins.print") as p:
            result = organize("/nonexistent/xyz", dry_run=False)
        self.assertEqual(result, 0)


# ── undo ────────────────────────────────────────────────────────────────────

class TestUndo(AutosortTestCase):
    def test_undo_restores(self):
        (Path(self.tmp) / "doc.pdf").write_text("hi")

        # organize() and undo_last() read/write history.json in CWD, so run
        # the whole scenario from inside the temp dir to keep it isolated.
        old_cwd = os.getcwd()
        try:
            os.chdir(self.tmp)
            organize(self.tmp, dry_run=False)
            self.assertTrue((Path(self.tmp) / "Documents").exists())

            undo_last()
        finally:
            os.chdir(old_cwd)

        self.assertTrue((Path(self.tmp) / "doc.pdf").exists())
        # Undo only moves files back; the now-empty category folder stays
        # behind by design (use --clean-empty to remove it).
        self.assertFalse((Path(self.tmp) / "Documents" / "doc.pdf").exists())


# ── clean_empty ─────────────────────────────────────────────────────────────

class TestCleanEmpty(AutosortTestCase):
    def test_removes_empty_nested(self):
        (Path(self.tmp) / "old").mkdir()
        (Path(self.tmp) / "old" / "nested").mkdir()

        clean_empty(self.tmp, dry_run=False)

        self.assertFalse((Path(self.tmp) / "old").exists())
        self.assertFalse((Path(self.tmp) / "old" / "nested").exists())

    def test_skips_nonempty(self):
        (Path(self.tmp) / "keep").mkdir()
        (Path(self.tmp) / "keep" / "f.txt").write_text("x")

        clean_empty(self.tmp, dry_run=False)

        self.assertTrue((Path(self.tmp) / "keep").exists())


# ── load_custom_config ──────────────────────────────────────────────────────

class TestLoadCustomConfig(AutosortTestCase):
    def _write(self, data):
        p = self.tmp + "/c.json"
        with open(p, "w") as f:
            json.dump(data, f)
        return p

    def test_valid_config(self):
        cats, ign, fb = load_custom_config(self._write({
            "categories": {"Docs": [".md"]},
            "ignore": ["x.txt"],
            "fallback": "Junk",
        }))
        self.assertIn("Docs", cats)
        self.assertIn("x.txt", ign)
        self.assertEqual(fb, "Junk")

    def test_extension_normalization(self):
        cats, _, _ = load_custom_config(self._write({"categories": {"A": ["PDF"]}}))
        self.assertIn(".pdf", cats["A"])

    def test_invalid_json(self):
        with open(self.tmp + "/bad.json", "w") as f:
            f.write("not json")
        with self.assertRaises(SystemExit):
            load_custom_config(self.tmp + "/bad.json")

    def test_missing_file(self):
        with self.assertRaises(SystemExit):
            load_custom_config(self.tmp + "/nope.json")

    def test_wrong_types_rejected(self):
        with open(self.tmp + "/bad2.json", "w") as f:
            json.dump({"categories": "oops"}, f)
        with self.assertRaises(SystemExit):
            load_custom_config(self.tmp + "/bad2.json")


# ── recursive ───────────────────────────────────────────────────────────────

class TestRecursive(AutosortTestCase):
    def test_recursive_moves_nested_files(self):
        (Path(self.tmp) / "sub").mkdir()
        (Path(self.tmp) / "sub" / "a.pdf").write_text("x")
        (Path(self.tmp) / "b.png").write_text("y")

        organize(self.tmp, dry_run=False, recursive=True)

        self.assertTrue((Path(self.tmp) / "Documents" / "a.pdf").exists())
        self.assertTrue((Path(self.tmp) / "Images" / "b.png").exists())
        self.assertFalse((Path(self.tmp) / "sub" / "a.pdf").exists())

    def test_recursive_skips_existing_category_dirs(self):
        (Path(self.tmp) / "Documents").mkdir()
        (Path(self.tmp) / "Documents" / "a.pdf").write_text("x")

        organize(self.tmp, dry_run=False, recursive=True)

        self.assertEqual(
            sorted(p.name for p in (Path(self.tmp) / "Documents").iterdir()),
            ["a.pdf"],
        )

    def test_default_mode_ignores_subfolders(self):
        (Path(self.tmp) / "sub").mkdir()
        (Path(self.tmp) / "sub" / "a.pdf").write_text("x")

        organize(self.tmp, dry_run=False)

        self.assertTrue((Path(self.tmp) / "sub" / "a.pdf").exists())


if __name__ == "__main__":
    unittest.main()
