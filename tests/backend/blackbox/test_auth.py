"""
Tests de caja negra para autenticación JWT y RBAC
"""
import json
import pytest
from tests.backend.conftest import (
    assert_success, assert_created, assert_bad_request,
    assert_unauthorized, assert_forbidden, auth_headers,
)


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
    assert data.get("access_token")

    access_token = data["access_token"]

    # Logout con access token
    resp = client.post('/api/auth/logout', headers=auth_headers(access_token))
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
    assert data.get("access_token")


def test_login_invalid_credentials(client):
    resp = client.post(
        '/api/auth/login',
        data=json.dumps({"username": "noexiste", "password": "clave_incorrecta"}),
        content_type='application/json'
    )
    assert_unauthorized(resp)


def test_logout_requires_auth(client):
    """Logout sin token de autenticación debe devolver 401"""
    resp = client.post('/api/auth/logout')
    assert_unauthorized(resp)


def test_auth_required_for_user_update(client):
    """POST /api/user sin access token debe devolver 401"""
    # Registrar usuario
    resp = client.post(
        '/api/auth/register',
        data=json.dumps({"username": "usuario3", "password": "clave_segura_123"}),
        content_type='application/json'
    )
    assert_created(resp)
    data = resp.get_json()
    access_token = data["access_token"]

    # Sin token -> 401
    resp = client.post('/api/user', json={
        "nombre": "Ana",
        "apellidos": "Prueba",
        "fecha_nacimiento": "1990-01-01",
        "talla_m": 1.70
    })
    assert_unauthorized(resp)

    # Con access token -> OK
    resp = client.post('/api/user', json={
        "nombre": "Ana",
        "apellidos": "Prueba",
        "fecha_nacimiento": "1990-01-01",
        "talla_m": 1.70
    }, headers=auth_headers(access_token))
    assert_success(resp)


def test_refresh_token_flow(client):
    """El refresh token (cookie) permite obtener un nuevo access token"""
    # Registrar usuario (establece refresh cookie)
    resp = client.post(
        '/api/auth/register',
        data=json.dumps({"username": "refresh_user", "password": "clave_segura_123"}),
        content_type='application/json'
    )
    assert_created(resp)

    # Llamar a refresh (la cookie se envía automáticamente por el test client)
    resp = client.post('/api/auth/refresh')
    assert_success(resp)
    data = resp.get_json()
    assert data.get("access_token")
    assert data.get("user_id")
    assert data.get("username") == "refresh_user"


def test_refresh_without_cookie(client):
    """Refresh sin cookie debe devolver 401"""
    resp = client.post('/api/auth/refresh')
    assert_unauthorized(resp)


def test_me_endpoint(client):
    """GET /api/auth/me devuelve datos del usuario autenticado"""
    resp = client.post(
        '/api/auth/register',
        data=json.dumps({"username": "me_user", "password": "clave_segura_123"}),
        content_type='application/json'
    )
    assert_created(resp)
    data = resp.get_json()
    access_token = data["access_token"]

    resp = client.get('/api/auth/me', headers=auth_headers(access_token))
    assert_success(resp)
    me_data = resp.get_json()
    assert me_data["username"] == "me_user"
    assert me_data["user_id"] == data["user_id"]


def test_me_without_auth(client):
    """GET /api/auth/me sin token devuelve 401"""
    resp = client.get('/api/auth/me')
    assert_unauthorized(resp)


## ─── Tests RBAC ───────────────────────────────────────────────────────────────

def test_first_user_is_admin(client):
    """El primer usuario registrado recibe rol 'admin'"""
    resp = client.post(
        '/api/auth/register',
        data=json.dumps({"username": "admin_user", "password": "clave_segura_123"}),
        content_type='application/json'
    )
    assert_created(resp)
    data = resp.get_json()
    assert data["role"] == "admin"


def test_second_user_is_regular(client):
    """El segundo usuario registrado recibe rol 'user'"""
    # Primer usuario (admin)
    client.post(
        '/api/auth/register',
        data=json.dumps({"username": "first_admin", "password": "clave_segura_123"}),
        content_type='application/json'
    )
    # Segundo usuario (user)
    resp = client.post(
        '/api/auth/register',
        data=json.dumps({"username": "second_user", "password": "clave_segura_123"}),
        content_type='application/json'
    )
    assert_created(resp)
    data = resp.get_json()
    assert data["role"] == "user"


