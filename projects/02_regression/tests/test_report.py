"""Тесты отчёта проекта 02: разделы, HTML и точка входа."""

import sys
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT.parents[1]))

import regression as reg
from tools import testing

CASES_DIR = PROJECT / "data" / "cases"
HISTORY_PATH = PROJECT / "data" / "history.tsv"
reg.demo_cases(CASES_DIR)
CASES = [reg.case_metrics(case) for case in reg.list_cases(CASES_DIR)]
HISTORY = reg.history_rows(reg.write_history(HISTORY_PATH))
TARGET = PROJECT / "docs" / "report.html"
SECTIONS = reg.sections(CASES, HISTORY)


class ReportTest(unittest.TestCase):
    def test_sections_are_blocks(self):
        self.assertTrue(all(part.startswith("<section") for part in SECTIONS))

    def test_sections_count(self):
        self.assertEqual(len(SECTIONS), 5)

    def test_sections_have_red_row(self):
        self.assertTrue(any('class="bad"' in part for part in SECTIONS))

    def test_report_mentions_regression(self):
        text = Path(reg.write_report(TARGET, CASES, HISTORY)).read_text(encoding="utf-8")
        self.assertIn("case_b_regression", text)

    def test_report_has_threshold(self):
        text = Path(reg.write_report(TARGET, CASES, HISTORY)).read_text(encoding="utf-8")
        self.assertIn("0.95", text)

    def test_main_returns_zero(self):
        self.assertEqual(testing.keep_file(TARGET, lambda: reg.main([])), 0)


if __name__ == "__main__":
    unittest.main()
