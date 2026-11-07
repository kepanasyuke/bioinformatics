"""Табличные тесты проекта 02: формат ключей, сравнение VCF, порог регрессии."""

import sys
import tempfile
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT.parents[1]))

import regression as reg
from tools import testing

BASE = reg.BASE_VARIANTS
WORKSPACE = Path(tempfile.mkdtemp(prefix="reg-"))
FIXTURE = WORKSPACE / "payload.txt"
FIXTURE.write_text("etalon", encoding="utf-8")
CASES_DIR = WORKSPACE / "cases"
reg.demo_cases(CASES_DIR)
CASES = [reg.case_metrics(case) for case in reg.list_cases(CASES_DIR)]
KEYS = [(chrom, 1000 * index + 17, "A", "G") for chrom in (1, 2, 7, 22, "X") for index in range(1, 9)]
LINES = [(f"chr{chrom}\t{pos}\t.\t{ref}\t{alt}\t50\tPASS\t.", f"chr{chrom}:{pos}:{ref}>{alt}") for chrom, pos, ref, alt in KEYS[:20]]
LINES = LINES + [("chr1\t100\t.\tA\tG\t50\tPASS", "chr1:100:A>G")]
SHORT = ["chr1", "chr1\t100", "", "##fileformat", "#CHROM\tPOS", "chr1\t100\t.", "chr1\t100\t.\tA"]
THRESHOLDS = [0.5, 0.9, 0.95, 1.0]
SCORES = [0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 0.94, 0.95, 0.96, 0.99, 1.0]
PAIRS = [(0, 0), (1, 0), (2, 0), (3, 0), (5, 0), (0, 1), (0, 2), (0, 3), (1, 1), (2, 2)]


def actual_variants(missing, extra):
    extras = [(1, 800000 + index, "C", "T") for index in range(extra)]
    return BASE[: len(BASE) - missing] + extras


def metrics(missing=0, extra=0):
    folder = Path(tempfile.mkdtemp(prefix="pair-"))
    (folder / "etalon.vcf").write_text(reg.vcf_text(BASE), encoding="utf-8")
    (folder / "actual.vcf").write_text(reg.vcf_text(actual_variants(missing, extra)), encoding="utf-8")
    return reg.compare_vcf(folder / "etalon.vcf", folder / "actual.vcf")


ROWS = []
ROWS += [testing.equal(reg.variant_key, chrom, pos, ref, alt, expected=f"chr{chrom}:{pos}:{ref}>{alt}") for chrom, pos, ref, alt in KEYS]
ROWS += [testing.equal(reg.parse_vcf_line, line, expected=expected) for line, expected in LINES]
ROWS += [testing.equal(reg.parse_vcf_line, line, expected="") for line in SHORT]
ROWS += [testing.equal(reg.is_regression, score, threshold, expected=score < threshold) for score in SCORES for threshold in THRESHOLDS]
ROWS += [testing.equal(lambda miss=miss, extra=extra: metrics(miss, extra)["tp"], expected=len(BASE) - miss) for miss, extra in PAIRS]
ROWS += [testing.equal(lambda miss=miss, extra=extra: metrics(miss, extra)["fn"], expected=miss) for miss, extra in PAIRS]
ROWS += [testing.equal(lambda miss=miss, extra=extra: metrics(miss, extra)["fp"], expected=extra) for miss, extra in PAIRS]
ROWS += [testing.truthy(lambda miss=miss, extra=extra: metrics(miss, extra)["f1"] <= 1.0) for miss, extra in PAIRS]
ROWS += [testing.equal(reg.hash_file, FIXTURE, expected=reg.hash_file(FIXTURE)) for _ in range(5)]
ROWS += [testing.equal(lambda path=FIXTURE: len(reg.hash_file(path)), expected=64) for _ in range(5)]
ROWS += [testing.falsy(lambda path=FIXTURE: reg.hash_file(path) == reg.hash_file(Path(__file__))) for _ in range(5)]
ROWS += [testing.equal(lambda size=size: len(reg.vcf_text(BASE[:size]).splitlines()), expected=size + 3) for size in range(0, 13)]
ROWS += [testing.equal(lambda index=index: len(reg.suite_rows(CASES)[index]), expected=8) for index in range(3)]
ROWS += [testing.equal(lambda size=size: len(reg.vcf_text(BASE[:size]).splitlines()), expected=min(size, len(BASE)) + 3) for size in range(13, 18)]
ROWS += [testing.truthy(lambda count=count: reg.pass_rate([{"verdict": "ok"} for _ in range(count)] + [{"verdict": "bad"}]) == round(count / (count + 1), 3)) for count in range(0, 13)]


class MatrixTest(unittest.TestCase):
    """Сгенерированные кейсы: по одному тесту на строку таблицы."""


TOTAL = testing.attach(MatrixTest, "case", ROWS)
