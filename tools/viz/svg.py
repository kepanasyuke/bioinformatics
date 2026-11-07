"""Рисует графики в SVG и блоки HTML без внешних библиотек.

Все функции возвращают строку. Цвета берутся из THEME, чтобы отчёты
всех семи проектов выглядели одинаково.
"""

import html

THEME = {
    "bg": "#0f1620",
    "panel": "#16202c",
    "grid": "#243343",
    "text": "#e6edf3",
    "muted": "#8aa0b4",
    "accent": "#38bdf8",
    "ok": "#34d399",
    "warn": "#fbbf24",
    "bad": "#f87171",
    "violet": "#a78bfa",
    "pink": "#f472b6",
}
SERIES = [THEME["accent"], THEME["violet"], THEME["ok"], THEME["warn"], THEME["pink"]]
FONT = "Inter, Segoe UI, sans-serif"


def esc(value):
    return html.escape(str(value))


def num(value):
    return f"{value:.1f}"


def rect(x, y, width, height, fill, radius=4, opacity=1.0):
    box = f'x="{num(x)}" y="{num(y)}" width="{num(max(width, 0))}" height="{num(max(height, 0))}"'
    return f'<rect {box} rx="{radius}" fill="{fill}" fill-opacity="{opacity}"/>'


def text(x, y, value, size=12, fill=None, anchor="start", weight=400):
    return (
        f'<text x="{num(x)}" y="{num(y)}" font-size="{size}" fill="{fill or THEME["text"]}" '
        f'text-anchor="{anchor}" font-weight="{weight}" font-family="{FONT}">{esc(value)}</text>'
    )


def line(x1, y1, x2, y2, stroke, width=1.0, dash=""):
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    return (
        f'<line x1="{num(x1)}" y1="{num(y1)}" x2="{num(x2)}" y2="{num(y2)}" '
        f'stroke="{stroke}" stroke-width="{width}"{dash_attr}/>'
    )


def polyline(points, stroke, width=2.0):
    path = " ".join(f"{num(x)},{num(y)}" for x, y in points)
    return f'<polyline points="{path}" fill="none" stroke="{stroke}" stroke-width="{width}" stroke-linejoin="round"/>'


def circle(cx, cy, radius, fill, opacity=1.0):
    return f'<circle cx="{num(cx)}" cy="{num(cy)}" r="{num(radius)}" fill="{fill}" fill-opacity="{opacity}"/>'


def svg(width, height, body, title="", animated=False):
    marker = ' class="animated"' if animated else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg"{marker} viewBox="0 0 {width} {height}" '
        f'width="100%" preserveAspectRatio="xMidYMid meet" role="img" aria-label="{esc(title)}">'
        f'<rect width="{width}" height="{height}" fill="{THEME["bg"]}" rx="10"/>{body}</svg>'
    )


def norm(value, low, high, out_low, out_high):
    span = (high - low) or 1
    return out_low + (value - low) / span * (out_high - out_low)


def geometry(labels, width, height):
    pad_left, pad_right, pad_top, pad_bottom = 62, 20, 36, 48
    plot_w = width - pad_left - pad_right
    plot_h = height - pad_top - pad_bottom
    return {"left": pad_left, "top": pad_top, "plot_w": plot_w, "plot_h": plot_h, "base": pad_top + plot_h, "slot": plot_w / max(len(labels), 1), "right": pad_left + plot_w}


def grid_lines(box):
    steps = [0, 1, 2, 3, 4]
    return "".join(
        line(box["left"], box["base"] - box["plot_h"] * s / 4, box["right"], box["base"] - box["plot_h"] * s / 4, THEME["grid"], 1, "4 6")
        for s in steps
    )


def y_ticks(box, top, fmt="{:.0f}"):
    steps = [0, 1, 2, 3, 4]
    return "".join(text(box["left"] - 10, box["base"] - box["plot_h"] * s / 4 + 4, fmt.format(top * s / 4), 11, THEME["muted"], "end") for s in steps)


def x_ticks(labels, box):
    return "".join(text(box["left"] + i * box["slot"] + box["slot"] / 2, box["base"] + 20, label, 11, THEME["muted"], "middle") for i, label in enumerate(labels))


def legend(groups, width):
    start = width - 20 - 132 * len(groups)
    return "".join(rect(start + i * 132, 14, 10, 10, groups[i].get("color", SERIES[i % len(SERIES)])) + text(start + i * 132 + 16, 23, groups[i]["name"], 11, THEME["muted"]) for i in range(len(groups)))