def test_role_in_jwt_and_me(client):
    """El rol se incluye en el JWT y se devuelve en /api/auth/me"""
    resp = client.post(
        '/api/auth/register',
        data=json.dumps({"username": "role_test", "password": "clave_segura_123"}),
        content_type='application/json'
    )
    data = resp.get_json()
    token = data["access_token"]

    resp = client.get('/api/auth/me', headers=auth_headers(token))
    assert_success(resp)
    me_data = resp.get_json()
    assert me_data["role"] == "admin"


def test_admin_can_change_user_role(auth_session, regular_user_session):
    """Un admin puede cambiar el rol de otro usuario"""
    client = auth_session["client"]
    admin_token = auth_session["access_token"]
    target_id = regular_user_session["user_id"]

    # Promover a admin
    resp = client.put(
        f'/api/admin/users/{target_id}/role',
        json={"role": "admin"},
        headers=auth_headers(admin_token)
    )
    assert_success(resp)
    data = resp.get_json()
    assert data["role"] == "admin"


def test_regular_user_cannot_change_roles(auth_session, regular_user_session):
    """Un usuario regular NO puede cambiar roles (403)"""
    client = auth_session["client"]
    user_token = regular_user_session["access_token"]
    admin_id = auth_session["user_id"]

    resp = client.put(
        f'/api/admin/users/{admin_id}/role',
        json={"role": "user"},
        headers=auth_headers(user_token)
    )
    assert_forbidden(resp)


def test_admin_cannot_demote_self(auth_session):
    """Un admin no puede degradar su propio rol"""
    client = auth_session["client"]
    admin_token = auth_session["access_token"]
    admin_id = auth_session["user_id"]

    resp = client.put(
        f'/api/admin/users/{admin_id}/role',
        json={"role": "user"},
        headers=auth_headers(admin_token)
    )
    assert_bad_request(resp)


def test_admin_route_blocked_for_regular_user(auth_session, regular_user_session):
    """Las rutas protegidas con require_role('admin') devuelven 403 para usuarios regulares"""
    client = auth_session["client"]
    user_token = regular_user_session["access_token"]

    # /api/wstg/status es solo para admin
    resp = client.get('/api/wstg/status', headers=auth_headers(user_token))
    assert_forbidden(resp)


def test_role_included_in_refresh(client):
    """El refresh token devuelve el rol correcto"""
    resp = client.post(
        '/api/auth/register',
        data=json.dumps({"username": "refresh_role", "password": "clave_segura_123"}),
        content_type='application/json'
    )
    assert_created(resp)

    resp = client.post('/api/auth/refresh')
    assert_success(resp)
    data = resp.get_json()
    assert data.get("role") == "admin"


## ─── Tests rehasheo ──────────────────────────────────────────────────────────

def test_login_rehashes_when_cost_config_changed(client, monkeypatch):
    """Al hacer login, si el coste de Argon2 ha cambiado, se rehashea y actualiza el hash en BD."""
    import app.config as config
    from app.helpers import verify_password

    # Registrar con coste por defecto (p. ej. 3)
    resp = client.post(
        '/api/auth/register',
        data=json.dumps({"username": "migrate_user", "password": "clave_segura_123"}),
        content_type='application/json'
    )
    assert_created(resp)
    app_flask = client.application
    storage = app_flask.storage
    user_before = storage.get_auth_user_by_username("migrate_user")
    assert user_before is not None
    hash_antes = user_before.password_hash

    # Cambiar coste en configuración (simula cambio posterior)
    orig_cost = config.PASSWORD_HASH_CONFIG["time_cost"]
    monkeypatch.setitem(config.PASSWORD_HASH_CONFIG, "time_cost", 4)

    # Login: debe verificar con hash antiguo y guardar hash nuevo (mismo coste, salt nuevo)
    resp = client.post(
        '/api/auth/login',
        data=json.dumps({"username": "migrate_user", "password": "clave_segura_123"}),
        content_type='application/json'
    )
    assert_success(resp)

    user_despues = storage.get_auth_user_by_username("migrate_user")
    # El hash guardado debe verificar con la contraseña y ser distinto del anterior (rehasheo con config actual)
    assert verify_password("clave_segura_123", user_despues.password_hash)
    assert user_despues.password_hash != hash_antes
    monkeypatch.setitem(config.PASSWORD_HASH_CONFIG, "time_cost", orig_cost)
