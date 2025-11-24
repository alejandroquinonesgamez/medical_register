from flask import Flask
from flask_cors import CORS
from .storage import MemoryStorage


def create_app():
    app = Flask(__name__)
    app.storage = MemoryStorage()

    # Configurar CORS para permitir llamadas desde el frontend
    # En desarrollo, permite cualquier origen
    # En producción, deberías restringir a dominios específicos
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type"]
        }
    })

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
        return response

    return app


