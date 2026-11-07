"""Тесты отчёта проекта 05: разделы, HTML и точка входа."""

import sys
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT.parents[1]))

import rnaseq
from tools import testing

SAMPLES = PROJECT / "data" / "samples.tsv"
READS = PROJECT / "data" / "reads"
rnaseq.write_demo(SAMPLES, READS)
SAMPLES_DATA = rnaseq.list_samples(SAMPLES)
METRICS = rnaseq.demo_qc(SAMPLES_DATA)
MATRIX = rnaseq.demo_counts()
DE_ROWS = rnaseq.demo_de()
TARGET = PROJECT / "docs" / "report.html"
SECTIONS = rnaseq.sections(SAMPLES_DATA, METRICS, MATRIX, DE_ROWS)


class ReportTest(unittest.TestCase):
    def test_sections_are_blocks(self):
        self.assertTrue(all(part.startswith("<section") for part in SECTIONS))

    def test_sections_count(self):
        self.assertEqual(len(SECTIONS), 9)

    def test_sections_have_pca(self):
        self.assertTrue(any("PC1" in part for part in SECTIONS))

    def test_report_mentions_q30(self):
        text = Path(rnaseq.write_report(TARGET, SAMPLES_DATA, METRICS, MATRIX, DE_ROWS)).read_text(encoding="utf-8")
        self.assertIn("Q30", text)

    def test_report_mentions_excluded_sample(self):
        text = Path(rnaseq.write_report(TARGET, SAMPLES_DATA, METRICS, MATRIX, DE_ROWS)).read_text(encoding="utf-8")
        self.assertIn("S9", text)

    def test_main_returns_zero(self):
        self.assertEqual(testing.keep_file(TARGET, lambda: rnaseq.main([])), 0)


if __name__ == "__main__":
    unittest.main()
