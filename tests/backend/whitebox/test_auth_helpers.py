"""
Tests de caja blanca para helpers de autenticación
"""
from app.helpers import validate_username, validate_password_strength, hash_password, verify_password, normalize_username


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
    assert validate_password_strength("1234567890")[0] is True


def test_hash_and_verify_password():
    password = "clave_segura_123"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("otra_clave", hashed) is False
