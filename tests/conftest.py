"""
Configuración de pytest y fixtures compartidas
"""
import pytest
from datetime import datetime, date
from app.storage import UserData, WeightEntryData


# Helpers para hacer los tests más legibles
def assert_success(response):
    """Verifica que la respuesta sea exitosa (200 OK)"""
    assert response.status_code == 200, f"Esperado 200 OK, obtenido {response.status_code}: {response.get_data(as_text=True)}"


def assert_created(response):
    """Verifica que el recurso fue creado (201 Created)"""
    assert response.status_code == 201, f"Esperado 201 Created, obtenido {response.status_code}: {response.get_data(as_text=True)}"


def assert_bad_request(response):
    """Verifica que la respuesta sea un error de petición inválida (400 Bad Request)"""
    assert response.status_code == 400, f"Esperado 400 Bad Request, obtenido {response.status_code}: {response.get_data(as_text=True)}"


def assert_not_found(response):
    """Verifica que el recurso no fue encontrado (404 Not Found)"""
    assert response.status_code == 404, f"Esperado 404 Not Found, obtenido {response.status_code}: {response.get_data(as_text=True)}"


@pytest.fixture
def app():
    """Crea una aplicación Flask para testing con almacenamiento en memoria"""
    from app import create_app
    
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    yield app


@pytest.fixture
def client(app):
    """Cliente de prueba para hacer requests HTTP"""
    return app.test_client()


@pytest.fixture
def sample_user(app):
    """Crea un usuario de prueba usando el storage"""
    with app.app_context():
        user = UserData(
            user_id=1,
            first_name="Juan",
            last_name="Pérez García",
            birth_date=date(1990, 5, 15),
            height_m=1.75
        )
        app.storage.save_user(user)
        return user


@pytest.fixture
def sample_weights(app, sample_user):
    """Crea varios registros de peso de prueba usando el storage"""
    with app.app_context():
        weights = [
            WeightEntryData(entry_id=0, user_id=1, weight_kg=70.0, recorded_date=datetime(2024, 1, 1, 10, 0)),
            WeightEntryData(entry_id=0, user_id=1, weight_kg=72.5, recorded_date=datetime(2024, 1, 15, 10, 0)),
            WeightEntryData(entry_id=0, user_id=1, weight_kg=75.0, recorded_date=datetime(2024, 2, 1, 10, 0)),
        ]
        for weight in weights:
            app.storage.add_weight_entry(weight)
        return weights

