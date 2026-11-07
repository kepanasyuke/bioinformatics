"""Тесты инструментов: линтер стиля, фабрики кейсов, раннер."""

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import check_style
import run_tests
from tools import testing

GOOD = "def good(value):\n    return value * 2\n"
TWO_RETURNS = "def bad(value):\n    if value:\n        return 1\n    return 0\n"
CONTINUE = "def bad(rows):\n    total = 0\n    for row in rows:\n        if not row:\n            continue\n        total += 1\n    return total\n"
DEEP = "def bad(rows):\n    for a in rows:\n        for b in rows:\n            for c in rows:\n                if a:\n                    a = 1\n    return 1\n"
LONG = "def bad(value):\n" + "".join(f"    value = value + {index}\n" for index in range(20)) + "    return value\n"
BASH_BAD = "run() {\n    return 1\n    return 2\n}\n"
BASH_CONTINUE = "run() {\n    for a in 1; do\n        continue\n    done\n    return 0\n}\n"


def write_temp(name, text):
    path = Path(tempfile.mkdtemp(prefix="style-")) / name
    path.write_text(text, encoding="utf-8")
    return path


class StyleTest(unittest.TestCase):
    def test_good_code_passes(self):
        self.assertEqual(check_style.check_file(write_temp("good.py", GOOD)), [])

    def test_two_returns_reported(self):
        issues = check_style.check_file(write_temp("bad.py", TWO_RETURNS))
        self.assertTrue(any("выходов 2" in item for item in issues))

    def test_continue_reported(self):
        issues = check_style.check_file(write_temp("cont.py", CONTINUE))
        self.assertTrue(any("continue" in item for item in issues))

    def test_depth_reported(self):
        issues = check_style.check_file(write_temp("deep.py", DEEP))
        self.assertTrue(any("вложенность" in item for item in issues))

    def test_long_body_reported(self):
        issues = check_style.check_file(write_temp("long.py", LONG))
        self.assertTrue(any("тело" in item for item in issues))

    def test_bash_double_return(self):
        issues = check_style.check_bash(write_temp("bad.sh", BASH_BAD))
        self.assertTrue(any("нужен один" in item for item in issues))

    def test_bash_continue(self):
        issues = check_style.check_bash(write_temp("cont.sh", BASH_CONTINUE))
        self.assertTrue(any("continue" in item for item in issues))

    def test_bash_good_function(self):
        self.assertEqual(check_style.check_bash(write_temp("ok.sh", "run() {\n    return 0\n}\n")), [])

    def test_count_returns(self):
        tree = check_style.read_tree(write_temp("c.py", TWO_RETURNS))
        self.assertEqual(check_style.count_returns(check_style.functions_of(tree)[0][1]), 2)

    def test_files_with_suffix(self):
        folder = Path(tempfile.mkdtemp(prefix="scan-"))
        (folder / "a.py").write_text(GOOD, encoding="utf-8")
        self.assertEqual(len(check_style.files_with_suffix(folder, ".py")), 1)

    def test_report_text_clean(self):
        self.assertIn("Нарушений стиля нет", check_style.report_text([], 3, 1))

    def test_report_text_with_issues(self):
        self.assertIn("выходов", check_style.report_text(["выходов 2"], 3, 1))

    def test_main_on_clean_folder(self):
        folder = Path(tempfile.mkdtemp(prefix="main-"))
        (folder / "ok.py").write_text(GOOD, encoding="utf-8")
        self.assertEqual(check_style.main(["check_style", str(folder)]), 0)

    def test_main_on_dirty_folder(self):
        folder = Path(tempfile.mkdtemp(prefix="main2-"))
        (folder / "bad.py").write_text(TWO_RETURNS, encoding="utf-8")
        self.assertEqual(check_style.main(["check_style", str(folder)]), 1)


class TestingHelpersTest(unittest.TestCase):
    def test_equal_passes(self):
        case = testing.equal(len, [1, 2], expected=2)
        case(self)

    def test_equal_fails(self):
        case = testing.equal(len, [1, 2], expected=3)
        self.assertRaises(AssertionError, case, self)

    def test_close(self):
        testing.close(lambda: 0.1 + 0.2, expected=0.3)(self)

    def test_truthy(self):
        testing.truthy(lambda: True)(self)

    def test_falsy(self):
        testing.falsy(lambda: False)(self)

    def test_raises(self):
        testing.raises(ValueError, int, "x")(self)

    def test_contains(self):
        testing.contains(lambda: "abc", needle="b")(self)

    def test_attach_names(self):
        cls = type("C", (), {})
        self.assertEqual(testing.attach(cls, "case", [lambda self: None, lambda self: None]), 2)

    def test_keep_file_restores(self):
        target = Path(tempfile.mkdtemp(prefix="keep-")) / "file.txt"
        target.write_text("original", encoding="utf-8")
        testing.keep_file(target, lambda: target.write_text("changed", encoding="utf-8"))
        self.assertEqual(target.read_text(encoding="utf-8"), "original")

    def test_keep_file_creates_missing(self):
        target = Path(tempfile.mkdtemp(prefix="keep2-")) / "absent.txt"
        testing.keep_file(target, lambda: target.write_text("x", encoding="utf-8"))
        self.assertEqual(target.read_bytes(), b"")


class RunnerTest(unittest.TestCase):
    def test_runner_sees_all_projects(self):
        self.assertGreaterEqual(len(run_tests.test_files()), 21)

    def test_load_module(self):
        module = run_tests.load_module(ROOT / "tools" / "tests" / "test_tools.py")
        self.assertTrue(hasattr(module, "StyleTest"))


if __name__ == "__main__":
    unittest.main()
