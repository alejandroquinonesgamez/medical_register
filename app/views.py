"""
Blueprint para las rutas de vistas (frontend)
Maneja las páginas HTML y la interfaz de usuario
"""
from flask import render_template, Blueprint
from .translations import HTML_TEXTS
from .config import ACTIVE_LANGUAGE, AVAILABLE_LANGUAGES

views = Blueprint('views', __name__)


@views.route('/')
def index():
    """Página principal de la aplicación"""
    return render_template('index.html', 
                         html_texts=HTML_TEXTS, 
                         active_language=ACTIVE_LANGUAGE,
                         available_languages=AVAILABLE_LANGUAGES)

