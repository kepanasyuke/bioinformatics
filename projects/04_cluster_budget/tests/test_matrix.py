"""Табличные тесты проекта 04: разбор памяти, процентили, рекомендации лимитов."""

import math
import sys
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT.parents[1]))

import budget
from tools import testing

MEM_INPUTS = [("4Gn", 4096), ("4g", 4096), ("512M", 512), ("512m", 512), ("1T", 1048576), ("2.5G", 2560), ("2048", 2048), ("0", 0), ("16G", 16384), ("32G", 32768), ("8G", 8192), ("1024M", 1024), ("0.5G", 512), ("64G", 65536), ("128M", 128), ("1M", 1), ("2T", 2097152), ("250M", 250), ("1G", 1024), ("3G", 3072)]
MEM_FORMATS = [(512, "512 МБ"), (1024, "1.0 ГБ"), (2048, "2.0 ГБ"), (1536, "1.5 ГБ"), (4096, "4.0 ГБ"), (32768, "32.0 ГБ"), (256, "256 МБ"), (768, "768 МБ"), (1023, "1023 МБ"), (1025, "1.0 ГБ"), (8192, "8.0 ГБ"), (16384, "16.0 ГБ"), (65536, "64.0 ГБ"), (100, "100 МБ"), (2047, "2.0 ГБ"), (3072, "3.0 ГБ"), (5120, "5.0 ГБ"), (12288, "12.0 ГБ"), (999, "999 МБ"), (16383, "16.0 ГБ")]
USAGE = [(4096, 8192, 0.5), (9000, 4096, 1.0), (100, 0, 0.0), (0, 4096, 0.0), (1024, 1024, 1.0), (500, 4096, 0.122), (2048, 4096, 0.5), (3000, 32768, 0.092), (1, 1, 1.0), (7, 8, 0.875), (8192, 16384, 0.5), (16384, 16384, 1.0), (1000, 1001, 0.999), (250, 500, 0.5), (33, 100, 0.33), (750, 1000, 0.75), (12345, 32768, 0.377), (64, 128, 0.5), (999, 1000, 0.999), (1, 3, 0.333)]
PERCENTILE_LISTS = [[1, 2, 3, 4, 5], [10], [5, 5, 5, 5], list(range(1, 11)), [100, 1, 50, 25], [0, 0, 1], [2, 4, 6, 8, 10, 12], [7, 14, 21], [3, 1, 2], [64, 32, 16, 8, 4, 2, 1]]
MEM_USED = [[1000, 1200, 1300], [4096], [512, 640, 700, 800], [16384, 16000], [100, 200, 300, 400, 500], [32768], [2048, 2048, 2048], [64, 128, 256, 512, 1024], [10000, 12000], [768, 800, 1024, 1100]]
JOBS = [{"total_cpu": 120.0, "elapsed": 60, "req_cpus": 4}, {"total_cpu": 480.0, "elapsed": 60, "req_cpus": 16}, {"total_cpu": 10.0, "elapsed": 100, "req_cpus": 8}, {"total_cpu": 0.0, "elapsed": 30, "req_cpus": 2}, {"total_cpu": 240.0, "elapsed": 120, "req_cpus": 4}, {"total_cpu": 1000.0, "elapsed": 50, "req_cpus": 24}]
CORE = [(8, 60, 8.0), (16, 30, 8.0), (1, 60, 1.0), (4, 15, 1.0), (24, 120, 48.0), (2, 90, 3.0), (12, 45, 9.0), (3, 20, 1.0), (0, 60, 0.0), (10, 6, 1.0)]
SAVINGS = [(100, 53, 47.0), (100, 100, 0.0), (200, 100, 50.0), (0, 10, 0.0), (1664, 1120, 32.7), (10, 5, 50.0), (3, 2, 33.3), (1000, 1, 99.9)]
MEANS = [([1, 2, 3], 2.0), ([0], 0.0), ([10, 20], 15.0), ([1, 1, 1, 1], 1.0), ([5, 10, 15, 20], 12.5), ([100, 0], 50.0), ([2, 3], 2.5), ([7], 7.0)]
JOBSET = budget.demo_jobs()
SUMMARY = budget.summarize(JOBSET)

ROWS = []
ROWS += [testing.equal(budget.parse_mem, text, expected=value) for text, value in MEM_INPUTS]
ROWS += [testing.equal(budget.format_mem, megabytes, expected=text) for megabytes, text in MEM_FORMATS]
ROWS += [testing.equal(budget.usage_ratio, used, requested, expected=share) for used, requested, share in USAGE]
ROWS += [testing.equal(budget.percentile, values, 0.0, expected=min(values)) for values in PERCENTILE_LISTS]
ROWS += [testing.equal(budget.percentile, values, 1.0, expected=max(values)) for values in PERCENTILE_LISTS]
ROWS += [testing.truthy(lambda values=values: min(values) <= budget.percentile(values, 0.5) <= max(values)) for values in PERCENTILE_LISTS]
ROWS += [testing.truthy(lambda values=values: budget.suggest_mem(values) >= max(values)) for values in MEM_USED]
ROWS += [testing.equal(lambda values=values: budget.suggest_mem(values) % 512, expected=0) for values in MEM_USED]
ROWS += [testing.equal(budget.cpu_efficiency, job, expected=round(job["total_cpu"] / max(job["elapsed"], 1) / max(job["req_cpus"], 1), 3)) for job in JOBS]
ROWS += [testing.equal(budget.suggest_cpus, job, expected=max(1, math.ceil(job["total_cpu"] / max(job["elapsed"], 1)))) for job in JOBS]
ROWS += [testing.equal(budget.core_hours, cpus, minutes, expected=hours) for cpus, minutes, hours in CORE]
ROWS += [testing.equal(budget.savings, before, after, expected=percent) for before, after, percent in SAVINGS]
ROWS += [testing.equal(budget.mean, values, expected=average) for values, average in MEANS]
ROWS += [testing.equal(lambda: len(JOBSET), expected=40) for _ in range(3)]
ROWS += [testing.equal(lambda: len(SUMMARY), expected=len(budget.STEPS)) for _ in range(3)]
ROWS += [testing.truthy(lambda job=job: job["max_rss"] <= job["req_mem"]) for job in JOBSET]
ROWS += [testing.equal(lambda index=index: len(budget.worst_rows(JOBSET, index + 1)), expected=index + 1) for index in range(6)]
ROWS += [testing.equal(lambda index=index: len(budget.scatter_points(JOBSET)[index]), expected=3) for index in range(5)]
ROWS += [testing.truthy(lambda row=row: 0.0 <= row["wasted"] <= 1.0) for row in SUMMARY]


class MatrixTest(unittest.TestCase):
    """Сгенерированные кейсы: по одному тесту на строку таблицы."""


TOTAL = testing.attach(MatrixTest, "case", ROWS)
