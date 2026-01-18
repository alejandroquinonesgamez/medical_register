"""
Tests de caja negra para autenticación y CSRF
"""
import json
from tests.backend.conftest import assert_success, assert_created, assert_bad_request, assert_unauthorized, assert_forbidden


def test_register_login_logout_flow(client):
    # Registro
    resp = client.post(
        '/api/auth/register',
        data=json.dumps({"username": "usuario1", "password": "clave_segura_123"}),
        content_type='application/json'
    )
    assert_created(resp)
    data = resp.get_json()
    assert data["username"] == "usuario1"
    assert data.get("csrf_token")

    # Logout con CSRF
    resp = client.post('/api/auth/logout', headers={"X-CSRF-Token": data["csrf_token"]})
    assert_success(resp)

    # Login
    resp = client.post(
        '/api/auth/login',
        data=json.dumps({"username": "usuario1", "password": "clave_segura_123"}),
        content_type='application/json'
    )
    assert_success(resp)
    data = resp.get_json()
    assert data["username"] == "usuario1"
    assert data.get("csrf_token")


def test_login_invalid_credentials(client):
    resp = client.post(
        '/api/auth/login',
        data=json.dumps({"username": "noexiste", "password": "clave_incorrecta"}),
        content_type='application/json'
    )
    assert_unauthorized(resp)


def test_logout_requires_csrf(client):
    # Registrar para tener sesión
    resp = client.post(
        '/api/auth/register',
        data=json.dumps({"username": "usuario2", "password": "clave_segura_123"}),
        content_type='application/json'
    )
    assert_created(resp)

    resp = client.post('/api/auth/logout')
    assert_forbidden(resp)


def test_csrf_required_for_user_update(client):
    # Registrar y obtener csrf
    resp = client.post(
        '/api/auth/register',
        data=json.dumps({"username": "usuario3", "password": "clave_segura_123"}),
        content_type='application/json'
    )
    assert_created(resp)
    data = resp.get_json()

    # Sin CSRF -> 403
    resp = client.post('/api/user', json={
        "nombre": "Ana",
        "apellidos": "Prueba",
        "fecha_nacimiento": "1990-01-01",
        "talla_m": 1.70
    })
    assert_forbidden(resp)

    # Con CSRF -> OK
    resp = client.post('/api/user', json={
        "nombre": "Ana",
        "apellidos": "Prueba",
        "fecha_nacimiento": "1990-01-01",
        "talla_m": 1.70
    }, headers={"X-CSRF-Token": data["csrf_token"]})
    assert_success(resp)
