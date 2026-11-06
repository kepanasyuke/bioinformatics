"""Запускает тесты всех проектов по очереди и печатает итог.

Нужен потому, что папки проектов начинаются с цифры и обычный
unittest discover их как пакеты не видит.
"""

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_files():
    return sorted((ROOT / "projects").glob("*/tests/test_*.py"))


def load_module(path):
    name = "case_" + path.parent.parent.name + "_" + path.stem
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_file(path):
    suite = unittest.defaultTestLoader.loadTestsFromModule(load_module(path))
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    return 0 if result.wasSuccessful() else 1


def main():
    files = test_files()
    codes = [run_file(path) for path in files]
    print(f"\nФайлов с тестами: {len(files)}, провалов: {sum(codes)}")
    return 1 if sum(codes) else 0


if __name__ == "__main__":
    sys.exit(main())
