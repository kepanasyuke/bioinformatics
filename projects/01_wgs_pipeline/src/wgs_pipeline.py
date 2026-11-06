"""Проект 01. WGS-пайплайн: план шагов в CWL, проверка референса и отчёт.

Запуск: python projects/01_wgs_pipeline/src/wgs_pipeline.py
Все данные синтетические, тяжёлые инструменты не запускаются (режим --dry-run).
"""

import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from tools.viz import report
from tools.viz import svg as art

PROJECT = Path(__file__).resolve().parents[1]
CONFIG = PROJECT / "data" / "config.json"

STEPS = [
    {
        "name": "тримминг",
        "tool": "fastp",
        "version": "0.23.4",
        "minutes": 21,
        "template": "fastp -i {sample}.R1.fastq.gz -I {sample}.R2.fastq.gz -o {sample}.R1.cl.fq.gz -O {sample}.R2.cl.fq.gz",
    },
    {
        "name": "выравнивание",
        "tool": "bwa-mem2",
        "version": "2.2.1",
        "minutes": 184,
        "template": "bwa-mem2 mem -t 16 ref.fa {sample}.R1.cl.fq.gz {sample}.R2.cl.fq.gz | samtools sort -@ 4 -o {sample}.sorted.bam",
    },
    {
        "name": "дубликаты",
        "tool": "gatk MarkDuplicates",
        "version": "4.6.0.0",
        "minutes": 46,
        "template": "gatk MarkDuplicates -I {sample}.sorted.bam -O {sample}.dedup.bam -M {sample}.metrics.txt",
    },
    {
        "name": "вызов вариантов",
        "tool": "gatk HaplotypeCaller",
        "version": "4.6.0.0",
        "minutes": 212,
        "template": "gatk HaplotypeCaller -R ref.fa -I {sample}.dedup.bam -O {sample}.g.vcf.gz -ERC GVCF",
    },
    {
        "name": "фильтрация",
        "tool": "bcftools",
        "version": "1.20",
        "minutes": 9,
        "template": "bcftools filter -i 'QUAL>30 && DP>10' -Oz -o {sample}.filtered.vcf.gz {sample}.raw.vcf.gz",
    },
]


