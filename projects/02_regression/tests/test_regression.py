"""Тесты проекта 02: ключи вариантов, сравнение VCF, порог регрессии."""

import sys
import tempfile
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

import regression as reg


class CompareTest(unittest.TestCase):
    def make_pair(self, etalon_rows, actual_rows):
        folder = tempfile.mkdtemp()
        etalon = Path(folder) / "etalon.vcf"
        actual = Path(folder) / "actual.vcf"
        etalon.write_text(reg.vcf_text(etalon_rows), encoding="utf-8")
        actual.write_text(reg.vcf_text(actual_rows), encoding="utf-8")
        return etalon, actual

    def test_key_format(self):
        self.assertEqual(reg.variant_key(1, 100, "A", "G"), "chr1:100:A>G")

    def test_header_skipped(self):
        etalon, _ = self.make_pair(reg.BASE_VARIANTS, reg.BASE_VARIANTS)
        self.assertEqual(len(reg.read_vcf(etalon)), len(reg.BASE_VARIANTS))

    def test_ideal_case_f1_is_one(self):
        etalon, actual = self.make_pair(reg.BASE_VARIANTS, reg.BASE_VARIANTS)
        self.assertEqual(reg.compare_vcf(etalon, actual)["f1"], 1.0)

    def test_missing_variant_lowers_recall(self):
        etalon, actual = self.make_pair(reg.BASE_VARIANTS, reg.BASE_VARIANTS[:-2])
        metrics = reg.compare_vcf(etalon, actual)
        self.assertEqual(metrics["fn"], 2)
        self.assertLess(metrics["recall"], 1.0)

    def test_extra_variant_lowers_precision(self):
        etalon, actual = self.make_pair(reg.BASE_VARIANTS, reg.BASE_VARIANTS + reg.EXTRA_VARIANT)
        metrics = reg.compare_vcf(etalon, actual)
        self.assertEqual(metrics["fp"], 1)
        self.assertLess(metrics["precision"], 1.0)

    def test_threshold_boundary(self):
        self.assertFalse(reg.is_regression(0.95))
        self.assertTrue(reg.is_regression(0.94))

    def test_hash_is_stable(self):
        etalon, actual = self.make_pair(reg.BASE_VARIANTS, reg.BASE_VARIANTS)
        self.assertEqual(reg.hash_file(actual), reg.hash_file(etalon))


if __name__ == "__main__":
    unittest.main()
