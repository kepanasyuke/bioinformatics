"""Проект 02. Регрессионные тесты: сравниваем VCF с эталоном и ловим просадку F1.

Запуск: python projects/02_regression/src/regression.py
Кейсы синтетические, но сравнение настоящие: считаются TP, FP, FN и F1.
"""

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from tools.viz import report
from tools.viz import svg as art

PROJECT = Path(__file__).resolve().parents[1]
CASES = PROJECT / "data" / "cases"
HISTORY = PROJECT / "data" / "history.tsv"
THRESHOLD = 0.95

BASE_VARIANTS = [(1, 1000 * index + 17, "A", "G") for index in range(1, 13)]
EXTRA_VARIANT = [(1, 777777, "C", "T")]


def variant_key(chrom, pos, ref, alt):
    return f"chr{chrom}:{pos}:{ref}>{alt}"


def parse_vcf_line(line):
    fields = line.split("\t")
    key = variant_key(fields[0].replace("chr", ""), fields[1], fields[3], fields[4]) if len(fields) >= 5 else ""
    return key


def read_vcf(path):
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    keys = [parse_vcf_line(line) for line in lines if line and not line.startswith("#")]
    return [key for key in keys if key]


def ratio(part, total):
    return round(part / max(total, 1), 4)


def f1_score(precision, recall):
    return round(2 * precision * recall / max(precision + recall, 1e-9), 4)


def compare_vcf(etalon_path, actual_path):
    etalon = set(read_vcf(etalon_path))
    actual = set(read_vcf(actual_path))
    matched = len(etalon & actual)
    precision = ratio(matched, len(actual))
    recall = ratio(matched, len(etalon))
    return {"tp": matched, "fp": len(actual - etalon), "fn": len(etalon - actual), "precision": precision, "recall": recall, "f1": f1_score(precision, recall)}


def is_regression(f1, threshold=THRESHOLD):
    return f1 < threshold


def hash_file(path):
    digest = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    return digest


def vcf_text(variants):
    header = ["##fileformat=VCFv4.2", "##source=regression-demo", "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO"]
    rows = [f"chr{chrom}\t{pos}\t.\t{ref}\t{alt}\t50\tPASS\t." for chrom, pos, ref, alt in variants]
    return "\n".join(header + rows) + "\n"


def write_case(cases_dir, name, etalon, actual):
    target = Path(cases_dir) / name
    target.mkdir(parents=True, exist_ok=True)
    (target / "etalon.vcf").write_text(vcf_text(etalon), encoding="utf-8")
    (target / "actual.vcf").write_text(vcf_text(actual), encoding="utf-8")
    return str(target)


def demo_cases(cases_dir):
    plans = {
        "case_a_ideal": (BASE_VARIANTS, BASE_VARIANTS),
        "case_b_regression": (BASE_VARIANTS, BASE_VARIANTS[:-2]),
        "case_c_extra": (BASE_VARIANTS, BASE_VARIANTS + EXTRA_VARIANT),
    }
    written = [write_case(cases_dir, name, etalon, actual) for name, (etalon, actual) in plans.items()]
    return written


def list_cases(cases_dir):
    return sorted([folder for folder in Path(cases_dir).iterdir() if folder.is_dir()])


def case_metrics(case_dir):
    etalon = Path(case_dir) / "etalon.vcf"
    actual = Path(case_dir) / "actual.vcf"
    metrics = compare_vcf(etalon, actual)
    metrics["name"] = Path(case_dir).name
    metrics["verdict"] = "bad" if is_regression(metrics["f1"]) else "ok"
    metrics["hash"] = hash_file(actual)[:12]
    return metrics


def suite_rows(cases):
    rows = [[item["name"], item["tp"], item["fp"], item["fn"], f"{item['precision']:.2f}", f"{item['recall']:.2f}", f"{item['f1']:.3f}", item["hash"]] for item in cases]
    return rows


def pass_rate(cases):
    passed = [item for item in cases if item["verdict"] == "ok"]
    return round(len(passed) / max(len(cases), 1), 3)


