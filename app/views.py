"""
Blueprint para las rutas de vistas (frontend)
Maneja las páginas HTML y la interfaz de usuario
"""
import os
from flask import render_template, Blueprint, abort
from .translations import HTML_TEXTS
from .config import ACTIVE_LANGUAGE, AVAILABLE_LANGUAGES, STORAGE_CONFIG

views = Blueprint('views', __name__)


@views.route('/')
def index():
    """Página principal de la aplicación"""
    return render_template(
        'index.html',
        html_texts=HTML_TEXTS,
        active_language=ACTIVE_LANGUAGE,
        available_languages=AVAILABLE_LANGUAGES,
        storage_backend=STORAGE_CONFIG["backend"],
        sqlcipher_requires_pepper=(STORAGE_CONFIG["backend"] == "sqlcipher"),
        supervisor_enabled=os.environ.get("APP_SUPERVISOR") == "1",
    )


@views.route('/supervisor')
def supervisor():
    if os.environ.get("APP_SUPERVISOR") != "1":
        abort(404)
    return render_template(
        'supervisor.html',
        active_language=ACTIVE_LANGUAGE,
    )


@views.route('/defectdojo')
def defectdojo_redirect():
    """Redirige a DefectDojo"""
    from flask import redirect
    return redirect('http://localhost:8080', code=302)

