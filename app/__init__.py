import os
from flask import Flask, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from .storage import MemoryStorage, SQLCipherStorage, SQLiteStorage
from .config import STORAGE_CONFIG, SESSION_CONFIG, HSTS_CONFIG

# Limiter sin límite por defecto; el límite se aplica solo a login/register en routes.py
limiter = Limiter(key_func=get_remote_address)


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

    # Rate limiting solo en login/register (3 por minuto por IP); ver decoradores en routes.py
    if os.environ.get("APP_TESTING") != "1":
        limiter.init_app(app)

    # Configurar CORS para permitir llamadas desde el frontend
    # En desarrollo, permite cualquier origen
    # En producción, deberías restringir a dominios específicos
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
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
            hsts_value = f"max-age={HSTS_CONFIG['max_age']}"
            if HSTS_CONFIG["include_subdomains"]:
                hsts_value += "; includeSubDomains"
            if HSTS_CONFIG["preload"]:
                hsts_value += "; preload"
            
            response.headers['Strict-Transport-Security'] = hsts_value
        
        return response

    # Inicializar supervisor después de todos los blueprints y hooks
    # para que capture todas las peticiones
    if os.environ.get("APP_SUPERVISOR") == "1":
        from .supervisor import init_supervisor
        init_supervisor(app)

    return app


