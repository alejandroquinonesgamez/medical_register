"""
Blueprint para las rutas de vistas (frontend)
Maneja las páginas HTML y la interfaz de usuario
"""
import os
from flask import render_template, Blueprint, abort, Response
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


# ─── Endpoints de prueba WAF (solo desarrollo) ─────────────────────────
# Estos endpoints simulan fugas de datos para verificar que el WAF
# (outbound filtering) bloquea la salida de información sensible.
# Solo disponibles cuando APP_SUPERVISOR=1 (desarrollo).

@views.route('/test/exfiltration/passwd')
def test_exfil_passwd():
    """Simula fuga de /etc/passwd en respuesta (WAF debe bloquear)"""
    if os.environ.get("APP_SUPERVISOR") != "1":
        abort(404)
    return Response(
        "root:x:0:0:root:/root:/bin/bash\n"
        "daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin\n"
        "bin:x:2:2:bin:/bin:/usr/sbin/nologin\n"
        "www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin\n",
        mimetype='text/plain',
    )


@views.route('/test/exfiltration/creditcard')
def test_exfil_creditcard():
    """Simula fuga de número de tarjeta de crédito (WAF debe bloquear)"""
    if os.environ.get("APP_SUPERVISOR") != "1":
        abort(404)
    return Response(
        '{"user": "admin", "card": "4539578763621486", "expiry": "12/28"}',
        mimetype='application/json',
    )


@views.route('/test/exfiltration/sqldump')
def test_exfil_sqldump():
    """Simula fuga de volcado de base de datos (WAF debe bloquear)"""
    if os.environ.get("APP_SUPERVISOR") != "1":
        abort(404)
    return Response(
        "-- mysqldump v5.7\n"
        "CREATE TABLE users (id INT, username VARCHAR(255), password_hash VARCHAR(255));\n"
        "INSERT INTO users VALUES (1, 'admin', '$argon2id$v=19$m=65536');\n",
        mimetype='text/plain',
    )


@views.route('/test/exfiltration/stacktrace')
def test_exfil_stacktrace():
    """Simula fuga de stack trace de Python (WAF debe bloquear)"""
    if os.environ.get("APP_SUPERVISOR") != "1":
        abort(404)
    return Response(
        "Traceback (most recent call last):\n"
        '  File "/app/routes.py", line 42, in index\n'
        "    result = db.execute(query)\n"
        "sqlite3.OperationalError: no such table: users\n",
        mimetype='text/plain',
    )

