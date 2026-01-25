import os
import time
from collections import deque
from datetime import datetime

from flask import Blueprint, jsonify, request, g, current_app


_MAX_REQUESTS = int(os.environ.get("SUPERVISOR_MAX_REQUESTS", "200"))
_REQUESTS = deque(maxlen=_MAX_REQUESTS)

supervisor_api = Blueprint("supervisor_api", __name__, url_prefix="/api/supervisor")


def _now_iso():
    return datetime.now().isoformat()


def _is_sensitive_key(key: str) -> bool:
    key = key.lower()
    return any(token in key for token in [
        "password",
        "pass",
        "token",
        "csrf",
        "secret",
        "authorization",
        "cookie",
        "key",
    ])


def _truncate(value: str, limit: int = 2048) -> str:
    if value is None:
        return ""
    if len(value) <= limit:
        return value
    return value[:limit] + "…"


def _redact(value, key_hint: str = ""):
    if _is_sensitive_key(key_hint):
        return "***"
    if isinstance(value, dict):
        return {k: _redact(v, k) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact(v, key_hint) for v in value]
    if isinstance(value, str):
        return _truncate(value, 512)
    return value


def _extract_request_body():
    if request.is_json:
        return _redact(request.get_json(silent=True) or {})
    if request.form:
        return _redact(request.form.to_dict())
    raw = request.get_data(as_text=True) or ""
    return _truncate(raw, 1024) if raw else ""


def _extract_headers(headers):
    sanitized = {}
    for key, value in headers.items():
        if _is_sensitive_key(key):
            sanitized[key] = "***"
        else:
            sanitized[key] = _truncate(value, 256)
    return sanitized


def _extract_response_body(response):
    try:
        content_type = response.mimetype or ""
        if content_type == "application/json":
            return _truncate(response.get_data(as_text=True), 2048)
    except Exception:
        return ""
    return ""


def _before_request():
    g._sup_start = time.time()


def _after_request(response):
    try:
        started = getattr(g, "_sup_start", None)
        duration_ms = int((time.time() - started) * 1000) if started else None
        entry = {
            "timestamp": _now_iso(),
            "method": request.method,
            "path": request.path,
            "query": request.query_string.decode("utf-8", "ignore"),
            "status": response.status_code,
            "duration_ms": duration_ms,
            "request_headers": _extract_headers(request.headers),
            "request_body": _extract_request_body(),
            "response_body": _extract_response_body(response),
        }
        _REQUESTS.append(entry)
    except Exception:
        pass
    return response


def _db_snapshot(storage):
    snapshot = {"users": [], "weights": [], "api_tokens": []}
    if storage is None:
        return snapshot

    if hasattr(storage, "_connect"):
        with storage._connect() as conn:
            snapshot["users"] = [
                dict(row) for row in conn.execute(
                    "SELECT id, username, created_at FROM users ORDER BY id DESC LIMIT 50"
                ).fetchall()
            ]
            snapshot["weights"] = [
                dict(row) for row in conn.execute(
                    "SELECT id, user_id, weight_kg, recorded_date FROM weights ORDER BY id DESC LIMIT 50"
                ).fetchall()
            ]
            snapshot["api_tokens"] = [
                dict(row) for row in conn.execute(
                    "SELECT id, user_id, expires_at, created_at FROM api_tokens ORDER BY id DESC LIMIT 50"
                ).fetchall()
            ]
        return snapshot

    if hasattr(storage, "_auth_users") and hasattr(storage, "_weight_entries"):
        snapshot["users"] = [
            {
                "id": user.user_id,
                "username": user.username,
                "created_at": user.created_at.isoformat(),
            }
            for user in storage._auth_users.values()
        ]
        snapshot["weights"] = [
            {
                "id": entry.entry_id,
                "user_id": entry.user_id,
                "weight_kg": entry.weight_kg,
                "recorded_date": entry.recorded_date.isoformat(),
            }
            for entry in storage._weight_entries
        ]
        snapshot["api_tokens"] = [
            {
                "user_id": token_data[0],
                "expires_at": token_data[1].isoformat(),
            }
            for token_data in storage._api_tokens.values()
        ]
    return snapshot


@supervisor_api.route("/requests", methods=["GET"])
def get_requests():
    return jsonify({"requests": list(reversed(_REQUESTS))})


@supervisor_api.route("/db", methods=["GET"])
def get_db_snapshot():
    return jsonify(_db_snapshot(current_app.storage))


def init_supervisor(app):
    app.before_request(_before_request)
    app.after_request(_after_request)
    app.register_blueprint(supervisor_api)
