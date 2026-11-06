"""Проект 04. Бюджет кластера: sacct, лимиты памяти и CPU, экономия core-hours.

Запуск: python projects/04_cluster_budget/src/budget.py
Данные синтетические: 40 задач, распределённых по пяти шагам пайплайна.
"""

import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from tools.viz import report
from tools.viz import svg as art

PROJECT = Path(__file__).resolve().parents[1]
STEPS = ["fastp", "bwa-mem2", "markdup", "haplotypecaller", "bcftools"]
UNITS = {"K": 1 / 1024, "M": 1, "G": 1024, "T": 1024 * 1024}


def parse_mem(value):
    text = str(value).strip().upper().replace("N", "")
    suffix = text[-1] if text[-1:] in UNITS else "M"
    digits = "".join([char for char in text if char.isdigit() or char == "."])
    return int(round(float(digits or 0) * UNITS[suffix]))


def format_mem(megabytes):
    return f"{megabytes / 1024:.1f} ГБ" if megabytes >= 1024 else f"{megabytes} МБ"


def usage_ratio(used, requested):
    share = min(used / requested, 1.0) if requested else 0.0
    return round(share, 3)


def percentile(values, share):
    ordered = sorted(values)
    position = (len(ordered) - 1) * share
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    weight = position - low
    return round(ordered[low] * (1 - weight) + ordered[high] * weight, 1)


def suggest_mem(values):
    target = percentile(values, 0.95) * 1.15
    return int(math.ceil(target / 512) * 512)


def cpu_efficiency(job):
    busy = job["total_cpu"] / max(job["elapsed"], 1)
    return round(busy / max(job["req_cpus"], 1), 3)


def suggest_cpus(job):
    busy = job["total_cpu"] / max(job["elapsed"], 1)
    return max(1, int(math.ceil(busy)))


def core_hours(cpus, minutes):
    return round(cpus * minutes / 60, 2)


def mean(values):
    return round(sum(values) / max(len(values), 1), 3)


def demo_jobs(seed=3, count=40):
    generator = random.Random(seed)
    jobs = []
    for index in range(count):
        requested = generator.choice([4096, 8192, 16384, 32768])
        cpus = generator.choice([8, 16, 24])
        elapsed = generator.randint(12, 220)
        used = int(requested * generator.uniform(0.18, 0.72))
        jobs.append({"job_id": f"{1000 + index}", "step": STEPS[index % len(STEPS)], "req_mem": requested, "max_rss": used, "req_cpus": cpus, "elapsed": elapsed, "total_cpu": round(elapsed * cpus * generator.uniform(0.35, 0.95), 1)})
    return jobs


def summarize(jobs):
    rows = []
    for step in STEPS:
        subset = [job for job in jobs if job["step"] == step]
        before = sum(core_hours(job["req_cpus"], job["elapsed"]) for job in subset)
        after = sum(core_hours(suggest_cpus(job), job["elapsed"]) for job in subset)
        wasted = mean([1 - usage_ratio(job["max_rss"], job["req_mem"]) for job in subset])
        rows.append({"step": step, "jobs": len(subset), "before": round(before, 1), "after": round(after, 1), "memory": suggest_mem([job["max_rss"] for job in subset]), "wasted": wasted})
    return rows


def savings(before, after):
    return round((1 - after / before) * 100, 1) if before else 0.0


def worst_rows(jobs, limit=8):
    ordered = sorted(jobs, key=lambda job: job["req_mem"] - job["max_rss"], reverse=True)[:limit]
    return [[job["job_id"], job["step"], format_mem(job["req_mem"]), format_mem(job["max_rss"]), f"{usage_ratio(job['max_rss'], job['req_mem']) * 100:.0f}%", f"{cpu_efficiency(job) * 100:.0f}%"] for job in ordered]


def scatter_points(jobs):
    return [{"x": job["req_mem"] / 1024, "y": job["max_rss"] / 1024, "group": "перерасход > 50%" if usage_ratio(job["max_rss"], job["req_mem"]) < 0.5 else "в норме"} for job in jobs]


def heatmap_values(rows):
    return [[round(1 - row["wasted"], 3), round(1 - savings_share(row), 3)] for row in rows]


def savings_share(row):
    return round(row["after"] / row["before"], 3) if row["before"] else 1.0


def summary_cards(jobs, rows):
    before = sum(row["before"] for row in rows)
    after = sum(row["after"] for row in rows)
    extra_mem = sum(job["req_mem"] - job["max_rss"] for job in jobs) / 1024
    return art.stat_cards(
        [
            {"value": str(len(jobs)), "label": "задач в профиле", "tone": "acc", "hint": "пять шагов пайплайна"},
            {"value": f"−{savings(before, after)}%", "label": "core-hours", "tone": "ok", "hint": f"{before:.0f} → {after:.0f}"},
            {"value": f"{extra_mem:.0f} ГБ", "label": "лишней памяти запрошено", "tone": "bad", "hint": "разница лимита и пика"},
            {"value": f"{mean([cpu_efficiency(job) for job in jobs]) * 100:.0f}%", "label": "средняя загрузка CPU", "tone": "warn", "hint": "доля от запрошенных потоков"},
        ]
    )


def sections(jobs, rows):
    cards = summary_cards(jobs, rows)
    before_after = art.bar_chart([row["step"] for row in rows], [{"name": "до", "values": [row["before"] for row in rows], "color": art.THEME["bad"]}, {"name": "после", "values": [row["after"] for row in rows], "color": art.THEME["ok"]}], title="core-hours по шагам, до и после")
    scatter = art.scatter(scatter_points(jobs), title="запрошено против использовано, ГБ", x_label="запрошено", y_label="пик")
    heat = art.heatmap([row["step"] for row in rows], ["память", "CPU"], heatmap_values(rows), title="доля полезного использования")
    table = art.table(["задача", "шаг", "запрошено", "пик", "память", "CPU"], worst_rows(jobs), flags=["bad" for _ in range(8)])
    return [
        report.section("01", "Сводка", "Что видно по 40 задачам без единого запуска заново.", cards),
        report.section("02", "До и после", "Экономия получается из двух правок: лимит памяти по p95 и число потоков по фактической загрузке.", report.figure("один и тот же результат, меньше core-hours", before_after)),
        report.section("03", "Запрошено против использовано", "Точки вдоль нижнего края — задачи, которым память просили «на всякий случай».", report.figure("идеал — диагональ", scatter)),
        report.section("04", "Полезное использование", "Тепловая карта по шагам: где ресурсы простаивают сильнее всего.", report.figure("1.0 — всё использовано", heat)),
        report.section("05", "Худшие задачи", "Кандидаты, с которых начинать оптимизацию.", table),
    ]


def write_report(path, jobs, rows):
    html = report.page(
        "Проект 04 · Бюджет кластера",
        "sacct, лимиты памяти и потоков, экономия core-hours без потери результата",
        sections(jobs, rows),
        footer="Данные синтетические, модель sacct упрощена до нужных полей.",
        badges=["SLURM", "p95", "core-hours"],
    )
    return report.write(path, html)


def main(argv):
    jobs = demo_jobs()
    rows = summarize(jobs)
    target = write_report(PROJECT / "docs" / "report.html", jobs, rows)
    before = sum(row["before"] for row in rows)
    after = sum(row["after"] for row in rows)
    print(f"Отчёт: {target}")
    print(f"Core-hours: {before:.0f} → {after:.0f} (−{savings(before, after)}%)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
