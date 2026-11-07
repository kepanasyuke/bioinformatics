"""Табличные тесты проекта 06: разбор VCF, подсчёт вариантов, сравнение прогонов."""

import sys
import tempfile
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT.parents[1]))

import legacy
from tools import testing

WORKSPACE = Path(tempfile.mkdtemp(prefix="legacy-"))
CHROMS = ["chr1", "chr2", "chr3", "chr7", "chr22", "chrX"]
POSITIONS = [1, 100, 5000, 10000, 250000, 999999, 123456789, 2000000]
VALID_LINES = [(f"{chrom}\t{position}\t.\tA\tG\t50\tPASS\tDP=30", (chrom, position)) for chrom in CHROMS for position in POSITIONS]
INVALID_LINES = ["", "chr1", "chr1\t100", "##fileformat=VCFv4.2", "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO", "chr1\t100\t.\tA\tG\t50\tPASS"]
AVERAGES = [([10, 20], 15.0), ([1, 2, 3], 2.0), ([0], 0.0), ([5, 10, 15, 20], 12.5), ([100, 200, 300], 200.0), ([7], 7.0), ([2, 3], 2.5), ([1, 1, 1, 1], 1.0), ([0, 0], 0.0), ([10, 0], 5.0), ([1, 2], 1.5), ([3, 4, 5], 4.0)]
RUN_PAIRS = [([400, 200], [200, 100], 50.0), ([100], [100], 0.0), ([300], [150], 50.0), ([50, 70], [25, 35], 50.0), ([0], [0], 0.0), ([1000, 1000], [10, 10], 99.0)]


def vcf_with(count):
    lines = ["##fileformat=VCFv4.2", "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO"]
    body = [f"chr1\t{index + 1}\t.\tA\tG\t50\tPASS\tDP=30" for index in range(count)]
    path = WORKSPACE / f"file-{count}.vcf"
    path.write_text("\n".join(lines + body) + "\n", encoding="utf-8")
    return path


def runs(minutes, failed=0):
    return [{"minutes": value, "failed": failed} for value in minutes]


ROWS = []
ROWS += [testing.equal(lambda line=line: (legacy.parse_vcf_line(line)["chrom"], legacy.parse_vcf_line(line)["pos"]), expected=expected) for line, expected in VALID_LINES]
ROWS += [testing.equal(lambda line=line: legacy.parse_vcf_line(line)["filter"], expected="PASS") for line, expected in VALID_LINES]
ROWS += [testing.equal(lambda line=line: legacy.parse_vcf_line(line)["ref"], expected="A") for line, expected in VALID_LINES]
ROWS += [testing.equal(legacy.parse_vcf_line, line, expected={}) for line in INVALID_LINES]
ROWS += [testing.equal(lambda count=count: legacy.count_variants(vcf_with(count)), expected=count) for count in range(1, 21)]
ROWS += [testing.equal(legacy.average, values, expected=expected) for values, expected in AVERAGES]
ROWS += [testing.equal(lambda before=before, after=after: legacy.compare_runs(runs(before), runs(after))["speedup"], expected=speedup) for before, after, speedup in RUN_PAIRS]
ROWS += [testing.equal(lambda before=before: legacy.compare_runs(runs(before, 3), runs(before))["failed_before"], expected=3 * len(before)) for before, after, speedup in RUN_PAIRS]
ROWS += [testing.equal(lambda before=before: legacy.compare_runs(runs(before), runs(before))["failed_after"], expected=0) for before, after, speedup in RUN_PAIRS]
ROWS += [testing.contains(legacy.issue_board, needle=title) for title in ("Открыто", "В работе", "Закрыто")]
ROWS += [testing.truthy(lambda: "kcard" in legacy.issue_board()) for _ in range(3)]
ROWS += [testing.truthy(lambda number=number: any(f'class="num">{number}' in part for part in legacy.sections(legacy.compare_runs(runs([100]), runs([50]))))) for number in ("01", "02", "03", "04", "05")]
ROWS += [testing.truthy(lambda: legacy.write_report(WORKSPACE / "report.html", legacy.compare_runs(runs([100]), runs([50])))) for _ in range(3)]
ROWS += [testing.equal(lambda: len(legacy.read_runs(Path(legacy.write_demo(WORKSPACE / "demo")) / "runs_before.tsv")), expected=5) for _ in range(3)]
ROWS += [testing.equal(lambda: legacy.count_variants(Path(legacy.write_demo(WORKSPACE / "demo2")) / "sample.vcf"), expected=14) for _ in range(3)]


class MatrixTest(unittest.TestCase):
    """Сгенерированные кейсы: по одному тесту на строку таблицы."""


TOTAL = testing.attach(MatrixTest, "case", ROWS)