def bar_rect(index, order, value, box, bar_w, top, colors):
    height = value / (top or 1) * box["plot_h"]
    x = box["left"] + index * box["slot"] + box["slot"] * 0.16 + order * bar_w
    return rect(x, box["base"] - height, bar_w, height, colors[order])


def bar_chart(labels, groups, width=760, height=300, title="", value_fmt="{:.0f}"):
    box = geometry(labels, width, height)
    values = [value for group in groups for value in group["values"]]
    top = max(values + [1]) * 1.18
    bar_w = box["slot"] * 0.68 / max(len(groups), 1)
    colors = [group.get("color", SERIES[i % len(SERIES)]) for i, group in enumerate(groups)]
    bars = "".join(bar_rect(i, k, value, box, bar_w, top, colors) for k, group in enumerate(groups) for i, value in enumerate(group["values"]))
    body = grid_lines(box) + bars + y_ticks(box, top, value_fmt) + x_ticks(labels, box)
    head = text(16, 24, title, 13, THEME["text"], weight=600) + legend(groups, width)
    return svg(width, height, head + body, title)


def line_points(values, box, top):
    return [(box["left"] + i * box["slot"] + box["slot"] / 2, box["base"] - value / (top or 1) * box["plot_h"]) for i, value in enumerate(values)]


def line_chart(labels, groups, width=760, height=300, title="", value_fmt="{:.0f}", dots=True):
    box = geometry(labels, width, height)
    values = [value for group in groups for value in group["values"]]
    top = max(values + [1]) * 1.18
    colors = [group.get("color", SERIES[i % len(SERIES)]) for i, group in enumerate(groups)]
    lines = "".join(polyline(line_points(group["values"], box, top), colors[i], 2) for i, group in enumerate(groups))
    marks = "".join(circle(x, y, 3.5, colors[i]) for i, group in enumerate(groups) for x, y in line_points(group["values"], box, top)) if dots else ""
    body = grid_lines(box) + lines + marks + y_ticks(box, top, value_fmt) + x_ticks(labels, box)
    head = text(16, 24, title, 13, THEME["text"], weight=600) + legend(groups, width)
    return svg(width, height, head + body, title)


def hbar_row(label, value, index, left, top, width, row_height, peak, value_fmt):
    y = top + index * row_height
    bar_width = value / (peak or 1) * (width - left - 80)
    name = text(left - 10, y + row_height - 12, label, 11, THEME["muted"], "end")
    amount = text(left + bar_width + 8, y + row_height - 12, value_fmt.format(value), 11, THEME["text"])
    return rect(left, y, bar_width, row_height - 8, THEME["accent"], 4) + name + amount


def hbar_chart(labels, values, width=1000, row_height=26, title="", value_fmt="{:.0f}"):
    left, top = 200, 44
    peak = max(values + [1])
    rows = [hbar_row(label, value, index, left, top, width, row_height, peak, value_fmt) for index, (label, value) in enumerate(zip(labels, values))]
    return svg(width, top + len(values) * row_height + 16, text(16, 24, title, 13, THEME["text"], weight=600) + "".join(rows), title)


def scatter_ranges(points):
    xs = [point["x"] for point in points]
    ys = [point["y"] for point in points]
    return {"x_low": min(xs) * 1.1, "x_high": max(xs) * 1.1, "y_low": min(ys) * 1.1, "y_high": max(ys) * 1.1}


def scatter_dots(points, box, limits, colors):
    xs = [norm(point["x"], limits["x_low"], limits["x_high"], box["left"], box["right"]) for point in points]
    ys = [norm(point["y"], limits["y_low"], limits["y_high"], box["base"], box["top"]) for point in points]
    return "".join(circle(xs[i], ys[i], 4.5, colors[points[i]["group"]], 0.85) for i in range(len(points)))


def scatter_axes(box, x_label, y_label):
    axes = line(box["left"], box["base"], box["right"], box["base"], THEME["grid"]) + line(box["left"], box["top"], box["left"], box["base"], THEME["grid"])
    return axes + text(box["right"], box["base"] + 22, x_label, 11, THEME["muted"], "end") + text(box["left"] - 6, box["top"] - 10, y_label, 11, THEME["muted"])


def scatter(points, width=760, height=320, title="", x_label="", y_label="", groups=None):
    names = groups or sorted({point["group"] for point in points})
    colors = {name: SERIES[i % len(SERIES)] for i, name in enumerate(names)}
    box = geometry(names, width, height)
    dots = scatter_dots(points, box, scatter_ranges(points), colors)
    head = text(16, 24, title, 13, THEME["text"], weight=600) + legend([{"name": name} for name in names], width)
    return svg(width, height, head + scatter_axes(box, x_label, y_label) + dots, title)


