"""Тесты отчёта проекта 01: разделы, HTML и точка входа."""

import sys
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT.parents[1]))

import wgs_pipeline as wgs
from tools import testing

COVERAGE = wgs.coverage_bins()
VARIANTS = wgs.demo_variants()
RESULTS = wgs.run_pipeline("S1")
TARGET = PROJECT / "docs" / "report.html"
SECTIONS = wgs.sections(COVERAGE, VARIANTS, RESULTS)


class ReportTest(unittest.TestCase):
    def test_sections_are_blocks(self):
        self.assertTrue(all(part.startswith("<section") for part in SECTIONS))

    def test_sections_count(self):
        self.assertEqual(len(SECTIONS), 6)

    def test_sections_have_svg(self):
        self.assertTrue(any("<svg" in part for part in SECTIONS))

    def test_sections_have_table(self):
        self.assertTrue(any("<table" in part for part in SECTIONS))

    def test_report_contains_title(self):
        text = Path(wgs.write_report(TARGET, COVERAGE, VARIANTS, RESULTS)).read_text(encoding="utf-8")
        self.assertIn("WGS-пайплайн", text)

    def test_report_contains_commands(self):
        text = Path(wgs.write_report(TARGET, COVERAGE, VARIANTS, RESULTS)).read_text(encoding="utf-8")
        self.assertIn("bwa-mem2", text)

    def test_main_returns_zero(self):
        self.assertEqual(testing.keep_file(TARGET, lambda: wgs.main([])), 0)


if __name__ == "__main__":
    unittest.main()
