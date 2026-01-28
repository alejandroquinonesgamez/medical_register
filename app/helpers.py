"""
Funciones auxiliares para la aplicación médica

Este módulo contiene funciones de utilidad para:
- Cálculo de IMC (Índice de Masa Corporal)
- Clasificación de IMC según categorías de la OMS
- Validación y sanitización de nombres (resuelve CWE-20)
  - Valida longitud (1-100 caracteres)
  - Elimina caracteres peligrosos (< > " ')
  - Normaliza espacios múltiples
  - Valida caracteres permitidos (letras Unicode, espacios, guiones, apóstrofes)
"""
import re
import hashlib
import urllib.request
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from .translations import get_bmi_complete_description
from .config import (
    AUTH_CONFIG,
    PASSWORD_HASH_CONFIG,
    PASSWORD_PEPPER,
    COMMON_PASSWORDS_PATH,
    HIBP_API_URL,
    HIBP_TIMEOUT_SECONDS,
    HIBP_FAIL_CLOSED,
    COMMON_PASSWORDS_FALLBACK_PATH,
)


def calculate_bmi(weight_kg, height_m):
    if height_m <= 0:
        return 0
    return round(weight_kg / (height_m ** 2), 1)


def get_bmi_description(bmi):
    """Devuelve la clasificación de BMI con su descripción detallada"""
    # Diccionario que vincula el rango de BMI con la clave de descripción
    # La descripción está vinculada directamente a la clasificación
    if bmi < 18.5:
        key = "underweight"
    elif 18.5 <= bmi < 25:
        key = "normal"
    elif 25 <= bmi < 30:
        key = "overweight"
    elif 30 <= bmi < 35:
        key = "obese_class_i"
    elif 35 <= bmi < 40:
        key = "obese_class_ii"
    else:  # bmi >= 40
        key = "obese_class_iii"
    
    return get_bmi_complete_description(key)


def validate_and_sanitize_name(name, min_length=1, max_length=100):
    """
    Valida y sanitiza un nombre o apellido.
    
    Permite:
    - Letras (incluyendo acentos y caracteres internacionales)
    - Espacios
    - Guiones (-)
    - Apóstrofes (')
    
    Elimina:
    - Caracteres peligrosos: < > " ' (comillas dobles y simples)
    - Espacios múltiples (normaliza a un solo espacio)
    - Espacios al inicio y final
    
    Args:
        name: String con el nombre a validar
        min_length: Longitud mínima permitida
        max_length: Longitud máxima permitida
    
    Returns:
        tuple: (is_valid: bool, sanitized_name: str, error_key: str or None)
    """
    if not isinstance(name, str):
        return False, "", "invalid_name"
    
    # Eliminar espacios al inicio y final
    name = name.strip()
    
    # Validar que no esté vacío
    if not name:
        return False, "", "name_empty"
    
    # Validar longitud
    if len(name) > max_length:
        return False, "", "name_too_long"
    if len(name) < min_length:
        return False, "", "invalid_name"
    
    # Eliminar caracteres peligrosos que podrían causar problemas de renderizado o seguridad
    # Eliminar: < > " ' (comillas dobles y simples)
    dangerous_chars = ['<', '>', '"', "'"]
    for char in dangerous_chars:
        name = name.replace(char, '')
    
    # Normalizar espacios múltiples a un solo espacio
    name = re.sub(r'\s+', ' ', name)
    
    # Validar que solo contenga caracteres permitidos
    # Permitir: letras (incluyendo Unicode), espacios, guiones, apóstrofes
    # Verificar manualmente que todos los caracteres sean letras, espacios, guiones o apóstrofes
    for char in name:
        if not (char.isalpha() or char.isspace() or char == '-' or char == "'"):
            return False, "", "invalid_name"
    
    # Verificar que no sean solo espacios después de la sanitización
    if not name.strip():
        return False, "", "invalid_name"
    
    return True, name, None


def normalize_username(username):
    if not isinstance(username, str):
        return ""
    return username.strip().lower()


def validate_username(username):
    normalized = normalize_username(username)
    if not normalized:
        return False, "invalid_username"
    if len(normalized) < AUTH_CONFIG["username_min_length"]:
        return False, "username_too_short"
    if len(normalized) > AUTH_CONFIG["username_max_length"]:
        return False, "username_too_long"
    if not re.match(r"^[a-z0-9._-]+$", normalized):
        return False, "invalid_username"
    return True, None


def validate_password_strength(password):
    if not isinstance(password, str) or not password:
        return False, "invalid_password"
    if len(password) < AUTH_CONFIG["password_min_length"]:
        return False, "password_too_short"
    if is_pwned_password(password):
        return False, "password_pwned"
    return True, None


def is_common_password(password):
    """Comprueba si la contraseña aparece en una lista común (RockYou)."""
    if not isinstance(password, str) or not password:
        return False
    try:
        with open(COMMON_PASSWORDS_PATH, "r", encoding="latin-1", errors="ignore") as f:
            candidate = password.strip()
            for line in f:
                if candidate == line.strip():
                    return True
    except FileNotFoundError:
        # Si no existe el archivo, no bloqueamos por este criterio
        return False
    except OSError:
        return False
    return False


def is_common_password_fallback(password):
    """Comprueba si la contraseña aparece en un fallback local."""
    if not isinstance(password, str) or not password:
        return False
    try:
        with open(COMMON_PASSWORDS_FALLBACK_PATH, "r", encoding="latin-1", errors="ignore") as f:
            candidate = password.strip()
            for line in f:
                if candidate == line.strip():
                    return True
    except FileNotFoundError:
        return False
    except OSError:
        return False
    return False


def _hibp_range_request(prefix):
    url = f"{HIBP_API_URL}{prefix}"
    req = urllib.request.Request(url, headers={"User-Agent": "PPS-Segura-App"})
    with urllib.request.urlopen(req, timeout=HIBP_TIMEOUT_SECONDS) as response:
        return response.read().decode("utf-8", errors="ignore")


def is_pwned_password(password):
    """Comprueba si la contraseña aparece en HIBP (k-anonymity)."""
    if not isinstance(password, str) or not password:
        return False
    try:
        sha1 = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
        prefix, suffix = sha1[:5], sha1[5:]
        body = _hibp_range_request(prefix)
        for line in body.splitlines():
            if ":" not in line:
                continue
            hash_suffix, _count = line.split(":", 1)
            if hash_suffix.strip().upper() == suffix:
                return True
        return False
    except Exception:
        # Fallback local si existe
        if is_common_password_fallback(password):
            return True
        # Si HIBP falla, opcionalmente cerramos el registro
        return True if HIBP_FAIL_CLOSED else False


def _get_password_hasher():
    return PasswordHasher(
        time_cost=PASSWORD_HASH_CONFIG["time_cost"],
        memory_cost=PASSWORD_HASH_CONFIG["memory_cost"],
        parallelism=PASSWORD_HASH_CONFIG["parallelism"],
        hash_len=PASSWORD_HASH_CONFIG["hash_len"],
        salt_len=PASSWORD_HASH_CONFIG["salt_len"],
    )


def hash_password(password):
    hasher = _get_password_hasher()
    peppered = f"{password}{PASSWORD_PEPPER}"
    return hasher.hash(peppered)


def verify_password(password, password_hash):
    hasher = _get_password_hasher()
    peppered = f"{password}{PASSWORD_PEPPER}"
    try:
        return hasher.verify(password_hash, peppered)
    except VerifyMismatchError:
        return False