def mix(color_a, color_b, share):
    first = [int(color_a[i:i + 2], 16) for i in (1, 3, 5)]
    second = [int(color_b[i:i + 2], 16) for i in (1, 3, 5)]
    parts = [int(round(first[i] + (second[i] - first[i]) * share)) for i in range(3)]
    return "#{:02x}{:02x}{:02x}".format(*parts)


def heatmap(rows, columns, values, width=760, cell_height=26, title=""):
    left, top = 96, 44
    cell_width = (width - left - 20) / max(len(columns), 1)
    cells = "".join(
        rect(left + j * cell_width, top + i * cell_height, cell_width - 2, cell_height - 2, mix(THEME["panel"], THEME["accent"], values[i][j]))
        for i in range(len(rows))
        for j in range(len(columns))
    )
    row_names = "".join(text(left - 8, top + i * cell_height + 17, rows[i], 11, THEME["muted"], "end") for i in range(len(rows)))
    column_names = "".join(text(left + j * cell_width + cell_width / 2, top - 10, columns[j], 11, THEME["muted"], "middle") for j in range(len(columns)))
    head = text(16, 24, title, 13, THEME["text"], weight=600)
    return svg(width, top + len(rows) * cell_height + 16, head + cells + row_names + column_names, title)


def dag(nodes, links, width=760, height=190, title="схема пайплайна"):
    step = (width - 40) / max(len(nodes), 1)
    boxes = "".join(dag_box(node, i, step) for i, node in enumerate(nodes))
    arrows = "".join(dag_arrow(i, step, links[i]) for i in range(len(nodes) - 1))
    return svg(width, height, boxes + arrows, title)


def dag_box(node, index, step):
    x = 20 + index * step
    width = step - 26
    return rect(x, 58, width, 62, THEME["panel"], 8) + text(x + width / 2, 82, node["label"], 12, THEME["text"], "middle", 600) + text(x + width / 2, 102, node.get("sub", ""), 10, THEME["muted"], "middle")


def dag_arrow(index, step, tool):
    start = 20 + index * step + step - 26
    return line(start, 89, start + 22, 89, THEME["accent"], 2) + text(start + 11, 78, tool, 9, THEME["muted"], "middle")


def tiles_map(tiles, width=760, height=300, title=""):
    boxes = "".join(
        rect(20 + tile["x"] * (width - 60), 44 + tile["y"] * (height - 90), tile["w"] * (width - 60), tile["h"] * (height - 90), mix(THEME["panel"], THEME["accent"], tile["value"]), 6)
        + text(20 + tile["x"] * (width - 60) + tile["w"] * (width - 60) / 2, 44 + tile["y"] * (height - 90) + tile["h"] * (height - 90) / 2 + 4, tile["label"], 10, THEME["text"], "middle")
        for tile in tiles
    )
    head = text(16, 26, title, 13, THEME["text"], weight=600)
    return svg(width, height, head + boxes, title)


def table(headers, rows, flags=None, caption=""):
    head = "".join(f"<th>{esc(item)}</th>" for item in headers)
    marks = flags or ["" for _ in rows]
    body = "".join(
        f'<tr class="{marks[i]}">' + "".join(f"<td>{esc(cell)}</td>" for cell in row) + "</tr>"
        for i, row in enumerate(rows)
    )
    caption_html = f"<caption>{esc(caption)}</caption>" if caption else ""
    return f'<table class="data">{caption_html}<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>'


def terminal(lines, title="terminal"):
    body = "".join(f"<span>{esc(item)}</span>" for item in lines)
    return f'<pre class="terminal" data-title="{esc(title)}">{body}</pre>'


def stat_cards(items):
    cards = "".join(
        f'<div class="card {item.get("tone", "")}"><span class="value">{esc(item["value"])}</span>'
        f'<span class="label">{esc(item["label"])}</span><span class="hint">{esc(item.get("hint", ""))}</span></div>'
        for item in items
    )
    return f'<div class="cards">{cards}</div>'


def kanban(columns):
    blocks = "".join(kanban_column(column) for column in columns)
    return f'<div class="kanban">{blocks}</div>'


def kanban_column(column):
    cards = "".join(f'<article class="kcard {card.get("tone", "")}"><b>{esc(card["title"])}</b><span>{esc(card.get("tag", ""))}</span></article>' for card in column["cards"])
    return f'<div class="kcol"><h3>{esc(column["title"])}<i>{len(column["cards"])}</i></h3>{cards}</div>'