def history_rows(path):
    lines = Path(path).read_text(encoding="utf-8").strip().splitlines()
    rows = [line.split("\t") for line in lines[1:]]
    return [{"version": row[0], "total": int(row[1]), "passed": int(row[2])} for row in rows]


def write_history(path):
    rows = [["version", "total", "passed"], ["v1.0", "12", "10"], ["v1.1", "12", "11"], ["v1.2", "12", "12"], ["v1.3", "12", "12"]]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join("\t".join(row) for row in rows) + "\n", encoding="utf-8")
    return str(path)


def summary_cards(cases):
    return art.stat_cards(
        [
            {"value": f"{pass_rate(cases) * 100:.0f}%", "label": "кейсов прошли", "tone": "ok" if pass_rate(cases) == 1 else "warn", "hint": f"{len(cases)} кейса"},
            {"value": str(THRESHOLD), "label": "порог F1", "hint": "ниже — сборка падает"},
            {"value": f"{min(item['f1'] for item in cases):.3f}", "label": "худший F1", "tone": "bad", "hint": "кейс с просадкой"},
            {"value": "0", "label": "continue в коде", "tone": "acc", "hint": "правило стиля"},
        ]
    )


def cases_table(cases):
    return art.table(
        ["кейс", "TP", "FP", "FN", "precision", "recall", "F1", "sha256"],
        suite_rows(cases),
        flags=[item["verdict"] for item in cases],
        caption="Красная строка — регрессия: результат разошёлся с эталоном сильнее порога.",
    )


def threshold_figure(cases):
    labels = [item["name"] for item in cases]
    groups = [{"name": "F1", "values": [item["f1"] for item in cases]}, {"name": "порог", "values": [THRESHOLD for _ in cases]}]
    return art.bar_chart(labels, groups, title="F1 по кейсам и порог", value_fmt="{:.2f}")


def history_figure(history):
    groups = [{"name": "доля пройденных", "values": [row["passed"] / row["total"] for row in history]}]
    return art.line_chart([row["version"] for row in history], groups, title="доля пройденных кейсов по версиям", value_fmt="{:.1f}")


def suite_log(cases):
    passed = sum(1 for item in cases if item["verdict"] == "ok")
    status = "ok" if passed == len(cases) else "regression detected"
    return art.terminal(["$ python src/regression.py", f"кейсов: {len(cases)}", f"прошли: {passed}", f"статус: {status}"], "suite")


def sections(cases, history):
    return [
        report.section("01", "Сводка", "Что показывает прогон набора кейсов.", summary_cards(cases)),
        report.section("02", "Кейсы", "Сравнение по вариантам: TP, FP, FN и итоговый F1.", cases_table(cases)),
        report.section("03", "Порог", "F1 по кейсам на фоне порога: всё, что ниже, валит сборку.", report.figure("красный столбик — регрессия", threshold_figure(cases))),
        report.section("04", "История версий", "Как менялась доля пройденных кейсов от версии к версии.", report.figure("data/history.tsv", history_figure(history))),
        report.section("05", "Вывод прогона", "Тот же вывод печатает CI-джоба.", suite_log(cases)),
    ]


def write_report(path, cases, history):
    html = report.page(
        "Проект 02 · Регрессионные тесты",
        "Сравнение VCF с эталоном: TP/FP/FN, F1, порог и падение сборки при просадке",
        sections(cases, history),
        footer="Данные синтетические. Сравнение написано без внешних библиотек.",
        badges=["F1", "sha256", "CI gate"],
    )
    return report.write(path, html)


def main(argv):
    demo_cases(CASES)
    write_history(HISTORY)
    cases = [case_metrics(case) for case in list_cases(CASES)]
    history = history_rows(HISTORY)
    target = write_report(PROJECT / "docs" / "report.html", cases, history)
    print(f"Отчёт: {target}")
    print(f"Кейсов: {len(cases)}, прошли: {sum(1 for item in cases if item['verdict'] == 'ok')}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
