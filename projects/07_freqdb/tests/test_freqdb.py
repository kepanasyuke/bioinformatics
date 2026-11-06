"""Тесты проекта 07: ключи, база, аннотация, фильтры, гистограмма."""

import sys
import tempfile
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

import freqdb


class KeyTest(unittest.TestCase):
    def test_chr_prefix_removed(self):
        self.assertEqual(freqdb.normalize_key("chr1", 100, "A", "G"), "1:100:A>G")

    def test_same_key_for_same_variant(self):
        self.assertEqual(freqdb.normalize_key(1, 100, "A", "G"), freqdb.normalize_key("chr1", 100, "A", "G"))


class DbTest(unittest.TestCase):
    def setUp(self):
        self.path = Path(tempfile.mkdtemp()) / "freqs.sqlite"
        self.rows = freqdb.demo_rows(count=20)
        freqdb.build_db(self.path, self.rows)
        self.connection = freqdb.open_db(self.path)

    def test_lookup_finds_variant(self):
        key = self.rows[0][0]
        self.assertEqual(freqdb.lookup_variant(self.connection, key)["key"], key)

    def test_lookup_missing_returns_empty(self):
        self.assertEqual(freqdb.lookup_variant(self.connection, "9:1:A>G"), {})

    def test_all_districts_present(self):
        stats = freqdb.district_rows(self.connection)
        self.assertEqual(len(stats), len(freqdb.DISTRICTS))

    def test_af_sorted_reasonable(self):
        stats = freqdb.district_rows(self.connection)
        self.assertTrue(all(0.0 <= row["af"] <= 1.0 for row in stats))


class AnnotationTest(unittest.TestCase):
    def test_af_added_to_info(self):
        record = freqdb.parse_vcf_record("1\t100\t.\tA\tG\t60\tPASS\tDP=30")
        result = freqdb.annotate_record(record, {"af": 0.1234})
        self.assertIn("AF=0.1234", result["info"])
        self.assertIn("DP=30", result["info"])

    def test_missing_frequency_marked(self):
        record = freqdb.parse_vcf_record("1\t100\t.\tA\tG\t60\tPASS\t.")
        self.assertEqual(freqdb.annotate_record(record, {})["info"], "AF=.")

    def test_header_gives_empty_record(self):
        self.assertEqual(freqdb.parse_vcf_record("#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO"), {})


class FilterTest(unittest.TestCase):
    def test_filter_by_population_and_af(self):
        rows = [{"population": "ЦФО", "af": 0.2}, {"population": "ЦФО", "af": 0.01}, {"population": "ДФО", "af": 0.3}]
        self.assertEqual(len(freqdb.filter_by_population(rows, "ЦФО", 0.05)), 1)

    def test_histogram_counts_all(self):
        counts = freqdb.af_histogram([0.01, 0.2, 0.45])
        self.assertEqual(sum(counts), 3)

    def test_histogram_has_bins(self):
        self.assertEqual(len(freqdb.af_histogram([0.1], bins=10)), 10)


if __name__ == "__main__":
    unittest.main()
