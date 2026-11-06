"""Тесты проекта 06: разбор строк VCF, подсчёт вариантов, сравнение прогонов."""

import sys
import tempfile
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

import legacy


class ParseTest(unittest.TestCase):
    def test_full_line_parsed(self):
        record = legacy.parse_vcf_line("chr1\t100\t.\tA\tG\t50\tPASS\tDP=30")
        self.assertEqual(record["pos"], 100)
        self.assertEqual(record["ref"], "A")

    def test_short_line_gives_empty_record(self):
        self.assertEqual(legacy.parse_vcf_line("chr1\t100"), {})

    def test_header_gives_empty_record(self):
        self.assertEqual(legacy.parse_vcf_line("##fileformat=VCFv4.2"), {})

    def test_count_skips_headers(self):
        folder = Path(tempfile.mkdtemp()) / "sample.vcf"
        rows = ["##fileformat=VCFv4.2", "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO", "chr1\t1\t.\tA\tG\t50\tPASS\t."]
        folder.write_text("\n".join(rows) + "\n", encoding="utf-8")
        self.assertEqual(legacy.count_variants(folder), 1)


class RunsTest(unittest.TestCase):
    def test_average(self):
        self.assertEqual(legacy.average([10, 20, 30]), 20.0)

    def test_speedup_positive(self):
        before = [{"minutes": 400, "failed": 10}]
        after = [{"minutes": 200, "failed": 0}]
        self.assertEqual(legacy.compare_runs(before, after)["speedup"], 50.0)

    def test_failures_summed(self):
        before = [{"minutes": 100, "failed": 3}, {"minutes": 100, "failed": 4}]
        after = [{"minutes": 50, "failed": 0}, {"minutes": 50, "failed": 0}]
        self.assertEqual(legacy.compare_runs(before, after)["failed_before"], 7)

    def test_demo_files_written(self):
        folder = legacy.write_demo(Path(tempfile.mkdtemp()))
        self.assertTrue((Path(folder) / "runs_before.tsv").exists())
        self.assertEqual(legacy.count_variants(Path(folder) / "sample.vcf"), 14)


if __name__ == "__main__":
    unittest.main()
