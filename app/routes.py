"""
Blueprint para las rutas de API REST

Este módulo maneja todas las operaciones de la API REST de la aplicación médica:
- Gestión de usuarios (crear, obtener, actualizar)
- Gestión de entradas de peso (crear, obtener, listar, eliminar)
- Cálculo de IMC y estadísticas
- Configuración (límites de validación)

Todas las rutas están prefijadas con /api y devuelven respuestas JSON.
Las validaciones incluyen sanitización de nombres (CWE-20 resuelto) y validación de tipos numéricos.
"""
from flask import request, jsonify, Blueprint, current_app, session, g
import secrets
from functools import wraps
from datetime import datetime, date
import math
import os

from .storage import UserData, WeightEntryData
from .helpers import (
    calculate_bmi,
    get_bmi_description,
    validate_and_sanitize_name,
    normalize_username,
    validate_username,
    validate_password_strength,
    hash_password,
    verify_password,
)
from .translations import get_error, get_message, get_text, get_days_text, get_frontend_messages
from .config import VALIDATION_LIMITS

# Obtener COMPOSE_PROJECT_NAME del entorno o usar el valor por defecto
COMPOSE_PROJECT_NAME = os.environ.get('COMPOSE_PROJECT_NAME', 'medical_register')


api = Blueprint('api', __name__, url_prefix='/api')


def _get_current_user_id():
    return session.get("user_id")


def _get_csrf_token():
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


