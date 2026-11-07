"""Тесты отчёта проекта 07: разделы, HTML и точка входа."""

import sys
import tempfile
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT.parents[1]))

import freqdb
from tools import testing

ROWS = freqdb.demo_rows()
freqdb.write_demo(freqdb.DATA, ROWS)
CONNECTION = freqdb.open_db(freqdb.DB_PATH)
STATS = freqdb.district_rows(CONNECTION)
ANNOTATED = freqdb.annotate_all(CONNECTION)
TIMINGS = freqdb.measure(CONNECTION, ROWS)
TARGET = PROJECT / "docs" / "report.html"
TEMP = Path(tempfile.mkdtemp(prefix="report-")) / "report.html"
SECTIONS = freqdb.sections(ROWS, STATS, ANNOTATED, TIMINGS, freqdb.SAMPLE_LINES)


class ReportTest(unittest.TestCase):
    def test_sections_are_blocks(self):
        self.assertTrue(all(part.startswith("<section") for part in SECTIONS))

    def test_sections_count(self):
        self.assertEqual(len(SECTIONS), 6)

    def test_sections_have_map(self):
        self.assertTrue(any("СЗФО" in part for part in SECTIONS))

    def test_report_mentions_sqlite(self):
        text = Path(freqdb.write_report(TEMP, ROWS, STATS, ANNOTATED, TIMINGS, freqdb.SAMPLE_LINES)).read_text(encoding="utf-8")
        self.assertIn("SQLite", text)

    def test_report_has_annotation(self):
        text = Path(freqdb.write_report(TEMP, ROWS, STATS, ANNOTATED, TIMINGS, freqdb.SAMPLE_LINES)).read_text(encoding="utf-8")
        self.assertIn("AF=", text)

    def test_main_returns_zero(self):
        self.assertEqual(testing.keep_file(TARGET, lambda: freqdb.main([])), 0)


if __name__ == "__main__":
    unittest.main()
