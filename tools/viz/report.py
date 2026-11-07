"""Собирает HTML-страницу отчёта из готовых блоков."""

from pathlib import Path

from tools.viz.svg import esc

CSS = """
:root{color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:#0b1118;color:#e6edf3;font:15px/1.55 Inter,"Segoe UI",sans-serif}
main{max-width:1240px;margin:0 auto;padding:32px 24px 64px}
header{padding:28px 0 12px;border-bottom:1px solid #1d2a38;margin-bottom:28px}
h1{margin:0 0 6px;font-size:30px;letter-spacing:-.02em}
.sub{margin:0;color:#8aa0b4;font-size:15px}
h2{font-size:19px;margin:0 0 4px;letter-spacing:-.01em}
.num{display:inline-block;min-width:28px;color:#38bdf8;font-variant-numeric:tabular-nums}
section{margin:34px 0;padding:22px;background:#111a24;border:1px solid #1d2a38;border-radius:14px}
.note{margin:0 0 16px;color:#8aa0b4;font-size:13.5px}
figure{margin:16px 0 0}
figure svg{border-radius:10px;display:block}
figcaption{margin-top:8px;color:#8aa0b4;font-size:12.5px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin:8px 0 18px}
.card{display:flex;flex-direction:column;gap:2px;padding:14px 16px;background:#16202c;border:1px solid #22303f;border-radius:12px}
.card .value{font-size:26px;font-weight:650;letter-spacing:-.02em}
.card .label{font-size:12.5px;color:#8aa0b4}
.card .hint{font-size:11.5px;color:#5f7488}
.card.ok .value{color:#34d399}.card.bad .value{color:#f87171}.card.warn .value{color:#fbbf24}.card.acc .value{color:#38bdf8}
table.data{width:100%;border-collapse:collapse;font-size:13.5px;margin-top:12px}
table.data th{text-align:left;padding:9px 10px;color:#8aa0b4;font-weight:600;border-bottom:1px solid #22303f;font-size:12px;text-transform:uppercase;letter-spacing:.04em}
table.data td{padding:9px 10px;border-bottom:1px solid #17222e;font-variant-numeric:tabular-nums}
table.data tr.ok td{color:#d5fbe9}table.data tr.ok td:first-child{box-shadow:inset 3px 0 0 #34d399}
table.data tr.bad td{color:#ffe2e2}table.data tr.bad td:first-child{box-shadow:inset 3px 0 0 #f87171}
table.data tr.warn td:first-child{box-shadow:inset 3px 0 0 #fbbf24}
table.data caption{caption-side:bottom;text-align:left;color:#8aa0b4;font-size:12px;padding-top:10px}
pre.terminal{background:#070c12;border:1px solid #1d2a38;border-radius:10px;padding:16px 18px;overflow:auto;font:12.5px/1.7 "JetBrains Mono",Consolas,monospace;color:#9fb3c8}
pre.terminal span{display:block;white-space:pre}
pre.terminal span:first-child{color:#34d399}
.kanban{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px}
.kcol{background:#16202c;border:1px solid #22303f;border-radius:12px;padding:12px}
.kcol h3{margin:0 0 10px;font-size:13px;color:#8aa0b4;display:flex;justify-content:space-between;font-weight:600}
.kcol h3 i{font-style:normal;color:#5f7488}
.kcard{display:flex;flex-direction:column;gap:2px;padding:9px 11px;margin-bottom:8px;background:#0f1620;border:1px solid #22303f;border-radius:9px;font-size:12.5px}
.kcard span{color:#5f7488;font-size:11px}
.kcard.done{border-color:#1f5142}.kcard.done b{color:#a7f3d0}
.kcard.open{border-color:#4a3a16}
footer{margin-top:40px;color:#5f7488;font-size:12px;border-top:1px solid #1d2a38;padding-top:16px}
.badge{display:inline-block;padding:2px 9px;border-radius:20px;background:#16202c;border:1px solid #22303f;color:#8aa0b4;font-size:11.5px;margin-right:6px}
"""


def page(title, subtitle, sections, footer="", badges=None):
    marks = "".join(f'<span class="badge">{esc(item)}</span>' for item in (badges or []))
    head = (
        '<!doctype html><html lang="ru"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{esc(title)}</title><style>{CSS}</style></head><body><main>"
    )
    top = f"<header>{marks}<h1>{esc(title)}</h1><p class=\"sub\">{esc(subtitle)}</p></header>"
    tail = f"<footer>{esc(footer)}</footer></main></body></html>" if footer else "</main></body></html>"
    return head + top + "".join(sections) + tail


def section(number, title, note, body):
    return f'<section id="s{esc(number)}"><h2><span class="num">{esc(number)}</span>{esc(title)}</h2><p class="note">{esc(note)}</p>{body}</section>'


def figure(caption, body):
    return f"<figure>{body}<figcaption>{esc(caption)}</figcaption></figure>"


def write(path, content):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8", newline="\n")
    return str(target)
