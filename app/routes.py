"""
Blueprint para las rutas de API REST
Maneja todas las operaciones de la API (usuarios, pesos, IMC, estadísticas)
"""
from flask import request, jsonify, Blueprint, current_app
from datetime import datetime, date

from .storage import UserData, WeightEntryData
from .helpers import calculate_bmi, get_bmi_description, validate_and_sanitize_name
from .translations import get_error, get_message, get_text, get_days_text, get_frontend_messages
from .config import USER_ID, VALIDATION_LIMITS


api = Blueprint('api', __name__, url_prefix='/api')


@api.route('/user', methods=['GET'])
def get_user():
    storage = current_app.storage
    user = storage.get_user(USER_ID)
    if not user:
        return jsonify({"error": get_error("user_not_found")}), 404
    return jsonify({
        "nombre": user.first_name,
        "apellidos": user.last_name,
        "fecha_nacimiento": user.birth_date.isoformat(),
        "talla_m": user.height_m
    })


@api.route('/user', methods=['POST'])
def create_or_update_user():
    storage = current_app.storage
    data = request.json or {}

    try:
        height_m = float(data['talla_m'])
    except Exception:
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
        user_id=USER_ID,
        first_name=nombre_sanitized,
        last_name=apellidos_sanitized,
        birth_date=birth_date,
        height_m=height_m
    )
    storage.save_user(user)
    
    return jsonify({"message": get_message("user_saved")}), 200


@api.route('/weight', methods=['POST'])
def add_weight():
    storage = current_app.storage
    data = request.json or {}
    
    user = storage.get_user(USER_ID)
    if not user:
        return jsonify({"error": get_error("user_must_be_configured")}), 400

    try:
        weight_kg = float(data['peso_kg'])
    except Exception:
        return jsonify({"error": get_error("invalid_weight")}), 400
    if not (VALIDATION_LIMITS["weight_min"] <= weight_kg <= VALIDATION_LIMITS["weight_max"]):
        return jsonify({"error": get_error("weight_out_of_range")}), 400

    current_date = date.today()
    
    # Obtener el último peso de un día diferente para validar variación
    # Si hay múltiples entradas del mismo día, se reemplazarán
    last_weight_different_date = storage.get_last_weight_entry_from_different_date(USER_ID, current_date)
    
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
        user_id=USER_ID,
        weight_kg=weight_kg,
        recorded_date=datetime.now()
    )
    storage.add_weight_entry(new_weight)
    
    return jsonify({"message": get_message("weight_registered")}), 201


@api.route('/imc', methods=['GET'])
def get_current_imc():
    storage = current_app.storage
    
    user = storage.get_user(USER_ID)
    if not user:
        return jsonify({"error": get_error("user_not_configured")}), 404

    last_weight = storage.get_last_weight_entry(USER_ID)
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
def get_stats():
    storage = current_app.storage
    
    weight_count = storage.get_weight_count(USER_ID)
    max_weight = storage.get_max_weight(USER_ID)
    min_weight = storage.get_min_weight(USER_ID)
    
    return jsonify({
        "num_pesajes": weight_count or 0,
        "peso_max": max_weight or 0,
        "peso_min": min_weight or 0
    })


@api.route('/weights', methods=['GET'])
def get_all_weights():
    """Obtiene todos los registros de peso del usuario"""
    storage = current_app.storage
    
    user = storage.get_user(USER_ID)
    if not user:
        return jsonify({"error": get_error("user_not_configured")}), 404
    
    # Obtener todas las entradas de peso
    all_entries = storage.get_all_weight_entries(USER_ID)
    
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


