from flask import Flask
from .storage import MemoryStorage


def create_app():
    app = Flask(__name__)
    app.storage = MemoryStorage()

    # Registrar blueprints
    from .views import views
    from .routes import api
    
    app.register_blueprint(views)
    app.register_blueprint(api)

    return app


