#!/usr/bin/env python3
"""
Genera texto tipo terminal + PNG para docs (device risk) usando test_client.
Dependencia: Pillow (`pip install Pillow` en el venv del monorepo Flask).
"""
from __future__ import annotations

import os
import sys
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Raíz del monorepo Flask
ROOT = Path(__file__).resolve().parent.parent

FP = "a" * 64


def _fmt_response(status: int, headers: list[tuple[str, str]], body: str) -> str:
    reason = {200: "OK", 204: "No Content", 400: "Bad Request", 403: "Forbidden", 401: "Unauthorized"}.get(
        status, ""
    )
    first = f"HTTP/1.1 {status} {reason}".strip()
    lines = [first]
    for k, v in headers:
        if k.lower() in ("content-length", "set-cookie"):
            continue
        lines.append(f"{k}: {v}")
    lines.append("")
    if body:
        lines.append(body.rstrip())
    return "\n".join(lines)


def main() -> int:
    os.environ.setdefault("APP_TESTING", "1")
    os.environ.setdefault("STORAGE_BACKEND", "memory")
    os.environ.setdefault("RECAPTCHA_SECRET_KEY", "")
    os.environ.setdefault("HIBP_FAIL_CLOSED", "false")

    sys.path.insert(0, str(ROOT))
    from app import create_app  # noqa: E402

    app = create_app()
    c = app.test_client()

    reg = c.post(
        "/api/auth/register",
        json={"username": "devrisk_doc", "password": "Xk9$mNp2!qLzDoc99", "recaptcha_token": ""},
    )
    if reg.status_code not in (201, 400):
        print("register unexpected:", reg.status_code, reg.get_data(as_text=True), file=sys.stderr)
        return 1
    if reg.status_code == 400 and "ya existe" not in reg.get_data(as_text=True).lower():
        # usuario duplicado en memoria de un run anterior no aplica; cada run es proceso nuevo
        pass

    login = c.post(
        "/api/auth/login",
        json={"username": "devrisk_doc", "password": "Xk9$mNp2!qLzDoc99", "recaptcha_token": ""},
    )
    if login.status_code != 200:
        print("login failed:", login.status_code, login.get_data(as_text=True), file=sys.stderr)
        return 1
    token = login.get_json()["access_token"]

    r200 = c.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}", "X-Device-Fingerprint": FP},
    )
    block = c.post("/api/security/report", json={"fingerprint": FP, "reason": "root"})
    r403 = c.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}", "X-Device-Fingerprint": FP},
    )

    hdr200 = [(k, v) for k, v in r200.headers if k.lower() != "content-length"]
    hdr403 = [(k, v) for k, v in r403.headers if k.lower() != "content-length"]
    hdr204 = [(k, v) for k, v in block.headers if k.lower() != "content-length"]

    body200 = r200.get_data(as_text=True)
    body403 = r403.get_data(as_text=True)
    body204 = block.get_data(as_text=True)

    text200 = "\n".join(
        [
            "# Device risk — /api/auth/me antes de marcar la huella (test_client Flask, rutas reales)",
            f'$ curl -i "http://localhost:5001/api/auth/me" \\',
            f'  -H "Authorization: Bearer <ACCESS_TOKEN>" \\',
            f'  -H "X-Device-Fingerprint: {FP}"',
            "",
            _fmt_response(r200.status_code, hdr200, body200),
        ]
    )

    text403 = "\n".join(
        [
            "# Tras: POST /api/security/report con la misma huella",
            f'$ curl -i -X POST "http://localhost:5001/api/security/report" \\',
            '  -H "Content-Type: application/json" \\',
            f'  -d \'{{"fingerprint":"{FP}","reason":"root"}}\'',
            "",
            _fmt_response(block.status_code, hdr204, body204),
            "",
            f'$ curl -i "http://localhost:5001/api/auth/me" \\',
            f'  -H "Authorization: Bearer <ACCESS_TOKEN>" \\',
            f'  -H "X-Device-Fingerprint: {FP}"',
            "",
            _fmt_response(r403.status_code, hdr403, body403),
        ]
    )

    out_dir = Path(
        sys.argv[1]
        if len(sys.argv) > 1
        else ROOT.parent / "medical_register_android" / "docs" / "img" / "MSTG_RESILIENCE_20260430"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    p200 = out_dir / "EXTRA_DEVICE_RISK_200_BEFORE.txt"
    p403 = out_dir / "EXTRA_DEVICE_RISK_403_BLOCKED.txt"
    p200.write_text(text200 + "\n", encoding="utf-8")
    p403.write_text(text403 + "\n", encoding="utf-8")

    def to_png(txt_path: Path, png_path: Path) -> None:
        text = txt_path.read_text(encoding="utf-8")
        font_paths = [
            "/usr/share/fonts/liberation/LiberationMono-Regular.ttf",
        ]
        font_file = next((p for p in font_paths if Path(p).is_file()), None)
        size = 13
        try:
            font = ImageFont.truetype(font_file, size) if font_file else ImageFont.load_default()
        except OSError:
            font = ImageFont.load_default()

        wrap_w = 96
        lines_out: list[str] = []
        for line in text.splitlines():
            if len(line) <= wrap_w:
                lines_out.append(line)
            else:
                lines_out.extend(textwrap.wrap(line, width=wrap_w, break_long_words=True, replace_whitespace=False))

        tmp_img = Image.new("RGB", (10, 10), "#1e1e1e")
        dr = ImageDraw.Draw(tmp_img)
        line_heights = []
        max_w = 0
        for ln in lines_out:
            bbox = dr.textbbox((0, 0), ln, font=font)
            h = bbox[3] - bbox[1]
            w = bbox[2] - bbox[0]
            line_heights.append(max(h, size + 2))
            max_w = max(max_w, w)

        pad = 20
        lh = max(line_heights) if line_heights else size + 4
        img_w = max_w + 2 * pad
        img_h = sum(line_heights) + 2 * pad
        img = Image.new("RGB", (img_w, img_h), "#1e1e1e")
        draw = ImageDraw.Draw(img)
        y = pad
        for ln, h in zip(lines_out, line_heights, strict=True):
            draw.text((pad, y), ln, font=font, fill="#d4d4d4")
            y += h
        img.save(png_path, format="PNG")

    png200 = out_dir / "EXTRA_DEVICE_RISK_200_BEFORE.png"
    png403 = out_dir / "EXTRA_DEVICE_RISK_403_BLOCKED.png"
    to_png(p200, png200)
    to_png(p403, png403)

    print("Wrote:", png200, png403, sep="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
