import os
from flask import Flask, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from .storage import MemoryStorage, SQLCipherStorage, SQLiteStorage
from .config import STORAGE_CONFIG, SESSION_CONFIG


def create_app():
    app = Flask(__name__)

    # Configurar secreto de sesión
    app.secret_key = os.environ.get("FLASK_SECRET_KEY") or os.urandom(32)
    app.config["SESSION_COOKIE_HTTPONLY"] = SESSION_CONFIG["cookie_httponly"]
    app.config["SESSION_COOKIE_SECURE"] = SESSION_CONFIG["cookie_secure"]
    app.config["SESSION_COOKIE_SAMESITE"] = SESSION_CONFIG["cookie_samesite"]

    # Configurar almacenamiento
    if STORAGE_CONFIG["backend"] == "sqlcipher":
        app.storage = SQLCipherStorage(
            db_path=STORAGE_CONFIG["db_path"],
            db_key=STORAGE_CONFIG["db_key"],
        )
    elif STORAGE_CONFIG["backend"] == "sqlite":
        app.storage = SQLiteStorage(
            db_path=STORAGE_CONFIG["db_path"],
        )
    else:
        app.storage = MemoryStorage()

    # Rate limiting global: 3 intentos por IP por minuto
    if os.environ.get("APP_TESTING") != "1":
        Limiter(
            get_remote_address,
            app=app,
            default_limits=["3 per minute"],
        )

    # Configurar CORS para permitir llamadas desde el frontend
    # En desarrollo, permite cualquier origen
    # En producción, deberías restringir a dominios específicos
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "X-CSRF-Token"]
        }
    }, supports_credentials=True)

    # Registrar blueprints
    from .views import views
    from .routes import api
    
    app.register_blueprint(views)
    app.register_blueprint(api)

    # Agregar headers de seguridad para prevenir clickjacking y otros ataques
    @app.after_request
    def set_security_headers(response):
        """Agrega headers de seguridad a todas las respuestas"""
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Content-Security-Policy'] = "frame-ancestors 'none'"
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Strict-Transport-Security (HSTS)
        # Solo se envía si SESSION_COOKIE_SECURE está activo (indica uso de HTTPS)
        # o si se detecta que la petición viene por HTTPS
        if SESSION_CONFIG["cookie_secure"] or request.is_secure:
            # max-age: 31536000 = 1 año (recomendado para producción)
            # includeSubDomains: incluir subdominios
            # preload: permitir inclusión en listas de preload de navegadores
            hsts_max_age = int(os.environ.get("HSTS_MAX_AGE", "31536000"))
            hsts_include_subdomains = os.environ.get("HSTS_INCLUDE_SUBDOMAINS", "true").lower() == "true"
            hsts_preload = os.environ.get("HSTS_PRELOAD", "false").lower() == "true"
            
            hsts_value = f"max-age={hsts_max_age}"
            if hsts_include_subdomains:
                hsts_value += "; includeSubDomains"
            if hsts_preload:
                hsts_value += "; preload"
            
            response.headers['Strict-Transport-Security'] = hsts_value
        
        return response

    return app