def load_config(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return data


def check_reference(paths):
    missing = [str(path) for path in paths if not Path(path).exists()]
    return missing


def step_command(step, sample):
    command = step["template"].format(sample=sample)
    return command


def build_job_order(sample, config):
    order = {"sample": sample, "reference": config["reference"], "outdir": config["outdir"], "threads": config["threads"]}
    order["steps"] = [step["name"] for step in STEPS]
    return order


def run_step(step, sample, dry_run=True):
    result = {"step": step["name"], "tool": step["tool"], "version": step["version"], "minutes": step["minutes"]}
    result["command"] = step_command(step, sample)
    result["code"] = 0
    result["dry_run"] = dry_run
    return result


def run_pipeline(sample, dry_run=True):
    results = [run_step(step, sample, dry_run) for step in STEPS]
    return results


def collect_outputs(results):
    names = [result["step"] for result in results]
    return names


def coverage_bins(seed=7, count=120, base=32.0):
    generator = random.Random(seed)
    values = [round(base + 14 * math.sin(index / 9) + generator.gauss(0, 3), 1) for index in range(count)]
    return values


def demo_variants(seed=11, count=9):
    generator = random.Random(seed)
    positions = sorted(round(generator.uniform(0.02, 0.98), 3) for _ in range(count))
    variants = [{"pos": position, "label": f"rs{1000 + index}"} for index, position in enumerate(positions)]
    return variants


def mean_depth(values):
    average = sum(values) / max(len(values), 1)
    return round(average, 1)


def step_rows(results):
    rows = [[result["step"], result["tool"], result["version"], result["minutes"], result["code"]] for result in results]
    return rows


def variant_track(variants, width=760, height=120):
    marks = "".join(
        art.rect(30 + variant["pos"] * (width - 60), 34, 3, 42, art.THEME["accent"]) + art.text(30 + variant["pos"] * (width - 60), 92, variant["label"], 9, art.THEME["muted"], "middle")
        for variant in variants
    )
    axis = art.line(30, 76, width - 30, 76, art.THEME["grid"], 1)
    head = art.text(16, 22, "положение вариантов на хромосоме (синтетика)", 12, art.THEME["muted"])
    return art.svg(width, height, head + axis + marks, "трек вариантов")


def summary_cards(results, coverage, variants):
    return art.stat_cards(
        [
            {"value": str(len(results)), "label": "шагов в пайплайне", "tone": "acc", "hint": "CWL v1.2"},
            {"value": f"{sum(item['minutes'] for item in results)} мин", "label": "время прогона", "hint": "оценка на 1 образец"},
            {"value": f"{mean_depth(coverage)}×", "label": "среднее покрытие", "tone": "ok", "hint": "синтетические бины"},
            {"value": str(len(variants)), "label": "вариантов в отчёте", "hint": "после фильтра QUAL>30"},
        ]
    )


def schema_figure():
    nodes = [{"label": step["name"], "sub": step["tool"]} for step in STEPS]
    return art.dag(nodes, [step["tool"] for step in STEPS[1:]])


def depth_figure(coverage):
    labels = [str(index) for index in range(len(coverage))]
    return art.line_chart(labels, [{"name": "глубина", "values": coverage}], title="глубина покрытия по бинам, ×", value_fmt="{:.0f}")


def steps_table(results):
    return art.table(
        ["шаг", "инструмент", "версия", "минуты", "код"],
        step_rows(results),
        flags=["ok" for _ in results],
        caption="Версии зафиксированы в образе контейнера — это и есть воспроизводимость.",
    )


def log_block(results):
    commands = [f"[{index + 1}/{len(results)}] {item['command']}" for index, item in enumerate(results)]
    return art.terminal(["$ python src/wgs_pipeline.py --dry-run"] + commands, "dry-run")


def sections(coverage, variants, results):
    return [
        report.section("01", "Сводка", "Что получится после прогона на одном образце.", summary_cards(results, coverage, variants)),
        report.section("02", "Схема пайплайна", "Линейная цепочка шагов, каждый шаг — отдельный инструмент в контейнере.", report.figure("germline.cwl: те же шаги, что и в отчёте", schema_figure())),
        report.section("03", "Покрытие", "Глубина по бинам генома: видно провалы в центромерных районах.", report.figure("синтетические бины, seed=7", depth_figure(coverage))),
        report.section("04", "Варианты", "Положение найденных вариантов на хромосоме.", report.figure("9 вариантов после фильтрации", variant_track(variants))),
        report.section("05", "Шаги и версии", "Таблица того, что именно запускалось.", steps_table(results)),
        report.section("06", "Команды", "Режим --dry-run печатает команды и ничего не запускает.", log_block(results)),
    ]


def write_report(path, coverage, variants, results):
    html = report.page(
        "Проект 01 · WGS-пайплайн",
        "Полногеномное секвенирование: пять шагов, зафиксированные версии, проверка референса",
        sections(coverage, variants, results),
        footer="Данные синтетические. Пайплайн описан в pipeline/germline.cwl.",
        badges=["CWL 1.2", "Docker", "dry-run"],
    )
    return report.write(path, html)


def main(argv):
    config = load_config(CONFIG)
    missing = check_reference([config["reference"], config["outdir"]])
    order = build_job_order("SYNTH_001", config)
    results = run_pipeline(order["sample"], dry_run="--run" not in argv)
    coverage = coverage_bins()
    variants = demo_variants()
    target = write_report(PROJECT / "docs" / "report.html", coverage, variants, results)
    print(f"Отчёт: {target}")
    print(f"Референс не найден: {len(missing)} файлов (это нормально для демо)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
