"""Тесты отчёта проекта 03: разделы, HTML и точка входа."""

import sys
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT.parents[1]))

import toolchain as chain
from tools import testing

MANIFEST = PROJECT / "data" / "manifest.tsv"
SPECS = chain.read_manifest(MANIFEST)
ORDER = chain.dependency_order(SPECS)
PREFIX = PROJECT / "data" / "prefix"
TARGET = PROJECT / "docs" / "report.html"
SECTIONS = chain.sections(SPECS, ORDER, PREFIX)


class ReportTest(unittest.TestCase):
    def test_sections_are_blocks(self):
        self.assertTrue(all(part.startswith("<section") for part in SECTIONS))

    def test_sections_count(self):
        self.assertEqual(len(SECTIONS), 4)

    def test_sections_have_table(self):
        self.assertTrue(any("<table" in part for part in SECTIONS))

    def test_report_mentions_htslib(self):
        text = Path(chain.write_report(TARGET, SPECS, ORDER, PREFIX)).read_text(encoding="utf-8")
        self.assertIn("htslib", text)

    def test_report_has_configure(self):
        text = Path(chain.write_report(TARGET, SPECS, ORDER, PREFIX)).read_text(encoding="utf-8")
        self.assertIn("./configure", text)

    def test_main_returns_zero(self):
        self.assertEqual(testing.keep_file(TARGET, lambda: chain.main([])), 0)


if __name__ == "__main__":
    unittest.main()