def require_csrf(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        sent_token = request.headers.get("X-CSRF-Token", "")
        expected = session.get("csrf_token", "")
        if not expected or not sent_token or sent_token != expected:
            return jsonify({"error": "CSRF token inválido"}), 403
        return func(*args, **kwargs)
    return wrapper


def require_auth(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user_id = _get_current_user_id()
        if not user_id:
            return jsonify({"error": get_error("auth_required")}), 401
        g.current_user_id = user_id
        return func(*args, **kwargs)
    return wrapper


@api.route('/auth/register', methods=['POST'])
def register():
    storage = current_app.storage
    data = request.json or {}
    username_raw = data.get('username', '')
    password_raw = data.get('password', '')

    is_valid_username, error_key = validate_username(username_raw)
    if not is_valid_username:
        return jsonify({"error": get_error(error_key or "invalid_username")}), 400
    is_valid_password, error_key = validate_password_strength(password_raw)
    if not is_valid_password:
        return jsonify({"error": get_error(error_key or "invalid_password")}), 400

    username = normalize_username(username_raw)
    if storage.get_auth_user_by_username(username):
        return jsonify({"error": get_error("user_already_exists")}), 400

    password_hash = hash_password(password_raw)
    auth_user = storage.create_auth_user(username, password_hash)
    session["user_id"] = auth_user.user_id
    _get_csrf_token()
    return jsonify({
        "user_id": auth_user.user_id,
        "username": auth_user.username,
        "csrf_token": session.get("csrf_token")
    }), 201


@api.route('/auth/login', methods=['POST'])
def login():
    storage = current_app.storage
    data = request.json or {}
    username_raw = data.get('username', '')
    password_raw = data.get('password', '')

    is_valid_username, _ = validate_username(username_raw)
    if not is_valid_username or not password_raw:
        return jsonify({"error": get_error("invalid_credentials")}), 401

    username = normalize_username(username_raw)
    auth_user = storage.get_auth_user_by_username(username)
    if not auth_user:
        return jsonify({"error": get_error("invalid_credentials")}), 401

    if not verify_password(password_raw, auth_user.password_hash):
        return jsonify({"error": get_error("invalid_credentials")}), 401

    session["user_id"] = auth_user.user_id
    _get_csrf_token()
    return jsonify({
        "user_id": auth_user.user_id,
        "username": auth_user.username,
        "csrf_token": session.get("csrf_token")
    }), 200


@api.route('/auth/logout', methods=['POST'])
@require_csrf
def logout():
    session.pop("user_id", None)
    return jsonify({"message": "ok"}), 200


@api.route('/auth/me', methods=['GET'])
def me():
    storage = current_app.storage
    user_id = _get_current_user_id()
    if not user_id:
        return jsonify({"error": get_error("auth_required")}), 401
    auth_user = storage.get_auth_user_by_id(user_id)
    if not auth_user:
        session.pop("user_id", None)
        return jsonify({"error": get_error("auth_required")}), 401
    _get_csrf_token()
    return jsonify({
        "user_id": auth_user.user_id,
        "username": auth_user.username,
        "csrf_token": session.get("csrf_token")
    }), 200


@api.route('/user', methods=['GET'])
@require_auth
def get_user():
    storage = current_app.storage
    user = storage.get_user(g.current_user_id)
    if not user:
        return jsonify({"error": get_error("user_not_found")}), 404
    return jsonify({
        "nombre": user.first_name,
        "apellidos": user.last_name,
        "fecha_nacimiento": user.birth_date.isoformat(),
        "talla_m": user.height_m
    })


@api.route('/user', methods=['POST'])
@require_auth
@require_csrf
def create_or_update_user():
    storage = current_app.storage
    data = request.json or {}

    # Validar y convertir altura con validación de tipo y finitud
    talla_raw = data.get('talla_m')
    if talla_raw is None:
        return jsonify({"error": get_error("invalid_height")}), 400
    
    # Validar que sea convertible a float
    if not isinstance(talla_raw, (int, float, str)):
        return jsonify({"error": get_error("invalid_height")}), 400
    
    try:
        height_m = float(talla_raw)
    except (ValueError, TypeError):
        current_app.logger.warning(f"Error al convertir altura: {talla_raw}")
        return jsonify({"error": get_error("invalid_height")}), 400
    
    # Verificar que sea un número finito (no NaN ni Infinity)
    if not math.isfinite(height_m):
        return jsonify({"error": get_error("invalid_height")}), 400
    
    if not (VALIDATION_LIMITS["height_min"] <= height_m <= VALIDATION_LIMITS["height_max"]):
        return jsonify({"error": get_error("height_out_of_range")}), 400

    try:
        birth_date = datetime.strptime(data['fecha_nacimiento'], '%Y-%m-%d').date()
    except (ValueError, KeyError):
        return jsonify({"error": get_error("invalid_birth_date")}), 400
    
    min_date = VALIDATION_LIMITS["birth_date_min"]
    max_date = datetime.now().date()
    if birth_date < min_date or birth_date > max_date:
        return jsonify({"error": get_error("birth_date_out_of_range")}), 400

    # Validar y sanitizar nombre
    nombre_raw = data.get('nombre', '')
    is_valid_nombre, nombre_sanitized, error_key_nombre = validate_and_sanitize_name(
        nombre_raw,
        min_length=VALIDATION_LIMITS["name_min_length"],
        max_length=VALIDATION_LIMITS["name_max_length"]
    )
    if not is_valid_nombre:
        return jsonify({"error": get_error(error_key_nombre or "invalid_name")}), 400

    # Validar y sanitizar apellidos
    apellidos_raw = data.get('apellidos', '')
    is_valid_apellidos, apellidos_sanitized, error_key_apellidos = validate_and_sanitize_name(
        apellidos_raw,
        min_length=VALIDATION_LIMITS["name_min_length"],
        max_length=VALIDATION_LIMITS["name_max_length"]
    )
    if not is_valid_apellidos:
        return jsonify({"error": get_error(error_key_apellidos or "invalid_last_name")}), 400

    user = UserData(
        user_id=g.current_user_id,
        first_name=nombre_sanitized,
        last_name=apellidos_sanitized,
        birth_date=birth_date,
        height_m=height_m
    )
    storage.save_user(user)
    
    return jsonify({"message": get_message("user_saved")}), 200


@api.route('/weight', methods=['POST'])
@require_auth
@require_csrf
def add_weight():
    storage = current_app.storage
    data = request.json or {}
    
    user = storage.get_user(g.current_user_id)
    if not user:
        return jsonify({"error": get_error("user_must_be_configured")}), 400

    # Validar y convertir peso con validación de tipo y finitud
    peso_raw = data.get('peso_kg')
    if peso_raw is None:
        return jsonify({"error": get_error("invalid_weight")}), 400
    
    # Validar que sea convertible a float
    if not isinstance(peso_raw, (int, float, str)):
        return jsonify({"error": get_error("invalid_weight")}), 400
    
    try:
        weight_kg = float(peso_raw)
    except (ValueError, TypeError):
        current_app.logger.warning(f"Error al convertir peso: {peso_raw}")
        return jsonify({"error": get_error("invalid_weight")}), 400
    
    # Verificar que sea un número finito (no NaN ni Infinity)
    if not math.isfinite(weight_kg):
        return jsonify({"error": get_error("invalid_weight")}), 400
    
    if not (VALIDATION_LIMITS["weight_min"] <= weight_kg <= VALIDATION_LIMITS["weight_max"]):
        return jsonify({"error": get_error("weight_out_of_range")}), 400

    current_date = date.today()
    
    # Obtener el último peso de un día diferente para validar variación
    # Si hay múltiples entradas del mismo día, se reemplazarán
    last_weight_different_date = storage.get_last_weight_entry_from_different_date(g.current_user_id, current_date)
    
    if last_weight_different_date:
        last_registration_date = last_weight_different_date.recorded_date.date()
        days_elapsed = (current_date - last_registration_date).days
        
        # Validar variación respecto al último peso de un día diferente
        max_allowed_difference = days_elapsed * VALIDATION_LIMITS["weight_variation_per_day"]
        weight_difference = abs(weight_kg - last_weight_different_date.weight_kg)
        
        if weight_difference > max_allowed_difference:
            days_text = get_days_text(days_elapsed)
            
            return jsonify({
                "error": get_error("weight_variation_exceeded", 
                                  days_text=days_text,
                                  max_allowed_difference=max_allowed_difference,
                                  weight_difference=weight_difference)
            }), 400

    new_weight = WeightEntryData(
        entry_id=0,
        user_id=g.current_user_id,
        weight_kg=weight_kg,
        recorded_date=datetime.now()
    )
    storage.add_weight_entry(new_weight)
    
    return jsonify({"message": get_message("weight_registered")}), 201


@api.route('/imc', methods=['GET'])
@require_auth
def get_current_imc():
    storage = current_app.storage
    
    user = storage.get_user(g.current_user_id)
    if not user:
        return jsonify({"error": get_error("user_not_configured")}), 404

    last_weight = storage.get_last_weight_entry(g.current_user_id)
    if not last_weight:
        return jsonify({"imc": 0, "description": get_text("no_weight_records")}), 200

    # Validación defensiva: verificar que los datos estén dentro de los límites
    # antes de calcular el IMC (protege contra datos antiguos o corruptos)
    if not (VALIDATION_LIMITS["weight_min"] <= last_weight.weight_kg <= VALIDATION_LIMITS["weight_max"]):
        return jsonify({"error": get_error("weight_out_of_range")}), 400
    if not (VALIDATION_LIMITS["height_min"] <= user.height_m <= VALIDATION_LIMITS["height_max"]):
        return jsonify({"error": get_error("height_out_of_range")}), 400

    bmi = calculate_bmi(last_weight.weight_kg, user.height_m)
    description = get_bmi_description(bmi)
    return jsonify({"imc": bmi, "description": description})


@api.route('/stats', methods=['GET'])
@require_auth
def get_stats():
    storage = current_app.storage
    
    weight_count = storage.get_weight_count(g.current_user_id)
    max_weight = storage.get_max_weight(g.current_user_id)
    min_weight = storage.get_min_weight(g.current_user_id)
    
    return jsonify({
        "num_pesajes": weight_count or 0,
        "peso_max": max_weight or 0,
        "peso_min": min_weight or 0
    })


@api.route('/weights', methods=['GET'])
@require_auth
def get_all_weights():
    """Obtiene todos los registros de peso del usuario"""
    storage = current_app.storage
    
    user = storage.get_user(g.current_user_id)
    if not user:
        return jsonify({"error": get_error("user_not_configured")}), 404
    
    # Obtener todas las entradas de peso
    all_entries = storage.get_all_weight_entries(g.current_user_id)
    
    # Convertir a formato JSON
    weights_data = [
        {
            "id": entry.entry_id,
            "peso_kg": entry.weight_kg,
            "fecha_registro": entry.recorded_date.isoformat()
        }
        for entry in all_entries
    ]
    
    return jsonify({
        "weights": weights_data
    })


@api.route('/weights/recent', methods=['GET'])
@require_auth
def get_recent_weights():
    """Obtiene los últimos 5 registros de peso del usuario"""
    storage = current_app.storage
    
    # Obtener todas las entradas de peso (ya están ordenadas por fecha descendente)
    # No requiere usuario configurado, similar a /stats
    all_entries = storage.get_all_weight_entries(g.current_user_id)
    
    # Limitar a los últimos 5
    recent_entries = all_entries[:5]
    
    # Convertir a formato JSON
    weights_data = [
        {
            "id": entry.entry_id,
            "peso_kg": entry.weight_kg,
            "fecha_registro": entry.recorded_date.isoformat()
        }
        for entry in recent_entries
    ]
    
    return jsonify({
        "weights": weights_data
    })


@api.route('/messages', methods=['GET'])
def get_messages():
    """Endpoint que devuelve todos los mensajes para el frontend"""
    return jsonify(get_frontend_messages())


@api.route('/config', methods=['GET'])
def get_config():
    """Endpoint que devuelve las constantes de validación y configuración para el frontend"""
    from .config import VALIDATION_LIMITS
    
    # Convertir fecha a string ISO para JSON
    config = {
        "validation_limits": {
            "height_min": VALIDATION_LIMITS["height_min"],
            "height_max": VALIDATION_LIMITS["height_max"],
            "weight_min": VALIDATION_LIMITS["weight_min"],
            "weight_max": VALIDATION_LIMITS["weight_max"],
            "birth_date_min": VALIDATION_LIMITS["birth_date_min"].isoformat(),
            "weight_variation_per_day": VALIDATION_LIMITS["weight_variation_per_day"],
            "name_min_length": VALIDATION_LIMITS["name_min_length"],
            "name_max_length": VALIDATION_LIMITS["name_max_length"]
        }
    }
    
    return jsonify(config)


