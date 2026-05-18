"""
Verificación servidor de tokens Play Integrity (Google Play Integrity API).

Documentación: https://developer.android.com/google/play/integrity/overview
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import requests
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2 import service_account

logger = logging.getLogger(__name__)

PLAY_INTEGRITY_SCOPE = "https://www.googleapis.com/auth/playintegrity"
DECODE_URL = "https://playintegrity.googleapis.com/v1/{package_name}:decodeIntegrityToken"


@dataclass
class IntegrityVerdict:
    verdict: str  # PASS | FAIL | UNAVAILABLE
    reason: Optional[str] = None


def _post_decode(integrity_token: str, package_name: str, credentials_path: str) -> dict[str, Any]:
    creds = service_account.Credentials.from_service_account_file(
        credentials_path,
        scopes=[PLAY_INTEGRITY_SCOPE],
    )
    creds.refresh(GoogleAuthRequest())
    if not creds.token:
        raise RuntimeError("No se obtuvo access token de la cuenta de servicio")

    url = DECODE_URL.format(package_name=package_name)
    resp = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {creds.token}",
            "Content-Type": "application/json",
        },
        json={"integrity_token": integrity_token},
        timeout=min(float(os.environ.get("PLAY_INTEGRITY_HTTP_TIMEOUT", "15")), 60.0),
    )
    try:
        data = resp.json()
    except Exception:
        data = {"raw": resp.text[:500]}

    if resp.status_code == 200:
        return data

    err = data.get("error", {}) if isinstance(data, dict) else {}
    msg = err.get("message", resp.text[:300]) if isinstance(err, dict) else str(data)
    raise IntegrityApiError(resp.status_code, msg, data)


class IntegrityApiError(Exception):
    def __init__(self, status_code: int, message: str, body: Any):
        self.status_code = status_code
        self.message = message
        self.body = body
        super().__init__(f"{status_code}: {message}")


def verify_play_integrity_token(
    integrity_token: str,
    nonce: str,
    package_name: str,
    credentials_path: str,
) -> IntegrityVerdict:
    """
    Decodifica el token con Google y devuelve PASS / FAIL / UNAVAILABLE.
    """
    if not integrity_token or not isinstance(integrity_token, str):
        return IntegrityVerdict("FAIL", "MISSING_INTEGRITY_TOKEN")
    if not nonce or not isinstance(nonce, str):
        return IntegrityVerdict("FAIL", "MISSING_NONCE")
    path = Path(credentials_path)
    if not path.is_file():
        return IntegrityVerdict("UNAVAILABLE", "SERVICE_ACCOUNT_FILE_MISSING")

    try:
        decoded = _post_decode(integrity_token.strip(), package_name, str(path))
    except IntegrityApiError as e:
        if e.status_code in (401, 403):
            logger.warning("Play Integrity API permiso denegado: %s", e.message)
            return IntegrityVerdict("UNAVAILABLE", "PLAY_INTEGRITY_API_DENIED")
        if e.status_code == 400:
            return IntegrityVerdict("FAIL", "INVALID_INTEGRITY_TOKEN")
        logger.exception("Play Integrity API error")
        return IntegrityVerdict("UNAVAILABLE", "PLAY_INTEGRITY_BACKEND_ERROR")
    except requests.RequestException as e:
        logger.warning("Red Play Integrity: %s", e)
        return IntegrityVerdict("UNAVAILABLE", "PLAY_INTEGRITY_NETWORK_ERROR")
    except Exception as e:
        logger.exception("Fallo inesperado Play Integrity: %s", e)
        return IntegrityVerdict("UNAVAILABLE", "PLAY_INTEGRITY_UNEXPECTED_ERROR")

    payload = decoded.get("tokenPayloadExternal") if isinstance(decoded, dict) else None
    if not isinstance(payload, dict):
        return IntegrityVerdict("FAIL", "MALFORMED_INTEGRITY_PAYLOAD")

    req_details = payload.get("requestDetails") or {}
    if isinstance(req_details, dict):
        token_nonce = req_details.get("nonce")
        if token_nonce is not None and str(token_nonce) != str(nonce):
            return IntegrityVerdict("FAIL", "NONCE_MISMATCH")

    app_block = payload.get("appIntegrity") or {}
    app_verdict = app_block.get("appRecognitionVerdict") if isinstance(app_block, dict) else None

    device_block = payload.get("deviceIntegrity") or {}
    device_verdicts = device_block.get("deviceRecognitionVerdict") if isinstance(device_block, dict) else None
    if not isinstance(device_verdicts, list):
        device_verdicts = []

    allow_basic = os.environ.get("PLAY_INTEGRITY_ALLOW_BASIC", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )

    if app_verdict != "PLAY_RECOGNIZED":
        return IntegrityVerdict(
            "FAIL",
            f"APP_INTEGRITY:{app_verdict or 'UNKNOWN'}",
        )

    strong = "MEETS_STRONG_INTEGRITY" in device_verdicts
    device_ok = "MEETS_DEVICE_INTEGRITY" in device_verdicts
    basic = "MEETS_BASIC_INTEGRITY" in device_verdicts

    if strong or device_ok:
        return IntegrityVerdict("PASS", None)
    if allow_basic and basic:
        return IntegrityVerdict("PASS", None)

    return IntegrityVerdict(
        "FAIL",
        f"DEVICE_INTEGRITY:{','.join(device_verdicts) or 'NONE'}",
    )
