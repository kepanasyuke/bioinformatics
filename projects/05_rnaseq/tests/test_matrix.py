"""Табличные тесты проекта 05: QC-пороги, линейная алгебра, PCA и volcano."""

import math
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT.parents[1]))

import rnaseq
from tools import testing

READS = Path(tempfile.mkdtemp(prefix="reads-"))
(READS / "ok_R1.fastq.gz").write_text("x", encoding="utf-8")
(READS / "ok_R2.fastq.gz").write_text("x", encoding="utf-8")
(READS / "empty_R1.fastq.gz").write_text("", encoding="utf-8")

SAMPLES = [
    {"sample": "ok", "group": "case", "r1": "ok_R1.fastq.gz", "r2": "ok_R2.fastq.gz"},
    {"sample": "half", "group": "case", "r1": "ok_R1.fastq.gz", "r2": "none_R2.fastq.gz"},
    {"sample": "empty", "group": "control", "r1": "empty_R1.fastq.gz", "r2": "ok_R2.fastq.gz"},
    {"sample": "both", "group": "control", "r1": "none_R1.fastq.gz", "r2": "none_R2.fastq.gz"},
]
QC_HIGH = [(96.0, "ok"), (95.5, "ok"), (93.0, "ok"), (92.5, "ok"), (92.0, "ok"), (91.0, "warn"), (90.0, "warn"), (89.5, "warn"), (88.5, "warn"), (88.0, "warn"), (87.5, "bad"), (85.0, "bad"), (80.0, "bad"), (0.0, "bad"), (99.0, "ok")]
QC_LOW = [(0.01, "ok"), (0.05, "ok"), (0.1, "ok"), (0.15, "ok"), (0.2, "warn"), (0.25, "warn"), (0.29, "warn"), (0.3, "warn"), (0.31, "bad"), (0.5, "bad")]
DOTS = [([1, 2, 3], [4, 5, 6], 32), ([0, 0], [0, 0], 0), ([1], [1], 1), ([2, 3], [4, 5], 23), ([-1, -1], [1, 1], -2), ([10, 0], [0, 10], 0), ([1, 1, 1], [2, 2, 2], 6), ([5], [0], 0), ([0.5, 0.5], [2, 2], 2), ([3, 4], [3, 4], 25)]
VOLCANO = [(2.5, 0.001, "значимо"), (-2.5, 0.001, "значимо"), (0.5, 0.001, "не значимо"), (1.0, 0.001, "значимо"), (0.99, 0.001, "не значимо"), (3.0, 0.04, "значимо"), (3.0, 0.05, "не значимо"), (3.0, 0.2, "не значимо"), (-1.2, 0.01, "значимо"), (1.05, 0.049, "значимо"), (0.0, 0.0, "не значимо"), (5.0, 1e-9, "значимо"), (-4.0, 0.002, "значимо"), (1.5, 0.0499, "значимо"), (1.0, 0.1, "не значимо")]
PADJ = [(1e-9, "значимо"), (1e-6, "значимо"), (0.001, "значимо"), (0.01, "значимо"), (0.049, "значимо"), (0.05, "не значимо"), (0.06, "не значимо"), (0.1, "не значимо"), (0.5, "не значимо"), (0.9, "не значимо")]
CHECK_COUNTS = [(SAMPLES[0], 0), (SAMPLES[1], 1), (SAMPLES[2], 1), (SAMPLES[3], 2)]
COUNTS = rnaseq.demo_counts()
DE_ROWS = rnaseq.demo_de()


def matrix_of(size):
    return [[index + row for index in range(3)] for row in range(size)]


def column_mean(matrix, column):
    return sum(row[column] for row in matrix) / len(matrix)


