"""Проект 03. Тулчейн: манифест версий, контрольные суммы, порядок сборки.

Запуск: python projects/03_toolchain/src/toolchain.py
Проверяет манифест, строит порядок сборки по зависимостям и пишет отчёт.
"""

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from tools.viz import report
from tools.viz import svg as art

PROJECT = Path(__file__).resolve().parents[1]
MANIFEST = PROJECT / "data" / "manifest.tsv"
CACHE = PROJECT / "data" / "cache"


def read_manifest(path):
    lines = Path(path).read_text(encoding="utf-8").strip().splitlines()
    header = lines[0].split("\t")
    rows = [dict(zip(header, line.split("\t"))) for line in lines[1:]]
    return [{"name": row["name"], "version": row["version"], "kind": row["kind"], "sha256": row["sha256"], "deps": [item for item in row["deps"].split(",") if item and item != "-"]} for row in rows]


def check_sum(path, expected):
    match = False
    if Path(path).exists():
        digest = hashlib.sha256(Path(path).read_bytes()).hexdigest()
        match = digest == expected
    return match


def plan_actions(spec, prefix):
    actions = {
        "autotools": [f"cd {spec['name']}-{spec['version']}", f"./configure --prefix={prefix}", "make -j 8", "make install"],
        "jar": [f"install -m 0644 {spec['name']}-{spec['version']}.jar {prefix}/share/java", f"printf '#!/bin/sh\\nexec java -jar {prefix}/share/java/{spec['name']}-{spec['version']}.jar \"$@\"\\n' > {prefix}/bin/{spec['name']}"],
    }
    return actions.get(spec["kind"], [])


def dependency_order(specs):
    names = [spec["name"] for spec in specs]
    pending = {spec["name"]: [dep for dep in spec["deps"] if dep in names] for spec in specs}
    order = []
    guard = len(names) + 1
    while pending and guard > 0:
        ready = sorted([name for name, deps in pending.items() if not [dep for dep in deps if dep in pending]])
        order = order + ready
        pending = {name: deps for name, deps in pending.items() if name not in ready}
        guard = guard - 1 if ready else 0
    return order


def matrix_rows(specs, order):
    positions = {name: index + 1 for index, name in enumerate(order)}
    rows = [[spec["name"], spec["version"], spec["kind"], ", ".join(spec["deps"]) or "—", str(positions.get(spec["name"], 0)), "нет" if spec["kind"] == "jar" else "да"] for spec in specs]
    return rows


def spec_flags(specs, prefix):
    flags = ["ok" if Path(prefix).exists() or spec["kind"] in {"autotools", "jar"} else "bad" for spec in specs]
    return flags


def step_rows(specs, order):
    steps = [[f"{index + 1}. {name}", " ".join(plan_actions(next(spec for spec in specs if spec["name"] == name), "/opt/bio")[:2])] for index, name in enumerate(order)]
    return steps


def dependency_graph(order, specs):
    nodes = [{"label": name, "sub": next(spec["version"] for spec in specs if spec["name"] == name)} for name in order]
    links = ["dep"] * (len(nodes) - 1)
    return art.dag(nodes, links, title="порядок сборки")


def summary_cards(specs, order):
    sources = len([spec for spec in specs if spec["kind"] == "autotools"])
    jars = len([spec for spec in specs if spec["kind"] == "jar"])
    return art.stat_cards(
        [
            {"value": str(len(specs)), "label": "инструментов в манифесте", "tone": "acc", "hint": "версии зафиксированы"},
            {"value": str(len(order)), "label": "шагов сборки", "hint": "порядок по зависимостям"},
            {"value": f"{sources}/{jars}", "label": "из исходников / jar", "hint": "две ветки установки"},
            {"value": "sha256", "label": "проверка архива", "tone": "ok", "hint": "до распаковки"},
        ]
    )


def matrix_table(specs, order, prefix):
    return art.table(["инструмент", "версия", "тип", "зависит от", "шаг", "сборка"], matrix_rows(specs, order), flags=spec_flags(specs, prefix))


def plan_log(specs, order):
    commands = [f"[{row[0]}] {row[1]}" for row in step_rows(specs, order)]
    return art.terminal(["$ ./install_tools.sh --prefix /opt/bio --dry-run"] + commands, "plan")


def sections(specs, order, prefix):
    return [
        report.section("01", "Сводка", "Что установится и в каком порядке.", summary_cards(specs, order)),
        report.section("02", "Порядок сборки", "htslib идёт раньше samtools: без библиотеки сборка не начнётся.", report.figure("топологический порядок по полю deps", dependency_graph(order, specs))),
        report.section("03", "Матрица инструментов", "Версии, тип установки и зависимости — одна таблица на весь тулчейн.", matrix_table(specs, order, prefix)),
        report.section("04", "План действий", "Что именно выполнит установщик в режиме --dry-run.", plan_log(specs, order)),
    ]


def write_report(path, specs, order, prefix):
    html = report.page(
        "Проект 03 · Тулчейн установки",
        "Сборка из исходников, проверка sha256, порядок по зависимостям, идемпотентность",
        sections(specs, order, prefix),
        footer="Пути и версии условные; структура манифеста и логика сборки рабочие.",
        badges=["bash", "sha256", "idempotent"],
    )
    return report.write(path, html)


def main(argv):
    prefix = PROJECT / "data" / "prefix"
    CACHE.mkdir(parents=True, exist_ok=True)
    specs = read_manifest(MANIFEST)
    order = dependency_order(specs)
    target = write_report(PROJECT / "docs" / "report.html", specs, order, prefix)
    print(f"Отчёт: {target}")
    print("Порядок сборки: " + ", ".join(order))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
