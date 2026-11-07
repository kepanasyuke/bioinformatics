"""Снимает скриншоты страницы покрытия через headless Chrome.

Запуск: python tools/shoot_coverage.py
Картинки кладутся в docs/img и вставляются в README.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.shoot_game import browser_path, shoot

PAGE = ROOT / "docs" / "coverage.html"
OUT = ROOT / "docs" / "img"
SHOTS = [("coverage-top.png", "1400,1000"), ("coverage-full.png", "1400,1900")]


def page_url():
    return f"file:///{PAGE.as_posix()}"


def main(argv):
    OUT.mkdir(parents=True, exist_ok=True)
    shots = [shoot(page_url(), OUT / name, 1500, size) for name, size in SHOTS]
    print("\n".join(shots))
    return 0 if browser_path() else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
