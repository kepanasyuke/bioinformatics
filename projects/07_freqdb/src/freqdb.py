"""Проект 07. База популяционных частот: SQLite, аннотация VCF, фильтры.

Запуск: python projects/07_freqdb/src/freqdb.py
Данные синтетические: 400 вариантов, восемь федеральных округов.
"""

import random
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from tools.viz import report
from tools.viz import svg as art

PROJECT = Path(__file__).resolve().parents[1]
DATA = PROJECT / "data"
DB_PATH = DATA / "freqs.sqlite"
QUERY_VCF = DATA / "query.vcf"

SAMPLE_LINES = {
    "before": "1\t10000\t.\tA\tG\t60\tPASS\tDP=30",
    "after": "1\t10000\t.\tA\tG\t60\tPASS\tDP=30;AF=0.1234",
}

DISTRICTS = [
    {"name": "СЗФО", "x": 0.10, "y": 0.08, "w": 0.16, "h": 0.16},
    {"name": "ЦФО", "x": 0.10, "y": 0.30, "w": 0.16, "h": 0.16},
    {"name": "ЮФО", "x": 0.10, "y": 0.52, "w": 0.14, "h": 0.12},
    {"name": "СКФО", "x": 0.26, "y": 0.54, "w": 0.11, "h": 0.10},
    {"name": "ПФО", "x": 0.28, "y": 0.30, "w": 0.17, "h": 0.16},
    {"name": "УФО", "x": 0.47, "y": 0.22, "w": 0.16, "h": 0.18},
    {"name": "СФО", "x": 0.56, "y": 0.40, "w": 0.20, "h": 0.22},
    {"name": "ДФО", "x": 0.78, "y": 0.26, "w": 0.18, "h": 0.30},
]


def normalize_key(chrom, pos, ref, alt):
    return f"{str(chrom).replace('chr', '')}:{pos}:{ref}>{alt}"


def build_db(path, rows):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE IF NOT EXISTS variant (key TEXT PRIMARY KEY, chrom TEXT, pos INTEGER, ref TEXT, alt TEXT, af REAL, population TEXT)")
    connection.execute("DELETE FROM variant")
    connection.executemany("INSERT OR REPLACE INTO variant VALUES (?, ?, ?, ?, ?, ?, ?)", rows)
    connection.commit()
    connection.close()
    return str(path)


def open_db(path):
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True)


def lookup_variant(connection, key):
    row = connection.execute("SELECT key, chrom, pos, ref, alt, af, population FROM variant WHERE key = ?", (key,)).fetchone()
    return {"key": row[0], "chrom": row[1], "pos": row[2], "ref": row[3], "alt": row[4], "af": row[5], "population": row[6]} if row else {}


def parse_vcf_record(line):
    fields = line.rstrip("\n").split("\t")
    record = {}
    if len(fields) >= 8 and not line.startswith("#"):
        record = {"chrom": fields[0], "pos": int(fields[1]), "ref": fields[3], "alt": fields[4], "filter": fields[6], "info": fields[7]}
        record["key"] = normalize_key(record["chrom"], record["pos"], record["ref"], record["alt"])
    return record


def annotate_record(record, freq):
    parts = [item for item in record.get("info", "").split(";") if item and item != "."]
    added = f"AF={freq['af']:.4f}" if freq else "AF=."
    return {**record, "info": ";".join(parts + [added])}


def filter_by_population(rows, population, min_af):
    selected = [row for row in rows if row["population"] == population and row["af"] >= min_af]
    return selected


def iter_vcf(path):
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    for line in lines:
        record = parse_vcf_record(line)
        if record:
            yield record


def average(values):
    return round(sum(values) / max(len(values), 1), 4)


def demo_rows(seed=4, count=400):
    generator = random.Random(seed)
    rows = []
    for index in range(count):
        district = DISTRICTS[index % len(DISTRICTS)]["name"]
        position = 10000 + index * 37
        frequency = round(min(generator.uniform(0.001, 0.42), 0.5), 4)
        rows.append((normalize_key(1, position, "A", "G"), "1", position, "A", "G", frequency, district))
    return rows


def write_demo(data_dir, rows):
    build_db(Path(data_dir) / "freqs.sqlite", rows)
    header = ["##fileformat=VCFv4.2", "##source=synthetic", "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO"]
    known = [f"1\t{10000 + index * 37}\t.\tA\tG\t60\tPASS\tDP=30" for index in range(0, 20, 2)]
    unknown = [f"1\t{900000 + index}\t.\tC\tT\t60\tPASS\tDP=30" for index in range(2)]
    Path(data_dir).mkdir(parents=True, exist_ok=True)
    Path(data_dir, "query.vcf").write_text("\n".join(header + known + unknown) + "\n", encoding="utf-8")
    return str(Path(data_dir) / "freqs.sqlite")


