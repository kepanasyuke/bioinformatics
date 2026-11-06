"""Тесты проекта 04: разбор памяти, процентили, рекомендации лимитов."""

import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

import budget


class MemoryTest(unittest.TestCase):
    def test_gigabytes(self):
        self.assertEqual(budget.parse_mem("4Gn"), 4096)

    def test_megabytes(self):
        self.assertEqual(budget.parse_mem("512M"), 512)

    def test_terabytes(self):
        self.assertEqual(budget.parse_mem("1T"), 1048576)

    def test_default_unit_is_megabyte(self):
        self.assertEqual(budget.parse_mem("2048"), 2048)

    def test_format_switches_to_gb(self):
        self.assertEqual(budget.format_mem(4096), "4.0 ГБ")

    def test_usage_ratio_capped(self):
        self.assertEqual(budget.usage_ratio(9000, 4096), 1.0)

    def test_usage_ratio_zero_request(self):
        self.assertEqual(budget.usage_ratio(100, 0), 0.0)


class SuggestTest(unittest.TestCase):
    def test_percentile_of_simple_list(self):
        self.assertEqual(budget.percentile([1, 2, 3, 4, 5], 0.5), 3.0)

    def test_suggest_mem_covers_max(self):
        values = [1200, 1400, 1500, 1600, 1800]
        self.assertGreaterEqual(budget.suggest_mem(values), max(values))

    def test_suggest_mem_rounded_to_half_gb(self):
        self.assertEqual(budget.suggest_mem([1000] * 5) % 512, 0)


class JobsTest(unittest.TestCase):
    def setUp(self):
        self.jobs = budget.demo_jobs()

    def test_five_steps_covered(self):
        self.assertEqual(sorted({job["step"] for job in self.jobs}), sorted(budget.STEPS))

    def test_peak_not_above_request(self):
        self.assertTrue(all(job["max_rss"] <= job["req_mem"] for job in self.jobs))

    def test_suggest_cpus_at_least_one(self):
        self.assertTrue(all(budget.suggest_cpus(job) >= 1 for job in self.jobs))

    def test_after_is_not_worse_than_before(self):
        rows = budget.summarize(self.jobs)
        self.assertTrue(all(row["after"] <= row["before"] * 1.01 for row in rows))

    def test_savings_percent(self):
        self.assertEqual(budget.savings(100, 53), 47.0)


if __name__ == "__main__":
    unittest.main()