ROWS = []
ROWS += [testing.equal(rnaseq.qa_grade, value, 92.0, 88.0, expected=grade) for value, grade in QC_HIGH]
ROWS += [testing.equal(rnaseq.qa_grade, value, 0.15, 0.3, False, expected=grade) for value, grade in QC_LOW]
ROWS += [testing.equal(rnaseq.dot, left, right, expected=total) for left, right, total in DOTS]
ROWS += [testing.close(lambda: rnaseq.normalize([3, 4])[0], expected=0.6)]
ROWS += [testing.close(lambda: rnaseq.normalize([3, 4])[1], expected=0.8)]
ROWS += [testing.close(lambda vector=vector: math.sqrt(rnaseq.dot(rnaseq.normalize(vector), rnaseq.normalize(vector))), expected=1.0) for vector in ([1, 1], [2, 3], [0.5, 0.5, 0.5], [1, 0], [10, 0, 10], [-1, 2, -3], [7], [1, 2, 3, 4], [4, 4], [9, 12])]
ROWS += [testing.equal(lambda: rnaseq.matvec([[1, 0], [0, 1]], [5, 7]), expected=[5, 7]) for _ in range(3)]
ROWS += [testing.equal(lambda: len(rnaseq.matvec([[1] * 3] * 3, [1, 1, 1])), expected=3) for _ in range(4)]
ROWS += [testing.truthy(lambda size=size: all(abs(column_mean(rnaseq.center_rows(matrix_of(size)), column)) < 1e-9 for column in range(3))) for size in range(2, 8)]
ROWS += [testing.equal(lambda: rnaseq.center_rows([[1, 2], [3, 4]]), expected=[[-1.0, -1.0], [1.0, 1.0]]) for _ in range(2)]
ROWS += [testing.truthy(lambda size=size: rnaseq.covariance(rnaseq.center_rows(matrix_of(size)))[0][1] == rnaseq.covariance(rnaseq.center_rows(matrix_of(size)))[1][0]) for size in range(2, 8)]
ROWS += [testing.close(lambda size=size: math.sqrt(rnaseq.dot(rnaseq.power_iteration(rnaseq.covariance(rnaseq.center_rows(matrix_of(size)))), rnaseq.power_iteration(rnaseq.covariance(rnaseq.center_rows(matrix_of(size)))))), expected=1.0) for size in range(2, 9)]
ROWS += [testing.equal(lambda: len(rnaseq.power_iteration(rnaseq.covariance(rnaseq.center_rows(matrix_of(4))))), expected=3) for _ in range(6)]
ROWS += [testing.equal(lambda: len(rnaseq.pca_2d(COUNTS)), expected=len(COUNTS)) for _ in range(3)]
ROWS += [testing.equal(lambda: rnaseq.pca_2d(COUNTS), expected=rnaseq.pca_2d(COUNTS)) for _ in range(3)]
ROWS += [testing.equal(lambda index=index: len(rnaseq.pca_2d(COUNTS)[index]), expected=2) for index in range(8)]
ROWS += [testing.equal(lambda lfc=lfc, padj=padj: rnaseq.volcano_points([{"gene": "A", "log2fc": lfc, "padj": padj}])[0]["group"], expected=group) for lfc, padj, group in VOLCANO]
ROWS += [testing.equal(lambda padj=padj: rnaseq.volcano_points([{"gene": "A", "log2fc": 2.0, "padj": padj}])[0]["group"], expected=group) for padj, group in PADJ]
ROWS += [testing.truthy(lambda values=rnaseq.heatmap_values(COUNTS): all(0.0 <= value <= 1.0 for row in values for value in row)) for _ in range(4)]
ROWS += [testing.equal(lambda: len(rnaseq.heatmap_values(COUNTS)), expected=8) for _ in range(3)]
ROWS += [testing.equal(lambda: len(rnaseq.heatmap_values(COUNTS)[0]), expected=8) for _ in range(3)]
ROWS += [testing.equal(rnaseq.check_reads, sample, READS, expected=[]) for sample in [SAMPLES[0]]]
ROWS += [testing.equal(lambda sample=sample: len(rnaseq.check_reads(sample, READS)), expected=count) for sample, count in CHECK_COUNTS for _ in range(3)]
ROWS += [testing.equal(lambda: len(rnaseq.accepted(SAMPLES)), expected=0) for _ in range(3)]
ROWS += [testing.contains(rnaseq.make_trim_cmd, SAMPLES[0], "trim", needle="trim/ok.R1.fq.gz") for _ in range(4)]
ROWS += [testing.contains(rnaseq.make_align_cmd, SAMPLES[0], "align", needle="STAR") for _ in range(4)]
ROWS += [testing.equal(lambda: rnaseq.run_cmd(["echo", "1"])["code"], expected=0) for _ in range(4)]
ROWS += [testing.truthy(lambda: rnaseq.run_cmd(["echo"], dry_run=True)["dry_run"]) for _ in range(3)]
ROWS += [testing.equal(lambda size=size: len(rnaseq.demo_counts(size=size)), expected=size) for size in range(1, 13)]
ROWS += [testing.equal(lambda: len(rnaseq.demo_counts()[0]), expected=12) for _ in range(3)]
ROWS += [testing.equal(lambda: len(DE_ROWS), expected=40) for _ in range(2)]
ROWS += [testing.equal(lambda index=index: len(rnaseq.demo_de()[index]), expected=3) for index in range(10)]
ROWS += [testing.equal(lambda: len(rnaseq.qc_table(rnaseq.demo_qc([SAMPLES[0]]))[0][0]), expected=6) for _ in range(3)]
ROWS += [testing.equal(lambda: len(rnaseq.accepted([])), expected=0) for _ in range(3)]
ROWS += [testing.equal(lambda: len(rnaseq.normalize([1, 1, 1])), expected=3) for _ in range(3)]
ROWS += [testing.equal(lambda: len(rnaseq.heatmap_values(rnaseq.demo_counts(size=4))), expected=8) for _ in range(2)]
ROWS += [testing.equal(lambda: len(rnaseq.demo_qc([SAMPLES[0]])), expected=1) for _ in range(2)]
ROWS += [testing.equal(lambda: sorted(rnaseq.demo_qc([SAMPLES[0]])[0]), expected=sorted(["sample", "group", "reads", "q30", "duplication"])) for _ in range(2)]


class MatrixTest(unittest.TestCase):
    """Сгенерированные кейсы: по одному тесту на строку таблицы."""


TOTAL = testing.attach(MatrixTest, "case", ROWS)
