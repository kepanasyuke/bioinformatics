"""Рисует анимированные SVG-шапки для каждого из семи проектов.

Анимация сделана на SMIL, поэтому работает в браузере и в <img> на GitHub.
Запуск: python -m tools.viz.header
"""

import sys
from pathlib import Path

from tools.viz import svg as art

ROOT = Path(__file__).resolve().parents[2]
WIDTH, HEIGHT = 1200, 300
TITLE_X, TITLE_Y = 40, 54


def fade_box(x, y, width, height, color, begin, radius=8):
    return (
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{radius}" fill="{color}" opacity="0">'
        f'<animate attributeName="opacity" from="0" to="1" begin="{begin}s" dur="0.55s" fill="freeze"/></rect>'
    )


def grow_bar(x, base, width, height, color, begin):
    return (
        f'<rect x="{x}" y="{base - height}" width="{width}" height="{height}" rx="5" fill="{color}" opacity="0.15">'
        f'<animate attributeName="opacity" values="0.15;1" begin="{begin}s" dur="0.6s" fill="freeze"/>'
        f'<animate attributeName="height" from="6" to="{height}" begin="{begin}s" dur="0.6s" fill="freeze" calcMode="spline" keySplines="0.2 0.8 0.2 1"/>'
        f'<animate attributeName="y" from="{base - 6}" to="{base - height}" begin="{begin}s" dur="0.6s" fill="freeze"/></rect>'
    )


def slide_dot(x, y, radius, color, begin):
    return (
        f'<circle cx="600" cy="200" r="{radius}" fill="{color}" opacity="0">'
        f'<animate attributeName="cx" from="600" to="{x}" begin="{begin}s" dur="0.9s" fill="freeze"/>'
        f'<animate attributeName="cy" from="200" to="{y}" begin="{begin}s" dur="0.9s" fill="freeze"/>'
        f'<animate attributeName="opacity" from="0" to="0.9" begin="{begin}s" dur="0.3s" fill="freeze"/></circle>'
    )


def head(title, tag):
    return art.text(TITLE_X, TITLE_Y, title, 26, art.THEME["text"], weight=700) + art.text(TITLE_X, TITLE_Y + 26, tag, 13, art.THEME["muted"])


def scene_pipeline():
    names = ["fastp", "bwa-mem2", "markdup", "haplotype", "фильтр"]
    boxes = [fade_box(40 + index * 220, 150, 190, 70, art.THEME["panel"], 0.2 + index * 0.45) for index, name in enumerate(names)]
    labels = [art.text(135 + index * 220, 190, name, 15, art.THEME["accent"], "middle", 600) for index, name in enumerate(names)]
    arrows = [art.line(230 + index * 220, 185, 262 + index * 220, 185, art.THEME["grid"], 2) for index in range(len(names) - 1)]
    marker = fade_box(1120, 250, 40, 10, art.THEME["ok"], 2.7, 4)
    return head("Проект 01 · WGS-пайплайн", "CWL + Docker · один прогон — один и тот же результат") + "".join(boxes + labels + arrows) + marker


