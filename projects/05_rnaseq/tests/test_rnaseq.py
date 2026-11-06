"""Тесты проекта 05: проверка чтений, PCA, пороги QC, volcano."""

import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

import rnaseq


class SampleTest(unittest.TestCase):
    def test_missing_reads_flagged(self):
        problems = rnaseq.check_reads({"sample": "X", "r1": "nope_R1.fastq.gz", "r2": "nope_R2.fastq.gz"})
        self.assertEqual(len(problems), 2)

    def test_trim_command_has_sample(self):
        command = rnaseq.make_trim_cmd({"sample": "S1", "r1": "a.fq.gz", "r2": "b.fq.gz"})
        self.assertIn("trim/S1.R1.fq.gz", command)

    def test_align_command_uses_star(self):
        command = rnaseq.make_align_cmd({"sample": "S1", "r1": "a", "r2": "b"})
        self.assertEqual(command[0], "STAR")


class QaTest(unittest.TestCase):
    def test_high_q30_is_ok(self):
        self.assertEqual(rnaseq.qa_grade(95.0, 92.0, 88.0), "ok")

    def test_middle_q30_is_warn(self):
        self.assertEqual(rnaseq.qa_grade(90.0, 92.0, 88.0), "warn")

    def test_low_q30_is_bad(self):
        self.assertEqual(rnaseq.qa_grade(80.0, 92.0, 88.0), "bad")

    def test_duplication_lower_is_better(self):
        self.assertEqual(rnaseq.qa_grade(0.1, 0.15, 0.3, higher_is_better=False), "ok")


class PcaTest(unittest.TestCase):
    def test_two_coordinates_per_sample(self):
        points = rnaseq.pca_2d(rnaseq.demo_counts())
        self.assertEqual(len(points), 8)

    def test_first_axis_splits_groups(self):
        points = rnaseq.pca_2d(rnaseq.demo_counts())
        control = sum(point["x"] for point in points[:4]) / 4
        case = sum(point["x"] for point in points[4:]) / 4
        self.assertGreater(abs(control - case), 1.0)

    def test_pca_is_deterministic(self):
        self.assertEqual(rnaseq.pca_2d(rnaseq.demo_counts()), rnaseq.pca_2d(rnaseq.demo_counts()))


class VolcanoTest(unittest.TestCase):
    def test_significant_gene_marked(self):
        points = rnaseq.volcano_points([{"gene": "A", "log2fc": 2.5, "padj": 0.001}])
        self.assertEqual(points[0]["group"], "значимо")

    def test_weak_gene_not_marked(self):
        points = rnaseq.volcano_points([{"gene": "B", "log2fc": 0.2, "padj": 0.5}])
        self.assertEqual(points[0]["group"], "не значимо")

    def test_heatmap_rows_normalised(self):
        rows = rnaseq.heatmap_values(rnaseq.demo_counts())
        self.assertTrue(all(0.0 <= value <= 1.0 for row in rows for value in row))


if __name__ == "__main__":
    unittest.main()
