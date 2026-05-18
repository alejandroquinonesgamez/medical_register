#!/usr/bin/env python3
"""
Genera transcripciones tipo terminal + PNG para el informe MSTG (Play Integrity backend).
Usa Flask test_client (mismas rutas que en ejecución). Requiere Pillow.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent


def _fmt_response(status: int, headers: list[tuple[str, str]], body: str) -> str:
    reason = {
        200: "OK",
        204: "No Content",
        400: "Bad Request",
        403: "Forbidden",
        401: "Unauthorized",
        501: "Not Implemented",
    }.get(status, "")
    lines = [f"HTTP/1.1 {status} {reason}".strip()]
    for k, v in headers:
        if k.lower() in ("content-length", "set-cookie"):
            continue
        lines.append(f"{k}: {v}")
    lines.append("")
    if body:
        lines.append(body.rstrip())
    return "\n".join(lines)


def _to_png(txt_path: Path, png_path: Path) -> None:
    text = txt_path.read_text(encoding="utf-8")
    font_file = "/usr/share/fonts/liberation/LiberationMono-Regular.ttf"
    font_path = font_file if Path(font_file).is_file() else None
    size = 13
    try:
        font = ImageFont.truetype(font_path, size) if font_path else ImageFont.load_default()
    except OSError:
        font = ImageFont.load_default()

    wrap_w = 96
    lines_out: list[str] = []
    for line in text.splitlines():
        if len(line) <= wrap_w:
            lines_out.append(line)
        else:
            lines_out.extend(
                textwrap.wrap(line, width=wrap_w, break_long_words=True, replace_whitespace=False)
            )

    tmp_img = Image.new("RGB", (10, 10), "#1e1e1e")
    dr = ImageDraw.Draw(tmp_img)
    line_heights: list[int] = []
    max_w = 0
    for ln in lines_out:
        bbox = dr.textbbox((0, 0), ln, font=font)
        h = bbox[3] - bbox[1]
        w = bbox[2] - bbox[0]
        line_heights.append(max(h, size + 2))
        max_w = max(max_w, w)

    pad = 20
    img_w = max_w + 2 * pad
    img_h = sum(line_heights) + 2 * pad
    img = Image.new("RGB", (img_w, img_h), "#1e1e1e")
    draw = ImageDraw.Draw(img)
    y = pad
    for ln, h in zip(lines_out, line_heights, strict=True):
        draw.text((pad, y), ln, font=font, fill="#d4d4d4")
        y += h
    img.save(png_path, format="PNG")


def main() -> int:
    os.environ.setdefault("APP_TESTING", "1")
    os.environ.setdefault("STORAGE_BACKEND", "memory")
    os.environ.setdefault("RECAPTCHA_SECRET_KEY", "")

    sys.path.insert(0, str(ROOT))
    from app import create_app  # noqa: E402

    out_dir = Path(
        sys.argv[1]
        if len(sys.argv) > 1
        else ROOT.parent / "medical_register_android" / "docs" / "img" / "MSTG_RESILIENCE_20260430"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    blocks: list[tuple[str, str]] = []

    # 1) Desactivado
    os.environ.pop("PLAY_INTEGRITY_ENABLED", None)
    app = create_app()
    c = app.test_client()
    r = c.post("/api/integrity/verify", json={"integrity_token": "x", "nonce": "eA=="})
    blocks.append(
        (
            "EXTRA_BACKEND_PLAY_INTEGRITY_DISABLED",
            "\n".join(
                [
                    "# PLAY_INTEGRITY_ENABLED desactivado (respuesta esperada en dev sin Google)",
                    '$ curl -s -X POST "http://localhost:5001/api/integrity/verify" \\',
                    '  -H "Content-Type: application/json" \\',
                    '  -d \'{"integrity_token":"x","nonce":"eA=="}\'',
                    "",
                    _fmt_response(
                        r.status_code,
                        [(k, v) for k, v in r.headers if k.lower() != "content-length"],
                        json.dumps(r.get_json(), ensure_ascii=False, indent=2) if r.is_json else r.get_data(as_text=True),
                    ),
                ]
            ),
        )
    )

    # 2) Activado pero sin variables obligatorias -> 501
    os.environ["PLAY_INTEGRITY_ENABLED"] = "1"
    os.environ.pop("PLAY_INTEGRITY_PACKAGE_NAME", None)
    os.environ.pop("PLAY_INTEGRITY_SERVICE_ACCOUNT_JSON", None)
    app = create_app()
    c = app.test_client()
    r = c.post("/api/integrity/verify", json={"integrity_token": "x", "nonce": "eA=="})
    blocks.append(
        (
            "EXTRA_BACKEND_PLAY_INTEGRITY_501",
            "\n".join(
                [
                    "# Activado pero falta PACKAGE o JSON de cuenta de servicio -> 501",
                    '$ curl -i -X POST "http://localhost:5001/api/integrity/verify" \\',
                    '  -H "Content-Type: application/json" \\',
                    '  -d \'{"integrity_token":"x","nonce":"eA=="}\'',
                    "# (servidor con PLAY_INTEGRITY_ENABLED=1 sin PLAY_INTEGRITY_PACKAGE_NAME / SERVICE_ACCOUNT_JSON)",
                    "",
                    _fmt_response(
                        r.status_code,
                        [(k, v) for k, v in r.headers if k.lower() != "content-length"],
                        json.dumps(r.get_json(), ensure_ascii=False, indent=2) if r.is_json else r.get_data(as_text=True),
                    ),
                ]
            ),
        )
    )

    # 3) Variables presentes, token vacío -> FAIL (validación local antes de Google)
    os.environ["PLAY_INTEGRITY_PACKAGE_NAME"] = "com.alejandro.medicalregister"
    sa_dummy: str | None = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
            tmp.write("{}")
            sa_dummy = tmp.name
        os.environ["PLAY_INTEGRITY_SERVICE_ACCOUNT_JSON"] = sa_dummy
        app = create_app()
        c = app.test_client()
        r = c.post("/api/integrity/verify", json={"integrity_token": "", "nonce": "dGVzdG5vbmNl"})
        blocks.append(
            (
                "EXTRA_BACKEND_PLAY_INTEGRITY_FAIL_MISSING",
                "\n".join(
                    [
                        "# Token vacío: rechazo local (no llama a Google)",
                        '$ curl -s -X POST "http://localhost:5001/api/integrity/verify" \\',
                        '  -H "Content-Type: application/json" \\',
                        '  -d \'{"integrity_token":"","nonce":"dGVzdG5vbmNl"}\'',
                        "",
                        _fmt_response(
                            r.status_code,
                            [(k, v) for k, v in r.headers if k.lower() != "content-length"],
                            json.dumps(r.get_json(), ensure_ascii=False, indent=2)
                            if r.is_json
                            else r.get_data(as_text=True),
                        ),
                    ]
                ),
            )
        )
    finally:
        if sa_dummy:
            try:
                os.unlink(sa_dummy)
            except OSError:
                pass

    for base, text in blocks:
        txt_path = out_dir / f"{base}.txt"
        png_path = out_dir / f"{base}.png"
        txt_path.write_text(text + "\n", encoding="utf-8")
        _to_png(txt_path, png_path)
        print("Wrote", png_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
