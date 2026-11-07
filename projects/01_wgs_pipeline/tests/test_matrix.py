"""Табличные тесты проекта 01: одна строка таблицы — один тест.

Проверяются команды шагов, сборка заказа и синтетические данные
на разных seed и размерах, а не один и тот же вызов сто раз.
"""

import sys
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT.parents[1]))

import wgs_pipeline as wgs
from tools import testing

SAMPLES = ["S1", "S7", "SYNTH_001", "образец 12"]
CONFIGS = [{"reference": "ref.fa", "outdir": "out", "threads": threads} for threads in (1, 2, 4, 8, 16, 24, 32, 64)]
EXISTING = [str(PROJECT / "data" / "config.json"), str(PROJECT / "README.md")]
MISSING = [f"missing_{index}.fa" for index in range(6)]
SEEDS = list(range(20))
VAR_SEEDS = list(range(12))
DEPTHS = [(list(range(start, start + size)), round(sum(range(start, start + size)) / size, 1)) for start in (1, 5, 10, 20) for size in (2, 3, 4, 5, 6)]
RESULTS = wgs.run_pipeline("S1")
VARIANTS = wgs.demo_variants()


def positions(seed):
    return [item["pos"] for item in wgs.demo_variants(seed=seed)]


ROWS = []
ROWS += [testing.contains(wgs.step_command, step, sample, needle=sample) for step in wgs.STEPS for sample in SAMPLES]
ROWS += [testing.contains(wgs.step_command, step, "S1", needle=step["tool"]) for step in wgs.STEPS]
ROWS += [testing.equal(lambda config=config: wgs.build_job_order("S1", config)["threads"], expected=config["threads"]) for config in CONFIGS]
ROWS += [testing.truthy(lambda config=config: len(wgs.build_job_order("S1", config)["steps"]) == len(wgs.STEPS)) for config in CONFIGS]
ROWS += [testing.equal(wgs.check_reference, EXISTING + MISSING[:size], expected=MISSING[:size]) for size in range(7)]
ROWS += [testing.equal(wgs.check_reference, EXISTING, expected=[]) for _ in range(3)]
ROWS += [testing.equal(lambda seed=seed: len(wgs.coverage_bins(seed=seed)), expected=120) for seed in SEEDS]
ROWS += [testing.truthy(lambda seed=seed: min(wgs.coverage_bins(seed=seed)) > 0) for seed in SEEDS]
ROWS += [testing.truthy(lambda seed=seed: wgs.coverage_bins(seed=seed) != wgs.coverage_bins(seed=seed + 500)) for seed in SEEDS]
ROWS += [testing.equal(lambda seed=seed: len(wgs.demo_variants(seed=seed)), expected=9) for seed in VAR_SEEDS]
ROWS += [testing.truthy(lambda seed=seed: positions(seed) == sorted(positions(seed))) for seed in VAR_SEEDS]
ROWS += [testing.truthy(lambda seed=seed: all(0 < value < 1 for value in positions(seed))) for seed in VAR_SEEDS]
ROWS += [testing.truthy(lambda seed=seed: len({item["label"] for item in wgs.demo_variants(seed=seed)}) == 9) for seed in VAR_SEEDS]
ROWS += [testing.equal(wgs.mean_depth, values, expected=expected) for values, expected in DEPTHS]
ROWS += [testing.equal(lambda step=step: wgs.run_step(step, "S1")["code"], expected=0) for step in wgs.STEPS * 2]
ROWS += [testing.truthy(lambda step=step: wgs.run_step(step, "S1")["dry_run"]) for step in wgs.STEPS]
ROWS += [testing.equal(lambda index=index: len(wgs.step_rows(RESULTS)[index]), expected=5) for index in range(5)]
ROWS += [testing.contains(wgs.variant_track, VARIANTS, needle=item["label"]) for item in VARIANTS]
ROWS += [testing.contains(wgs.variant_track, VARIANTS, needle="<svg") for _ in range(4)]


class MatrixTest(unittest.TestCase):
    """Сгенерированные кейсы: по одному тесту на строку таблицы."""


TOTAL = testing.attach(MatrixTest, "case", ROWS)
