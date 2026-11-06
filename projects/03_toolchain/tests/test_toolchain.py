"""Тесты проекта 03: манифест, контрольные суммы, порядок сборки."""

import sys
import tempfile
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

import toolchain as chain

MANIFEST = Path(__file__).resolve().parents[1] / "data" / "manifest.tsv"


class ManifestTest(unittest.TestCase):
    def setUp(self):
        self.specs = chain.read_manifest(MANIFEST)

    def test_all_fields_present(self):
        self.assertTrue(all(spec["sha256"] for spec in self.specs))

    def test_deps_parsed(self):
        samtools = next(spec for spec in self.specs if spec["name"] == "samtools")
        self.assertEqual(samtools["deps"], ["htslib"])

    def test_empty_deps_become_list(self):
        htslib = next(spec for spec in self.specs if spec["name"] == "htslib")
        self.assertEqual(htslib["deps"], [])


class OrderTest(unittest.TestCase):
    def setUp(self):
        self.specs = chain.read_manifest(MANIFEST)

    def test_htslib_before_samtools(self):
        order = chain.dependency_order(self.specs)
        self.assertLess(order.index("htslib"), order.index("samtools"))

    def test_picard_before_gatk(self):
        order = chain.dependency_order(self.specs)
        self.assertLess(order.index("picard"), order.index("gatk"))

    def test_all_tools_present(self):
        order = chain.dependency_order(self.specs)
        self.assertEqual(sorted(order), sorted(spec["name"] for spec in self.specs))

    def test_cycle_does_not_hang(self):
        specs = [{"name": "a", "version": "1", "kind": "jar", "sha256": "", "deps": ["b"]}, {"name": "b", "version": "1", "kind": "jar", "sha256": "", "deps": ["a"]}]
        self.assertEqual(chain.dependency_order(specs), [])


class SumTest(unittest.TestCase):
    def test_missing_file_fails(self):
        self.assertFalse(chain.check_sum("no_such_file.tar.gz", "abc"))

    def test_matching_sum_passes(self):
        folder = Path(tempfile.mkdtemp()) / "payload.txt"
        folder.write_text("htslib", encoding="utf-8")
        expected = "076ef90f531be50d654a3bdc8dc77411fed1b52a3c2458ae5296fdbf031d72c9"
        self.assertTrue(chain.check_sum(folder, expected))


class PlanTest(unittest.TestCase):
    def test_autotools_has_configure(self):
        spec = {"name": "htslib", "version": "1.20", "kind": "autotools"}
        self.assertIn("./configure --prefix=/opt/bio", chain.plan_actions(spec, "/opt/bio"))

    def test_unknown_kind_is_empty(self):
        spec = {"name": "x", "version": "1", "kind": "magic"}
        self.assertEqual(chain.plan_actions(spec, "/opt/bio"), [])


if __name__ == "__main__":
    unittest.main()
