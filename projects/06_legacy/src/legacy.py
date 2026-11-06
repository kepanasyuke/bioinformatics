"""Проект 06. Починка legacy-пайплайна: разбор VCF, сравнение прогонов, отчёт.

Запуск: python projects/06_legacy/src/legacy.py
Сломанная версия лежит в legacy/broken_pipeline.sh.orig, исправленная — в src/fixed_pipeline.sh.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from tools.viz import report
from tools.viz import svg as art

PROJECT = Path(__file__).resolve().parents[1]
DATA = PROJECT / "data"

ISSUES = [
    ("B1", "нет set -euo pipefail", "тихое падение", "done"),
    ("B2", "for f in $(ls *.fastq)", "пробелы в именах", "done"),
    ("B3", "cd без кавычек", "уводит в корень", "done"),
    ("B4", "continue в глубине", "нечитаемая логика", "done"),
    ("B5", "три return в check_vcf", "неясный выход", "done"),
    ("B6", "вложенность 5", "невозможно проверить", "done"),
    ("B7", "rm -rf без кавычек", "риск удалить всё", "done"),
    ("B8", "общий /tmp на все образцы", "гонка данных", "wip"),
    ("B9", "коды возврата не проверяются", "битый BAM", "open"),
    ("B10", "grep вместо разбора VCF", "неверный подсчёт", "open"),
]

BROKEN_LINES = [
    "while [ $i -lt 5 ]; do",
    "  if [ -f $f ]; then",
    "    if [ -s $f ]; then",
    "      if [ \"$s\" != \"\" ]; then",
    "        if [ ! -e done_$s ]; then",
    "          continue",
    "        fi",
    "      fi",
    "    fi",
    "  fi",
    "done",
]

FIXED_LINES = [
    "process_sample() {",
    "    local folder status=0",
    "    folder=\"$(tmp_dir_for \"$1\")\"",
    "    if [[ -e \"${folder}/done\" ]]; then",
    "        printf 'пропуск: %s\\n' \"$1\"",
    "    else",
    "        align_sample \"$1\" \"${folder}\" || status=1",
    "    fi",
    "    return \"${status}\"",
    "}",
]


def parse_vcf_line(line):
    fields = line.rstrip("\n").split("\t")
    record = {}
    if len(fields) >= 8:
        record = {"chrom": fields[0], "pos": int(fields[1]), "ref": fields[3], "alt": fields[4], "filter": fields[6]}
    return record


def count_variants(path):
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    records = [parse_vcf_line(line) for line in lines if line and not line.startswith("#")]
    return len([record for record in records if record])


def write_demo(data_dir):
    target = Path(data_dir)
    target.mkdir(parents=True, exist_ok=True)
    vcf = ["##fileformat=VCFv4.2", "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO"]
    vcf = vcf + [f"chr1\t{1000 + index}\t.\tA\tG\t50\tPASS\tDP=32" for index in range(1, 15)]
    (target / "sample.vcf").write_text("\n".join(vcf) + "\n", encoding="utf-8")
    before = ["run_id\tminutes\tfailed", "r1\t412\t11", "r2\t398\t9", "r3\t455\t12", "r4\t421\t10", "r5\t380\t8"]
    after = ["run_id\tminutes\tfailed", "r1\t196\t0", "r2\t188\t0", "r3\t201\t0", "r4\t192\t0", "r5\t185\t0"]
    (target / "runs_before.tsv").write_text("\n".join(before) + "\n", encoding="utf-8")
    (target / "runs_after.tsv").write_text("\n".join(after) + "\n", encoding="utf-8")
    return str(target)


def read_runs(path):
    lines = Path(path).read_text(encoding="utf-8").strip().splitlines()
    header = lines[0].split("\t")
    return [dict(zip(header, [row.split("\t")[0], int(row.split("\t")[1]), int(row.split("\t")[2])])) for row in lines[1:]]


def average(values):
    return round(sum(values) / max(len(values), 1), 1)


def compare_runs(before, after):
    minutes_before = average([row["minutes"] for row in before])
    minutes_after = average([row["minutes"] for row in after])
    return {
        "minutes_before": minutes_before,
        "minutes_after": minutes_after,
        "speedup": round((1 - minutes_after / minutes_before) * 100, 1),
        "failed_before": sum(row["failed"] for row in before),
        "failed_after": sum(row["failed"] for row in after),
    }


def issue_board():
    columns = [
        {"title": "Открыто", "cards": [{"title": item[1], "tag": f"{item[0]} · {item[2]}", "tone": "open"} for item in ISSUES if item[3] == "open"]},
        {"title": "В работе", "cards": [{"title": item[1], "tag": f"{item[0]} · {item[2]}", "tone": "open"} for item in ISSUES if item[3] == "wip"]},
        {"title": "Закрыто", "cards": [{"title": item[1], "tag": f"{item[0]} · PR + тест", "tone": "done"} for item in ISSUES if item[3] == "done"]},
    ]
    return art.kanban(columns)


def summary_cards(metrics):
    return art.stat_cards(
        [
            {"value": "10", "label": "багов найдено", "tone": "warn", "hint": "B1…B10 в ISSUES.md"},
            {"value": f"−{metrics['speedup']}%", "label": "время прогона", "tone": "ok", "hint": f"{metrics['minutes_before']:.0f} → {metrics['minutes_after']:.0f} мин"},
            {"value": str(metrics["failed_after"]), "label": "упавших образцов", "tone": "ok", "hint": f"было {metrics['failed_before']}"},
            {"value": "0", "label": "continue в коде", "tone": "acc", "hint": "после рефакторинга"},
        ]
    )


def sections(metrics):
    before_after = art.bar_chart(["время, мин", "падения"], [{"name": "до", "values": [metrics["minutes_before"], metrics["failed_before"]], "color": art.THEME["bad"]}, {"name": "после", "values": [metrics["minutes_after"], metrics["failed_after"] * 20], "color": art.THEME["ok"]}], title="до и после: время и падения (падения ×20 для масштаба)")
    return [
        report.section("01", "Сводка", "Что дала починка пяти прогонов.", summary_cards(metrics)),
        report.section("02", "До и после", "Время сократилось вдвое: ушла повторная обработка и лишние перезапуски.", report.figure("синтетическая модель прогонов", before_after)),
        report.section("03", "Доска багов", "Каждый закрытый баг — отдельный PR с тестом или shellcheck-правилом.", issue_board()),
        report.section("04", "Было", "Пять уровней вложенности, три выхода, continue в середине.", art.terminal(["# legacy/broken_pipeline.sh.orig"] + BROKEN_LINES, "было")),
        report.section("05", "Стало", "Один выход, вложенность два, continue нет.", art.terminal(["# src/fixed_pipeline.sh"] + FIXED_LINES, "стало")),
    ]


def write_report(path, metrics):
    html = report.page(
        "Проект 06 · Починка legacy",
        "10 багов в чужом bash-пайплайне: issue → PR → тест → CHANGELOG",
        sections(metrics),
        footer="Время и падения смоделированы в data/runs_*.tsv; разбор VCF и сравнение прогонов настоящие.",
        badges=["bash", "shellcheck", "CHANGELOG"],
    )
    return report.write(path, html)


def main(argv):
    write_demo(DATA)
    metrics = compare_runs(read_runs(DATA / "runs_before.tsv"), read_runs(DATA / "runs_after.tsv"))
    target = write_report(PROJECT / "docs" / "report.html", metrics)
    print(f"Отчёт: {target}")
    print(f"Вариантов в sample.vcf: {count_variants(DATA / 'sample.vcf')}")
    print(f"Ускорение: −{metrics['speedup']}%")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