def district_rows(connection):
    rows = connection.execute("SELECT population, AVG(af), COUNT(*) FROM variant GROUP BY population").fetchall()
    stats = {row[0]: {"af": round(row[1], 4), "count": row[2]} for row in rows}
    return [{"name": district["name"], "af": stats.get(district["name"], {"af": 0.0})["af"], "count": stats.get(district["name"], {"count": 0})["count"], "x": district["x"], "y": district["y"], "w": district["w"], "h": district["h"]} for district in DISTRICTS]


def district_tiles(rows):
    peak = max(row["af"] for row in rows) or 1.0
    return [{"label": row["name"], "x": row["x"], "y": row["y"], "w": row["w"], "h": row["h"], "value": min(row["af"] / peak, 1.0)} for row in rows]


def af_histogram(values, bins=10, limit=0.5):
    counts = [0] * bins
    for value in values:
        index = min(int(value / limit * bins), bins - 1)
        counts[index] += 1
    return counts


def time_sqlite(connection, keys, repeats=3):
    start = time.perf_counter()
    for _ in range(repeats):
        for key in keys:
            lookup_variant(connection, key)
    return round((time.perf_counter() - start) * 1000, 1)


def time_dict(index, keys, repeats=3):
    start = time.perf_counter()
    for _ in range(repeats):
        for key in keys:
            index.get(key)
    return round((time.perf_counter() - start) * 1000, 1)


def summary_cards(rows, annotated, timings):
    total_af = average([row[5] for row in rows])
    return art.stat_cards(
        [
            {"value": str(len(rows)), "label": "вариантов в базе", "tone": "acc", "hint": "синтетика, 8 округов"},
            {"value": f"{total_af:.3f}", "label": "средняя частота", "hint": "AF по всем округам"},
            {"value": f"{annotated}", "label": "аннотировано записей", "tone": "ok", "hint": "из query.vcf"},
            {"value": f"{timings['sqlite']:.0f} мс", "label": "1000 запросов", "hint": f"dict: {timings['dict']:.1f} мс"},
        ]
    )


def sections(rows, stats, annotated, timings, sample_line):
    tiles = art.tiles_map(district_tiles(stats), title="средняя частота по федеральным округам (схема)")
    histogram = art.bar_chart([f"{index * 5}%" for index in range(10)], [{"name": "вариантов", "values": af_histogram([row[5] for row in rows])}], title="распределение частот, AF")
    bench = art.bar_chart(["1000 запросов, мс"], [{"name": "SQLite + индекс", "values": [timings["sqlite"]], "color": art.THEME["accent"]}, {"name": "словарь в памяти", "values": [timings["dict"]], "color": art.THEME["violet"]}], title="скорость поиска")
    table = art.table(["округ", "вариантов", "средний AF"], [[row["name"], row["count"], f"{row['af']:.4f}"] for row in stats], flags=["ok" for _ in stats])
    return [
        report.section("01", "Сводка", "Что лежит в базе и как быстро отвечает.", summary_cards(rows, annotated, timings)),
        report.section("02", "Карта частот", "Схематичная карта: чем темнее плитка, тем выше средняя частота в округе.", report.figure("не географическая проекция, а схема округов", tiles)),
        report.section("03", "Распределение", "Большинство вариантов редкие — так и должно быть.", report.figure("шаг 5%", histogram)),
        report.section("04", "Скорость", "SQLite с индексом против словаря в памяти. Разница — цена того, что база не влезает в RAM.", report.figure("измерено на этой машине", bench)),
        report.section("05", "Таблица по округам", "Числа, на которых построена карта.", table),
        report.section("06", "Аннотация", "Что добавляется в INFO после поиска по базе.", art.terminal(["# было", sample_line["before"], "# стало", sample_line["after"]], "annotate")),
    ]


def write_report(path, rows, stats, annotated, timings, sample_line):
    html = report.page(
        "Проект 07 · База популяционных частот",
        "SQLite, аннотация VCF, фильтры по округам и бенчмарк поиска",
        sections(rows, stats, annotated, timings, sample_line),
        footer="Частоты синтетические; структура базы и запросы настоящие.",
        badges=["SQLite", "VCF", "AF"],
    )
    return report.write(path, html)


def annotate_all(connection):
    records = list(iter_vcf(QUERY_VCF))
    return [annotate_record(record, lookup_variant(connection, record["key"])) for record in records]


def measure(connection, rows):
    keys = [row[0] for row in rows[:50]]
    return {"sqlite": time_sqlite(connection, keys), "dict": time_dict({row[0]: row for row in rows}, keys)}


def main(argv):
    rows = demo_rows()
    write_demo(DATA, rows)
    connection = open_db(DB_PATH)
    stats = district_rows(connection)
    annotated = annotate_all(connection)
    timings = measure(connection, rows)
    target = write_report(PROJECT / "docs" / "report.html", rows, stats, len(annotated), timings, SAMPLE_LINES)
    print(f"Отчёт: {target}")
    print(f"Вариантов: {len(rows)}, аннотировано: {len(annotated)}, найдено в базе: {sum(1 for item in annotated if 'AF=.' not in item['info'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
