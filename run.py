"""
Script principal para ejecutar la aplicación Flask en modo desarrollo.

Este script crea la instancia de la aplicación Flask y la ejecuta
usando el servidor de desarrollo integrado de Flask.

La configuración del servidor (host, puerto) se obtiene de app.config.SERVER_CONFIG.
Por defecto, la aplicación corre en http://localhost:5001.

En producción, se debe usar un servidor WSGI como Gunicorn o uWSGI.
"""
from app import create_app
from app.config import SERVER_CONFIG

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host=SERVER_CONFIG["host"], port=SERVER_CONFIG["port"])


