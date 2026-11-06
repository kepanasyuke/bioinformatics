"""Собирает GIF-версии анимированных шапок через headless Chrome.

GitHub не проигрывает SMIL-анимацию внутри SVG, поэтому в README лежат GIF,
а SVG остаются исходником. Съёмка идёт по кадрам: для каждого момента времени
браузер получает --virtual-time-budget и отдаёт скриншот.

Запуск: python tools/headers_gif.py
"""

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "docs" / "img"
BUDGETS = [250, 750, 1250, 1750, 2250, 2750]
SIZE = "1200,300"

sys.path.insert(0, str(ROOT))

from tools.shoot_game import shoot


def wrapper(svg_text):
    style = "html,body{margin:0;background:#0b1118}svg{display:block;width:1200px;height:300px}"
    return f'<!doctype html><html lang="ru"><head><meta charset="utf-8"><style>{style}</style></head><body>{svg_text}</body></html>'


def scene_files():
    return sorted(IMG.glob("header-*.svg"))


def page_for(svg_path, folder):
    page = Path(folder) / (svg_path.stem + ".html")
    page.write_text(wrapper(svg_path.read_text(encoding="utf-8")), encoding="utf-8")
    return page


def frames_of(svg_path, folder):
    page = page_for(svg_path, folder)
    url = f"file:///{page.as_posix()}"
    return [shoot(url, Path(folder) / f"{svg_path.stem}-{index}.png", budget, SIZE) for index, budget in enumerate(BUDGETS)]


def make_gif(paths, target, duration=380):
    try:
        from PIL import Image

        images = [Image.open(path).convert("RGB") for path in paths]
        images[0].save(target, save_all=True, append_images=images[1:], duration=duration, loop=0, optimize=True)
        result = f"{target.relative_to(ROOT)} — {target.stat().st_size // 1024} КБ"
    except ImportError:
        result = "Pillow не установлен: pip install pillow"
    return result


def main(argv):
    folder = tempfile.mkdtemp(prefix="headers-")
    scenes = scene_files()
    made = [make_gif(frames_of(scene, folder), IMG / (scene.stem + ".gif")) for scene in scenes]
    print("\n".join(made))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
