"""
Utilidades JWT (JSON Web Tokens) para autenticación stateless

Implementa un esquema de doble token:
- Access token (corta vida, ~15 min): se envía en la cabecera Authorization: Bearer.
  Almacenado solo en memoria del cliente (no en localStorage) para mitigar XSS.
- Refresh token (larga vida, ~7 días): se envía como cookie HttpOnly.
  No accesible desde JavaScript; protegido contra XSS.

Cada token incluye un campo 'jti' (JWT ID) único que permite la revocación
individual de tokens mediante una blacklist en base de datos.
"""
import secrets
from datetime import datetime, timezone

import jwt

from .config import JWT_CONFIG


def _get_secret():
    """Obtiene el secreto JWT. Genera uno temporal si no está configurado."""
    secret = JWT_CONFIG["secret_key"]
    if not secret:
        if not hasattr(_get_secret, "_fallback"):
            _get_secret._fallback = secrets.token_urlsafe(64)
        return _get_secret._fallback
    return secret


def create_access_token(user_id, username):
    """
    Crea un access token JWT de corta vida.

    Payload:
        sub: user_id (int)
        username: nombre de usuario
        type: "access"
        jti: identificador único del token
        iat: fecha de emisión
        exp: fecha de expiración
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "username": username,
        "type": "access",
        "jti": secrets.token_urlsafe(16),
        "iat": now,
        "exp": now + JWT_CONFIG["access_token_expires"],
    }
    return jwt.encode(payload, _get_secret(), algorithm=JWT_CONFIG["algorithm"])


def create_refresh_token(user_id):
    """
    Crea un refresh token JWT de larga vida.

    Payload:
        sub: user_id (como string, PyJWT requiere 'sub' string)
        type: "refresh"
        jti: identificador único (usado para revocación en blacklist)
        iat: fecha de emisión
        exp: fecha de expiración
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "jti": secrets.token_urlsafe(16),
        "iat": now,
        "exp": now + JWT_CONFIG["refresh_token_expires"],
    }
    return jwt.encode(payload, _get_secret(), algorithm=JWT_CONFIG["algorithm"])


def decode_token(token, expected_type=None):
    """
    Decodifica y valida un token JWT.

    Args:
        token: cadena JWT
        expected_type: si se especifica, verifica que el campo 'type' coincida

    Returns:
        dict con el payload decodificado

    Raises:
        jwt.ExpiredSignatureError: token expirado
        jwt.InvalidTokenError: token inválido (firma, formato, etc.)
        ValueError: tipo de token no coincide con expected_type
    """
    payload = jwt.decode(
        token,
        _get_secret(),
        algorithms=[JWT_CONFIG["algorithm"]],
    )
    if expected_type and payload.get("type") != expected_type:
        raise ValueError(f"Se esperaba token tipo '{expected_type}', recibido '{payload.get('type')}'")
    return payload
