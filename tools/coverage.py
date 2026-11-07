"""Считает покрытие строк тестами стандартным модулем trace, без внешних пакетов.

Запуск: python tools/coverage.py
Пишет docs/coverage.md и печатает сводку по файлам.
"""

import ast
import contextlib
import io
import sys
import trace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import run_tests

TARGETS = [ROOT / "tools", ROOT / "projects"]
BROWSER_ONLY = {"shoot_game.py", "headers_gif.py", "coverage.py"}


def python_files():
    found = [path for folder in TARGETS for path in folder.rglob("*.py")]
    return [path for path in found if path.name not in BROWSER_ONLY and not path.name.startswith("test_") and path.name != "__init__.py" and "__pycache__" not in path.parts]


def guard_lines(tree):
    guards = [node for node in ast.walk(tree) if isinstance(node, ast.If) and "__name__" in ast.dump(node.test)]
    return sorted({item.lineno for guard in guards for item in guard.body})


def statement_lines(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    guarded = set(guard_lines(tree))
    return sorted({node.lineno for node in ast.walk(tree) if isinstance(node, ast.stmt) and node.lineno not in guarded})


def run_suite():
    with contextlib.redirect_stdout(io.StringIO()):
        return run_tests.main()


def traced_counts():
    tracer = trace.Trace(count=1, trace=0, ignoredirs=[sys.prefix, sys.exec_prefix])
    tracer.runfunc(run_suite)
    return tracer.results().counts


def per_file(path, counts):
    hits = {line for (name, line), hits_count in counts.items() if hits_count and Path(name).resolve() == path.resolve()}
    lines = statement_lines(path)
    covered = len([line for line in lines if line in hits])
    missing = [line for line in lines if line not in hits]
    return {"path": path, "total": len(lines), "covered": covered, "percent": round(covered / max(len(lines), 1) * 100, 1), "missing": missing}


def short_list(values, limit=8):
    text = ", ".join(str(value) for value in values[:limit])
    return text + (" …" if len(values) > limit else "")


def table(rows):
    head = "| Файл | Строк покрыто | Покрытие | Не покрыто |\n|---|---|---|---|\n"
    body = "".join(f"| `{row['path'].relative_to(ROOT).as_posix()}` | {row['covered']}/{row['total']} | {row['percent']}% | {short_list(row['missing']) or '—'} |\n" for row in rows)
    return head + body


def summary(rows):
    total = sum(row["total"] for row in rows)
    covered = sum(row["covered"] for row in rows)
    full = len([row for row in rows if row["percent"] == 100.0])
    return f"Файлов: {len(rows)}, полностью покрыто: {full}, строк: {covered}/{total} = {round(covered / max(total, 1) * 100, 1)}%"


def main():
    counts = traced_counts()
    rows = sorted((per_file(path, counts) for path in python_files()), key=lambda row: row["percent"])
    text = "# Покрытие\n\n" + summary(rows) + "\n\n" + table(rows)
    (ROOT / "docs" / "coverage.md").write_text(text, encoding="utf-8", newline="\n")
    print(summary(rows))
    print(f"Отчёт: docs/coverage.md")
    return 0 if all(row["percent"] >= 95.0 for row in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