def scene_cases():
    cells = [fade_box(40 + (index % 6) * 88, 140 + (index // 6) * 62, 74, 48, art.THEME["ok"], 0.2 + index * 0.16) for index in range(12)]
    counter = art.text(600, 268, "12 / 12 кейсов прошли", 16, art.THEME["ok"], "middle", 600)
    return head("Проект 02 · Регрессионные тесты", "сравнение с эталоном · порог F1 · падение сборки при регрессии") + "".join(cells) + counter


def scene_build():
    lines = ["$ ./install_tools.sh --prefix /opt/bio", "==> htslib 1.20 ................ ok", "==> samtools 1.20 ............. ok", "==> bcftools 1.20 ............. ok", "==> bwa-mem2 2.2.1 ............ ok", "готово: 4 из 4, sha256 совпал"]
    rows = [fade_box(40, 132 + index * 26, 16, 16, art.THEME["accent"] if index == 0 else art.THEME["ok"], 0.2 + index * 0.35, 3) for index in range(len(lines))]
    texts = [art.text(66, 146 + index * 26, item, 13, art.THEME["muted"] if index == 0 else art.THEME["text"]) for index, item in enumerate(lines)]
    return head("Проект 03 · Тулчейн установки", "сборка из исходников · контрольные суммы · идемпотентность") + "".join(rows + texts)


def scene_budget():
    before = [190, 150, 210, 230]
    after = [96, 78, 110, 124]
    bars = [grow_bar(70 + index * 62, 268, 40, before[index], art.THEME["bad"], 0.2 + index * 0.1) for index in range(4)]
    bars = bars + [grow_bar(330 + index * 62, 268, 40, after[index], art.THEME["ok"], 1.0 + index * 0.1) for index in range(4)]
    arrows = [art.text(628, 200, "−47%", 40, art.THEME["ok"], "middle", 700), art.text(628, 232, "core-hours за прогон", 13, art.THEME["muted"], "middle")]
    return head("Проект 04 · Бюджет кластера", "профиль sacct · лимиты памяти и CPU · экономия без потери результата") + "".join(bars + arrows)


def scene_rnaseq():
    dots = [slide_dot(120 + (index % 7) * 130, 150 + (index % 3) * 34, 9, art.THEME["accent"] if index % 2 else art.THEME["violet"], 0.2 + index * 0.12) for index in range(14)]
    labels = art.text(40, 268, "PCA по матрице counts · 8 образцов, 2 группы", 13, art.THEME["muted"])
    return head("Проект 05 · RNA-Seq QC", "fastp → STAR → counts · MultiQC · PCA и volcano") + "".join(dots) + labels


def scene_legacy():
    lines = ["while read sample; do", "  bwa mem -t 8 $REF $sample > out.sam", "  samtools sort out.sam > out.bam", "done < samples.txt", "echo done"]
    rows = [art.text(40, 150 + index * 24, item, 13, art.THEME["text"] if index < 3 else art.THEME["muted"]) for index, item in enumerate(lines)]
    strike = [art.line(34, 150 + index * 24 - 5, 420, 150 + index * 24 - 5, art.THEME["bad"], 2) for index in (1, 3)]
    fixed = art.text(520, 160, "set -euo pipefail · уникальный tmp · проверка кода", 15, art.THEME["ok"], weight=600)
    return head("Проект 06 · Починка legacy", "10 issues · PR с тестом на каждый баг · CHANGELOG") + "".join(rows + strike) + fixed


def scene_freqdb():
    boxes = [
        fade_box(620 + tile["x"] * 520, 120 + tile["y"] * 130, tile["w"] * 520, tile["h"] * 130, art.mix(art.THEME["panel"], art.THEME["accent"], tile["v"]), 0.2 + index * 0.22, 6)
        for index, tile in enumerate(FREQDB_TILES)
    ]
    return head("Проект 07 · База частот", "SQLite + Parquet · аннотация VCF · фильтры по популяциям") + "".join(boxes)


SCENES = [
    ("01-wgs", scene_pipeline),
    ("02-regression", scene_cases),
    ("03-toolchain", scene_build),
    ("04-budget", scene_budget),
    ("05-rnaseq", scene_rnaseq),
    ("06-legacy", scene_legacy),
    ("07-freqdb", scene_freqdb),
]

FREQDB_TILES = [
    {"x": 0.05, "y": 0.10, "w": 0.18, "h": 0.34, "v": 0.25},
    {"x": 0.26, "y": 0.05, "w": 0.22, "h": 0.30, "v": 0.55},
    {"x": 0.51, "y": 0.12, "w": 0.19, "h": 0.40, "v": 0.80},
    {"x": 0.16, "y": 0.50, "w": 0.24, "h": 0.34, "v": 0.40},
    {"x": 0.44, "y": 0.58, "w": 0.18, "h": 0.26, "v": 0.65},
    {"x": 0.66, "y": 0.46, "w": 0.26, "h": 0.32, "v": 0.95},
]


def render(scene):
    name, painter = scene
    body = painter()
    return art.svg(WIDTH, HEIGHT, body, name, animated=True)


def main(argv):
    out_dir = ROOT / "docs" / "img"
    out_dir.mkdir(parents=True, exist_ok=True)
    written = [art_report(name, out_dir, painter) for name, painter in SCENES]
    print("\n".join(written))
    return 0


def art_report(name, out_dir, painter):
    target = out_dir / f"header-{name}.svg"
    target.write_text(art.svg(WIDTH, HEIGHT, painter(), name, animated=True), encoding="utf-8")
    return f"Сохранено: {target.relative_to(ROOT)}"


if __name__ == "__main__":
    sys.exit(main(sys.argv))
