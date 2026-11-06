"""Проект 05. RNA-Seq: проверка чтений, команды шагов, QC, PCA и volcano.

Запуск: python projects/05_rnaseq/src/rnaseq.py
Матрица counts и результаты DE синтетические, математика PCA настоящая.
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
DATA = PROJECT / "data"
READS = DATA / "reads"
SAMPLES = DATA / "samples.tsv"
GENES = [f"GENE{index:02d}" for index in range(1, 13)]


def list_samples(path):
    lines = Path(path).read_text(encoding="utf-8").strip().splitlines()
    header = lines[0].split("\t")
    return [dict(zip(header, line.split("\t"))) for line in lines[1:]]


def check_reads(sample, base=READS):
    paths = [base / sample["r1"], base / sample["r2"]]
    problems = [f"нет файла {path.name}" for path in paths if not path.exists() or path.stat().st_size == 0]
    return problems


def make_trim_cmd(sample, outdir="trim"):
    return ["fastp", "-i", sample["r1"], "-I", sample["r2"], "-o", f"{outdir}/{sample['sample']}.R1.fq.gz", "-O", f"{outdir}/{sample['sample']}.R2.fq.gz", "-j", f"{outdir}/{sample['sample']}.fastp.json"]


def make_align_cmd(sample, outdir="align"):
    return ["STAR", "--runThreadN", "8", "--genomeDir", "ref/star", "--readFilesIn", f"{outdir}/../trim/{sample['sample']}.R1.fq.gz", f"{outdir}/../trim/{sample['sample']}.R2.fq.gz", "--outFileNamePrefix", f"{outdir}/{sample['sample']}."]


def run_cmd(command, dry_run=True):
    return {"command": " ".join(command), "code": 0, "dry_run": dry_run}


def qa_grade(value, good, limit, higher_is_better=True):
    score = (value - good) if higher_is_better else (good - value)
    edge = (value - limit) if higher_is_better else (limit - value)
    grade = "bad" if edge < 0 else ("ok" if score >= 0 else "warn")
    return grade


def demo_qc(samples, seed=9):
    generator = random.Random(seed)
    return [
        {
            "sample": sample["sample"],
            "group": sample["group"],
            "reads": generator.randint(18, 42) * 1000000,
            "q30": round(generator.uniform(88.0, 96.5), 1),
            "duplication": round(generator.uniform(0.08, 0.34), 2),
        }
        for sample in samples
    ]


def dot(left, right):
    return sum(pair[0] * pair[1] for pair in zip(left, right))


def matvec(matrix, vector):
    return [dot(row, vector) for row in matrix]


def normalize(vector):
    length = math.sqrt(dot(vector, vector)) or 1.0
    return [value / length for value in vector]


def center_rows(matrix):
    rows = len(matrix)
    columns = len(matrix[0])
    means = [sum(matrix[row][column] for row in range(rows)) / rows for column in range(columns)]
    return [[matrix[row][column] - means[column] for column in range(columns)] for row in range(rows)]


def covariance(matrix):
    rows = len(matrix)
    columns = len(matrix[0])
    return [[sum(matrix[row][left] * matrix[row][right] for row in range(rows)) / max(rows - 1, 1) for right in range(columns)] for left in range(columns)]


def power_iteration(matrix, rounds=80):
    vector = normalize([1.0 + index * 0.01 for index in range(len(matrix))])
    for _ in range(rounds):
        vector = normalize(matvec(matrix, vector))
    return vector


def eigenvalue(matrix, vector):
    return dot(vector, matvec(matrix, vector))


def deflate(matrix, vector):
    share = eigenvalue(matrix, vector)
    size = len(matrix)
    return [[matrix[left][right] - share * vector[left] * vector[right] for right in range(size)] for left in range(size)]


def pca_2d(matrix):
    centered = center_rows(matrix)
    covariance_matrix = covariance(centered)
    first = power_iteration(covariance_matrix)
    second = power_iteration(deflate(covariance_matrix, first))
    xs = matvec(centered, first)
    ys = matvec(centered, second)
    return [{"x": round(xs[index], 2), "y": round(ys[index], 2)} for index in range(len(xs))]


def demo_counts(seed=5, size=8):
    generator = random.Random(seed)
    matrix = [[round(50 + generator.uniform(0, 18) + (6 if row < size // 2 and column < 6 else 0), 1) for column in range(len(GENES))] for row in range(size)]
    return matrix


def demo_de(seed=13, count=40):
    generator = random.Random(seed)
    rows = [
        {"gene": f"GENE{index:02d}", "log2fc": round(generator.gauss(0, 2.1), 2), "padj": round(generator.uniform(1e-9, 0.9), 6)}
        for index in range(1, count + 1)
    ]
    return rows


def write_demo(samples_path, reads_dir):
    reads_dir.mkdir(parents=True, exist_ok=True)
    plans = [("S1", "control"), ("S2", "control"), ("S3", "control"), ("S4", "control"), ("S5", "case"), ("S6", "case"), ("S7", "case"), ("S8", "case")]
    missing = ("S9", "case")
    lines = ["sample\tgroup\tr1\tr2"]
    for name, group in plans + [missing]:
        lines.append(f"{name}\t{group}\t{name}_R1.fastq.gz\t{name}_R2.fastq.gz")
    for name, _group in plans:
        (reads_dir / f"{name}_R1.fastq.gz").write_text("synthetic\n", encoding="utf-8")
        (reads_dir / f"{name}_R2.fastq.gz").write_text("synthetic\n", encoding="utf-8")
    Path(samples_path).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(samples_path)


def accepted(samples):
    return [sample for sample in samples if not check_reads(sample)]


def volcano_points(rows, lfc_cut=1.0, padj_cut=0.05):
    return [
        {"x": row["log2fc"], "y": round(-math.log10(max(row["padj"], 1e-9)), 2), "group": "значимо" if row["padj"] < padj_cut and abs(row["log2fc"]) >= lfc_cut else "не значимо"}
        for row in rows
    ]


def heatmap_values(matrix):
    rows = []
    for gene_index in range(min(len(GENES), 8)):
        column = [matrix[sample][gene_index] for sample in range(len(matrix))]
        low, high = min(column), max(column)
        rows.append([round((value - low) / ((high - low) or 1), 3) for value in column])
    return rows


def qc_table(metrics):
    rows = [[item["sample"], item["group"], f"{item['reads'] / 1000000:.0f}M", f"{item['q30']}%", f"{item['duplication'] * 100:.0f}%", qa_grade(item["q30"], 92.0, 88.0)] for item in metrics]
    flags = [qa_grade(item["q30"], 92.0, 88.0) for item in metrics]
    return rows, flags


def summary_cards(samples, metrics, matrix):
    valid = accepted(samples)
    return art.stat_cards(
        [
            {"value": str(len(samples)), "label": "образцов в таблице", "tone": "acc", "hint": "две группы"},
            {"value": str(len(valid)), "label": "прошли проверку чтений", "tone": "ok", "hint": "файлы на месте"},
            {"value": str(len(samples) - len(valid)), "label": "исключено", "tone": "bad", "hint": "нет fastq"},
            {"value": f"{sum(item['q30'] for item in metrics) / len(metrics):.1f}%", "label": "средний Q30", "hint": "порог 92%"},
        ]
    )


def pca_points(matrix, samples):
    points = pca_2d(matrix)
    return [dict(point, group=samples[index]["group"]) for index, point in enumerate(points)]


def qc_sections(samples, metrics):
    rows, flags = qc_table(metrics)
    qc_chart = art.bar_chart([item["sample"] for item in metrics], [{"name": "Q30, %", "values": [item["q30"] for item in metrics]}], title="доля оснований с Q30")
    table = art.table(["образец", "группа", "чтений", "Q30", "дубликаты", "статус"], rows, flags=flags, caption="Жёлтая метка — образец ниже хорошего порога, красная — ниже предельного.")
    check_log = art.terminal([f"проверено: {len(samples)}", f"принято: {len(accepted(samples))}", "исключён: S9 (нет файлов)"], "check_reads")
    return [
        report.section("01", "Сводка", "Что происходит с образцами до выравнивания.", summary_cards(samples, metrics, [])),
        report.section("02", "Проверка чтений", "Образец без fastq исключается сразу, а не через три часа на кластере.", check_log),
        report.section("03", "QC по образцам", "Q30 и дубликаты — два порога, по которым образец уходит в брак.", table),
        report.section("04", "Q30 по образцам", "Наглядно видно, кто выбивается из общей картины.", report.figure("порог 92%", qc_chart)),
    ]


def analysis_sections(samples, matrix, de_rows):
    valid = accepted(samples)
    counts = art.line_chart([sample["sample"] for sample in valid], [{"name": "глубина", "values": [sum(matrix[index]) / len(GENES) for index in range(len(valid))]}], title="средняя глубина по генам")
    commands = [run_cmd(make_trim_cmd(samples[0]))["command"], run_cmd(make_align_cmd(samples[0]))["command"], "multiqc -o qc reports/"]
    return [
        report.section("05", "Глубина по генам", "Средняя глубина по принятым образцам.", report.figure("синтетическая матрица counts", counts)),
        report.section("06", "PCA", "Образцы двух групп расходятся по первой компоненте.", report.figure("power iteration по ковариационной матрице", art.scatter(pca_points(matrix, valid), title="PCA: 8 образцов", x_label="PC1", y_label="PC2"))),
        report.section("07", "Volcano", "Дифференциальная экспрессия: значимые гены уходят вверх и в стороны.", report.figure("порог padj 0.05 и |log2FC| 1", art.scatter(volcano_points(de_rows), title="volcano", x_label="log2FC", y_label="−log10 padj"))),
        report.section("08", "Тепловая карта", "Топ-8 генов по образцам: видно блочную структуру двух групп.", report.figure("нормировка по гену", art.heatmap([f"GENE{index:02d}" for index in range(1, 9)], [sample["sample"] for sample in valid], heatmap_values(matrix), title="экспрессия, 0..1"))),
        report.section("09", "Команды", "Что реально запускается для одного образца.", art.terminal(["$ " + command for command in commands], "dry-run")),
    ]


def sections(samples, metrics, matrix, de_rows):
    return qc_sections(samples, metrics) + analysis_sections(samples, matrix, de_rows)


def write_report(path, samples, metrics, matrix, de_rows):
    html = report.page(
        "Проект 05 · RNA-Seq QC",
        "fastp → STAR → counts, проверка файлов, QC, PCA и вулкано-график",
        sections(samples, metrics, matrix, de_rows),
        footer="Матрица counts и DE синтетические; PCA считается честно, без numpy.",
        badges=["RNA-Seq", "PCA", "QC"],
    )
    return report.write(path, html)


def main(argv):
    write_demo(SAMPLES, READS)
    samples = list_samples(SAMPLES)
    metrics = demo_qc(samples)
    matrix = demo_counts()
    de_rows = demo_de()
    target = write_report(PROJECT / "docs" / "report.html", samples, metrics, matrix, de_rows)
    print(f"Отчёт: {target}")
    print(f"Образцов: {len(samples)}, принято: {len(accepted(samples))}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
