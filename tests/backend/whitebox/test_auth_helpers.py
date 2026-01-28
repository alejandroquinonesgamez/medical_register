"""
Tests de caja blanca para helpers de autenticación
"""
from app.helpers import validate_username, validate_password_strength, hash_password, verify_password, normalize_username
import app.helpers as helpers


def test_validate_username_rules():
    assert validate_username("usuario_ok")[0] is True
    assert validate_username("UsUARIO.OK")[0] is True
    assert validate_username("no")[0] is False
    assert validate_username("usuario con espacios")[0] is False
    assert validate_username("usuario!*")[0] is False


def test_normalize_username():
    assert normalize_username("  UsEr  ") == "user"


def test_password_strength():
    assert validate_password_strength("")[0] is False
    assert validate_password_strength("123456789")[0] is False
    assert validate_password_strength("clave_segura_123")[0] is True


def test_common_password_blocking(monkeypatch):
    monkeypatch.setattr(helpers, "is_common_password", lambda _: True)
    assert validate_password_strength("password123")[0] is False


def test_pwned_password_blocking(monkeypatch):
    monkeypatch.setattr(helpers, "is_pwned_password", lambda _: True)
    assert validate_password_strength("password123")[0] is False


def test_top10k_fallback(monkeypatch):
    monkeypatch.setattr(helpers, "is_common_password_fallback", lambda _: True)
    assert validate_password_strength("password123")[0] is False


def test_hash_and_verify_password():
    password = "clave_segura_123"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("otra_clave", hashed) is False


def test_hash_uses_pepper(monkeypatch):
    monkeypatch.setattr(helpers, "PASSWORD_PEPPER", "pepper_test")
    hashed = helpers.hash_password("clave_segura_123")
    assert helpers.verify_password("clave_segura_123", hashed) is True
    monkeypatch.setattr(helpers, "PASSWORD_PEPPER", "pepper_diferente")
    assert helpers.verify_password("clave_segura_123", hashed) is False


def test_different_cost_produces_different_hash_verify_still_works(monkeypatch):
    """Distinto coste produce distinto hash; verify acepta hashes antiguos (rehash en login)."""
    import app.config as config
    password = "clave_segura_123"
    orig = config.PASSWORD_HASH_CONFIG.copy()
    monkeypatch.setitem(config.PASSWORD_HASH_CONFIG, "time_cost", 2)
    hash_coste_2 = hash_password(password)
    monkeypatch.setitem(config.PASSWORD_HASH_CONFIG, "time_cost", 3)
    hash_coste_3 = hash_password(password)
    assert hash_coste_2 != hash_coste_3
    assert verify_password(password, hash_coste_2) is True
    assert verify_password(password, hash_coste_3) is True
    monkeypatch.setitem(config.PASSWORD_HASH_CONFIG, "time_cost", orig["time_cost"])
