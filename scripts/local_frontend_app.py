"""
Servidor local solo-frontend para modo desarrollo.
Renderiza la plantilla principal y fuerza modo offline en el frontend.
"""
import os
from pathlib import Path

from flask import Flask, render_template, jsonify

from app.translations import HTML_TEXTS
from app.config import ACTIVE_LANGUAGE, AVAILABLE_LANGUAGES, STORAGE_CONFIG


BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "app" / "templates"
STATIC_DIR = BASE_DIR / "app" / "static"

app = Flask(
    __name__,
    template_folder=str(TEMPLATES_DIR),
    static_folder=str(STATIC_DIR),
)


@app.route("/")
def index():
    return render_template(
        "index.html",
        html_texts=HTML_TEXTS,
        active_language=ACTIVE_LANGUAGE,
        available_languages=AVAILABLE_LANGUAGES,
        storage_backend=STORAGE_CONFIG["backend"],
        sqlcipher_requires_pepper=(STORAGE_CONFIG["backend"] == "sqlcipher"),
        offline_mode=True,
    )


@app.route("/api/<path:_>")
def api_unavailable(_):
    return jsonify({"error": "API no disponible en modo local"}), 503


if __name__ == "__main__":
    port = int(os.environ.get("FRONTEND_PORT", "5001"))
    app.run(host="0.0.0.0", port=port, debug=False)
