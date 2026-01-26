"""
Script principal para ejecutar la aplicación Flask.

Este script crea la instancia de la aplicación Flask y la ejecuta
usando el servidor de desarrollo integrado de Flask.

La configuración del servidor (host, puerto) se obtiene de app.config.SERVER_CONFIG.
Por defecto, la aplicación corre en http://localhost:5001.

En producción, se debe usar un servidor WSGI como Gunicorn o uWSGI.
"""
from app import create_app
from app.config import SERVER_CONFIG
import os

app = create_app()

if __name__ == '__main__':
    # En producción, debug debe estar desactivado
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug_mode, host=SERVER_CONFIG["host"], port=SERVER_CONFIG["port"])


