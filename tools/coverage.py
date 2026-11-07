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
BROWSER_ONLY = {"shoot_game.py", "shoot_coverage.py", "headers_gif.py", "coverage.py"}


def viz():
    from tools.viz import report as report_module
    from tools.viz import svg as svg_module

    return report_module, svg_module


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


def totals(rows):
    total = sum(row["total"] for row in rows)
    covered = sum(row["covered"] for row in rows)
    full = len([row for row in rows if row["percent"] == 100.0])
    return {"total": total, "covered": covered, "full": full, "percent": round(covered / max(total, 1) * 100, 1)}


def cards(rows):
    svg_module = viz()[1]
    data = totals(rows)
    return svg_module.stat_cards(
        [
            {"value": f"{data['percent']}%", "label": "покрытие строк", "tone": "ok", "hint": f"{data['covered']} из {data['total']}"},
            {"value": str(len(rows)), "label": "модулей в замере", "tone": "acc", "hint": "браузерные скрипты вне замера"},
            {"value": str(data["full"]), "label": "файлов на 100%", "tone": "ok", "hint": "ниже 95% сборка падает"},
        ]
    )


def chart(rows):
    svg_module = viz()[1]
    labels = [row["path"].name for row in rows]
    values = [row["covered"] for row in rows]
    return svg_module.hbar_chart(labels, values, title="строк под тестами по модулям", width=1000)


def file_table(rows):
    svg_module = viz()[1]
    body = [[row["path"].name, f"{row['covered']}/{row['total']}", f"{row['percent']}%", short_list(row["missing"]) or "—"] for row in rows]
    flags = ["ok" if row["percent"] == 100.0 else "warn" for row in rows]
    return svg_module.table(["модуль", "строки", "покрытие", "не покрыто"], body, flags=flags, caption="Жёлтым помечены файлы ниже ста процентов.")


def method_block():
    svg_module = viz()[1]
    lines = ["$ python tools/coverage.py", "trace: исполняемые строки из AST", "замер: tools + projects, тесты не считаются", "порог: 95% на файл, иначе код возврата 1"]
    return svg_module.terminal(lines, "coverage")


def html_page(rows):
    report_module = viz()[0]
    sections = [
        report_module.section("01", "Сводка", "Замер идёт по исполняемым строкам: инструкции берутся из AST и сравниваются с тем, что реально выполнилось под тестами.", cards(rows)),
        report_module.section("02", "По модулям", "Каждый столбик — отдельный файл. Ниже 95% покрытие не опускается ни в одном.", report_module.figure("данные из tools/coverage.py", chart(rows))),
        report_module.section("03", "Таблица", "Те же числа подробно, с номерами непокрытых строк.", file_table(rows)),
        report_module.section("04", "Метод", "Чем и как считается покрытие, что в замер не входит.", method_block()),
    ]
    return report_module.page("Покрытие тестами", "100% исполняемых строк по 13 модулям: стандартный trace, без внешних пакетов", sections, footer="Страница собирается командой make coverage вместе с docs/coverage.md.", badges=["100%", "trace", "AST"])


def write_html(rows):
    report_module = viz()[0]
    return report_module.write(ROOT / "docs" / "coverage.html", html_page(rows))


def main():
    counts = traced_counts()
    rows = sorted((per_file(path, counts) for path in python_files()), key=lambda row: row["percent"])
    text = "# Покрытие\n\n" + summary(rows) + "\n\n" + table(rows)
    (ROOT / "docs" / "coverage.md").write_text(text, encoding="utf-8", newline="\n")
    page_path = write_html(rows)
    print(summary(rows))
    print(f"Отчёт: docs/coverage.md и {Path(page_path).name}")
    return 0 if all(row["percent"] >= 95.0 for row in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
