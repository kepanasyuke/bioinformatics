"""Тесты отчёта проекта 04: разделы, HTML и точка входа."""

import sys
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT.parents[1]))

import budget
from tools import testing

JOBS = budget.demo_jobs()
ROWS = budget.summarize(JOBS)
TARGET = PROJECT / "docs" / "report.html"
SECTIONS = budget.sections(JOBS, ROWS)


class ReportTest(unittest.TestCase):
    def test_sections_are_blocks(self):
        self.assertTrue(all(part.startswith("<section") for part in SECTIONS))

    def test_sections_count(self):
        self.assertEqual(len(SECTIONS), 5)

    def test_sections_have_charts(self):
        self.assertTrue(any("<svg" in part for part in SECTIONS))

    def test_report_mentions_core_hours(self):
        text = Path(budget.write_report(TARGET, JOBS, ROWS)).read_text(encoding="utf-8")
        self.assertIn("core-hours", text)

    def test_report_has_savings(self):
        text = Path(budget.write_report(TARGET, JOBS, ROWS)).read_text(encoding="utf-8")
        self.assertIn("%", text)

    def test_main_returns_zero(self):
        self.assertEqual(testing.keep_file(TARGET, lambda: budget.main([])), 0)


if __name__ == "__main__":
    unittest.main()
