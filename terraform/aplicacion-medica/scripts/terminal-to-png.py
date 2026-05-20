#!/usr/bin/env python3
"""Renderiza salida de terminal (texto plano) a PNG estilo consola."""
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("pip install pillow")

BG = (30, 30, 30)
FG = (220, 220, 220)
GREEN = (80, 200, 120)
YELLOW = (230, 200, 80)
RED = (230, 100, 100)
PAD = 24
LINE_H = 18
FONT_SIZE = 14
MAX_W = 1100


def load_font():
    for name in (
        "DejaVuSansMono.ttf",
        "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
        "/usr/share/fonts/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/liberation/LiberationMono-Regular.ttf",
    ):
        p = Path(name)
        if p.is_file() or Path("/usr/share/fonts").joinpath(name).is_file():
            try:
                return ImageFont.truetype(str(p) if p.is_file() else name, FONT_SIZE)
            except OSError:
                pass
    return ImageFont.load_default()


def color_line(line: str):
    lo = line.lower()
    if "success" in lo or "ok" in lo or "http:200" in lo:
        return GREEN
    if "failed" in lo or "unreachable" in lo or "fatal" in lo:
        return RED
    if "changed=" in lo or "recap" in lo or "play" in lo:
        return YELLOW
    return FG


def main():
    if len(sys.argv) < 3:
        print(f"Uso: {sys.argv[0]} <entrada.txt> <salida.png>", file=sys.stderr)
        sys.exit(1)
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    lines = src.read_text(encoding="utf-8", errors="replace").splitlines()
    if not lines:
        lines = ["(vacío)"]
    font = load_font()
    w = min(MAX_W, max(400, max(len(l) for l in lines) * 8 + PAD * 2))
    h = PAD * 2 + len(lines) * LINE_H
    img = Image.new("RGB", (w, h), BG)
    draw = ImageDraw.Draw(img)
    y = PAD
    for line in lines:
        draw.text((PAD, y), line[:200], fill=color_line(line), font=font)
        y += LINE_H
    dst.parent.mkdir(parents=True, exist_ok=True)
    img.save(dst)
    print(dst, w, h)


if __name__ == "__main__":
    main()
