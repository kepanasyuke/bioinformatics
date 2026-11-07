"""Тесты отчёта проекта 06: разделы, HTML и точка входа."""

import sys
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT.parents[1]))

import legacy
from tools import testing

DATA = PROJECT / "data"
legacy.write_demo(DATA)
METRICS = legacy.compare_runs(legacy.read_runs(DATA / "runs_before.tsv"), legacy.read_runs(DATA / "runs_after.tsv"))
TARGET = PROJECT / "docs" / "report.html"
SECTIONS = legacy.sections(METRICS)


class ReportTest(unittest.TestCase):
    def test_sections_are_blocks(self):
        self.assertTrue(all(part.startswith("<section") for part in SECTIONS))

    def test_sections_count(self):
        self.assertEqual(len(SECTIONS), 5)

    def test_sections_have_kanban(self):
        self.assertTrue(any("kanban" in part for part in SECTIONS))

    def test_report_mentions_bugs(self):
        text = Path(legacy.write_report(TARGET, METRICS)).read_text(encoding="utf-8")
        self.assertIn("B1", text)

    def test_report_has_speedup(self):
        text = Path(legacy.write_report(TARGET, METRICS)).read_text(encoding="utf-8")
        self.assertIn("−", text)

    def test_main_returns_zero(self):
        self.assertEqual(testing.keep_file(TARGET, lambda: legacy.main([])), 0)


if __name__ == "__main__":
    unittest.main()
