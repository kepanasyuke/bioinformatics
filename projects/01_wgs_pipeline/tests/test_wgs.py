"""Тесты проекта 01: план шагов, проверка референса, синтетические данные."""

import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

import wgs_pipeline as wgs


class StepsTest(unittest.TestCase):
    def test_command_contains_sample(self):
        command = wgs.step_command(wgs.STEPS[0], "S7")
        self.assertIn("S7", command)

    def test_job_order_lists_all_steps(self):
        order = wgs.build_job_order("S1", {"reference": "r.fa", "outdir": "o", "threads": 8})
        self.assertEqual(len(order["steps"]), len(wgs.STEPS))

    def test_run_step_is_dry_by_default(self):
        result = wgs.run_step(wgs.STEPS[2], "S1")
        self.assertTrue(result["dry_run"])
        self.assertEqual(result["code"], 0)

    def test_missing_reference_reported(self):
        missing = wgs.check_reference(["no_such_file.fa"])
        self.assertEqual(len(missing), 1)

    def test_cov_bins_repeatable(self):
        self.assertEqual(wgs.coverage_bins(), wgs.coverage_bins())

    def test_variants_sorted(self):
        positions = [item["pos"] for item in wgs.demo_variants()]
        self.assertEqual(positions, sorted(positions))

    def test_mean_depth(self):
        self.assertEqual(wgs.mean_depth([10, 20, 30]), 20.0)


if __name__ == "__main__":
    unittest.main()
