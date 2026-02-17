"""
Archivo de configuración de la aplicación

Centraliza todos los valores de configuración y constantes de la aplicación:
- Límites de validación para altura, peso, nombres y fechas
- Configuración del servidor (host, puerto)
- Configuración de idioma (actualmente solo español)
- ID de usuario (aplicación monousuario, USER_ID = 1)

Estos valores se sincronizan con el frontend mediante el endpoint /api/config
y se usan para validaciones tanto en backend como frontend.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Cargar .env del proyecto (raíz del repo) para tener RECAPTCHA_*, etc. sin depender de Docker
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

from datetime import datetime, timedelta

# Configuración de usuario (monousuario legado)
USER_ID = 1

# Configuración de autenticación
AUTH_CONFIG = {
    "username_min_length": 3,
    "username_max_length": 30,
    "password_min_length": 10,
}

# Ruta a lista de contraseñas comunes (RockYou u otra)
COMMON_PASSWORDS_PATH = os.environ.get(
    "COMMON_PASSWORDS_PATH",
    os.path.join(os.getcwd(), "data", "rockyou.txt"),
)

# HIBP (Pwned Passwords) - K-anonymity
HIBP_API_URL = os.environ.get(
    "HIBP_API_URL",
    "https://api.pwnedpasswords.com/range/",
)
HIBP_TIMEOUT_SECONDS = float(os.environ.get("HIBP_TIMEOUT_SECONDS", "2.5"))
HIBP_FAIL_CLOSED = os.environ.get("HIBP_FAIL_CLOSED", "true").lower() == "true"

# reCAPTCHA v3 (login y register).
# - Se configura mediante variables de entorno (idealmente desde un archivo `.env` local NO versionado).
# - Si NO se configuran, NO se exigirá token (útil para desarrollo/tests).
RECAPTCHA_SECRET_KEY = os.environ.get("RECAPTCHA_SECRET_KEY", "").strip()
RECAPTCHA_SITE_KEY = os.environ.get("RECAPTCHA_SITE_KEY", "").strip()
RECAPTCHA_MIN_SCORE = float(os.environ.get("RECAPTCHA_MIN_SCORE", "0.5"))
RECAPTCHA_VERIFY_URL = os.environ.get(
    "RECAPTCHA_VERIFY_URL",
    "https://www.google.com/recaptcha/api/siteverify",
)

# Fallback local de contraseñas comunes (ruta local)
COMMON_PASSWORDS_FALLBACK_PATH = os.environ.get(
    "COMMON_PASSWORDS_FALLBACK_PATH",
    os.path.join(os.getcwd(), "data", "common_passwords_fallback.txt"),
)

# Configuración de hash de contraseñas (Argon2id)
# Parámetros (ver https://argon2-cffi.readthedocs.io/):
#   time_cost: nº de iteraciones sobre la memoria. Mayor = más lento y más resistencia a fuerza bruta. Típico 2–4 para login.
#   parallelism: nº de hilos/lanes en paralelo. Suele usarse 1–4 según CPU.
#   hash_len: longitud del hash de salida en bytes (32 = 256 bits). Estándar para derivación de claves.
#   salt_len: longitud del salt aleatorio en bytes (16 = 128 bits). Un salt distinto por contraseña evita tablas arcoíris.
PASSWORD_HASH_CONFIG = {
    "time_cost": 3,
    "memory_cost": 65536,
    "parallelism": 2,
    "hash_len": 32,
    "salt_len": 16,
}

# Pepper (solo servidor)
PASSWORD_PEPPER = os.environ.get("PASSWORD_PEPPER", "")

# Configuración de sesión (legado, mantenido para cookie del refresh token)
SESSION_CONFIG = {
    "cookie_samesite": "Lax",
    "cookie_secure": os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true",
    "cookie_httponly": True,
}

# Configuración JWT (JSON Web Tokens)
# - JWT_SECRET_KEY: secreto para firmar tokens. DEBE ser único y seguro en producción.
#   Si no se define, se genera uno aleatorio al arrancar (tokens invalidados al reiniciar).
# - Access token (corta vida): se envía en Authorization: Bearer y se almacena solo en
#   memoria del cliente (no en localStorage) para mitigar XSS.
# - Refresh token (larga vida): se envía como cookie HttpOnly (no accesible desde JS).
JWT_CONFIG = {
    "secret_key": os.environ.get("JWT_SECRET_KEY", ""),
    "algorithm": "HS256",
    "access_token_expires": timedelta(
        minutes=int(os.environ.get("JWT_ACCESS_TOKEN_MINUTES", "15"))
    ),
    "refresh_token_expires": timedelta(
        days=int(os.environ.get("JWT_REFRESH_TOKEN_DAYS", "7"))
    ),
    "refresh_cookie_name": "refresh_token",
    "refresh_cookie_path": "/api/auth",
}

# Configuración de HSTS (Strict-Transport-Security)
HSTS_CONFIG = {
    "max_age": int(os.environ.get("HSTS_MAX_AGE", "31536000")),  # 1 año por defecto
    "include_subdomains": os.environ.get("HSTS_INCLUDE_SUBDOMAINS", "true").lower() == "true",
    "preload": os.environ.get("HSTS_PRELOAD", "false").lower() == "true",
}

# Configuración de almacenamiento (memory / sqlite / sqlcipher)
_storage_backend = os.environ.get("STORAGE_BACKEND", "sqlite").strip().lower()
if _storage_backend not in {"memory", "sqlite", "sqlcipher"}:
    _storage_backend = "sqlite"

_sqlite_db_path = os.environ.get(
    "SQLITE_DB_PATH",
    os.path.join(os.getcwd(), "data", "app.db"),
)
_sqlcipher_db_path = os.environ.get(
    "SQLCIPHER_DB_PATH",
    os.path.join(os.getcwd(), "data", "app_secure.db"),
)
_sqlcipher_key = os.environ.get("SQLCIPHER_KEY", "")
if _storage_backend == "sqlcipher" and not _sqlcipher_key:
    _sqlcipher_key = PASSWORD_PEPPER

STORAGE_CONFIG = {
    "backend": _storage_backend,
    "db_path": _sqlcipher_db_path if _storage_backend == "sqlcipher" else _sqlite_db_path,
    "db_key": _sqlcipher_key,
}

# Límites de validación
VALIDATION_LIMITS = {
    "height_min": 0.4,  # metros
    "height_max": 2.72,  # metros
    "weight_min": 2,  # kilogramos
    "weight_max": 650,  # kilogramos
    "birth_date_min": datetime(1900, 1, 1).date(),
    "weight_variation_per_day": 5,  # kg por día
    "name_min_length": 1,  # caracteres mínimos
    "name_max_length": 100,  # caracteres máximos
}

# Configuración del servidor
SERVER_CONFIG = {
    "port": 5001,
    "host": "0.0.0.0",
}

# Configuración de idioma
ACTIVE_LANGUAGE = 'es'

# Lista de idiomas disponibles (códigos de idioma)
AVAILABLE_LANGUAGES = ['es']

# Configuración WSTG Sync
WSTG_WEBHOOK_KEY = os.environ.get('WSTG_WEBHOOK_KEY', 'change_me_in_production')
WSTG_SYNC_API_URL = os.environ.get('WSTG_SYNC_API_URL', 'http://localhost:5001/api/wstg/sync')