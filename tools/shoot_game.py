"""Снимает скриншоты игры про ДНК и собирает из кадров GIF.

Нужен установленный Chrome или Edge. Запуск:
    python tools/shoot_game.py
"""

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "web" / "dna-game" / "index.html"
OUT = ROOT / "web" / "dna-game" / "docs"
BROWSERS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]
SHOTS = [
    ("game-play.png", "state=play&seed=7&score=6", 1200),
    ("game-result.png", "state=result&seed=7&score=9", 1200),
]
DEMO_FRAMES = [400, 1100, 1800, 2500, 3200, 3900]


def browser_path():
    found = [path for path in BROWSERS if Path(path).exists()]
    return found[0] if found else ""


def game_url(query):
    return f"file:///{GAME.as_posix()}?{query}"


def shoot(url, target, budget, size="1200,760"):
    profile = tempfile.mkdtemp(prefix="shot-")
    command = [browser_path(), "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--user-data-dir={profile}", f"--window-size={size}", f"--virtual-time-budget={budget}", f"--screenshot={target}", url]
    subprocess.run(command, capture_output=True, check=False)
    return str(target)


def demo_frames():
    folder = tempfile.mkdtemp(prefix="frames-")
    paths = []
    for index, budget in enumerate(DEMO_FRAMES):
        paths.append(shoot(game_url("demo=1&seed=7"), Path(folder) / f"frame-{index + 1}.png", budget))
    return paths


def make_gif(paths, target, duration=650):
    try:
        from PIL import Image

        images = [Image.open(path).convert("RGB").resize((900, 570)) for path in paths]
        images[0].save(target, save_all=True, append_images=images[1:], duration=duration, loop=0, optimize=True)
        result = f"GIF: {target} ({target.stat().st_size // 1024} КБ)"
    except ImportError:
        result = "GIF не собран: pip install pillow"
    return result


def main(argv):
    OUT.mkdir(parents=True, exist_ok=True)
    shots = [shoot(game_url(query), OUT / name, budget) for name, query, budget in SHOTS]
    gif = make_gif(demo_frames(), OUT / "game-demo.gif")
    print("\n".join(shots))
    print(gif)
    return 0 if browser_path() else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
