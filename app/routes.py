"""
Blueprint para las rutas de API REST

Este módulo maneja todas las operaciones de la API REST de la aplicación médica:
- Gestión de usuarios (crear, obtener, actualizar)
- Gestión de entradas de peso (crear, obtener, listar, eliminar)
- Cálculo de IMC y estadísticas
- Configuración (límites de validación)
- Integración con DefectDojo (exportar/importar dumps, generar PDF del informe ASVS)

Todas las rutas están prefijadas con /api y devuelven respuestas JSON.
Las validaciones incluyen sanitización de nombres (CWE-20 resuelto) y validación de tipos numéricos.
"""
from flask import request, jsonify, Blueprint, current_app, session, g
import secrets
from functools import wraps
from datetime import datetime, date
import math
import os
import shutil

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


def _compose_cmd():
    """Devuelve el comando de Docker Compose disponible."""
    if shutil.which("docker"):
        try:
            import subprocess
            subprocess.run(
                ["docker", "compose", "version"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return ["docker", "compose"]
        except Exception:
            pass
    if shutil.which("docker-compose"):
        return ["docker-compose"]
    return ["docker", "compose"]


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

    # Rehash con el coste actual si la configuración ha cambiado (migración de parámetros)
    new_hash = hash_password(password_raw)
    if new_hash != auth_user.password_hash:
        storage.update_password_hash(auth_user.user_id, new_hash)

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


@api.route('/defectdojo/export-dump', methods=['GET'])
def export_defectdojo_dump():
    """
    Exportar el dump de la base de datos de DefectDojo
    
    Ejecuta el script export_defectdojo_db.sh para crear un dump SQL de la base de datos
    de DefectDojo y lo devuelve como descarga. El dump incluye todos los datos:
    - Usuarios, productos, engagements, tests
    - Findings (vulnerabilidades) con su estado actual
    - Configuraciones y metadatos
    
    El dump se genera con fecha en el nombre: defectdojo_db_dump_YYYYMMDD_HHMMSS.sql
    """
    import subprocess
    import os
    from flask import send_file
    
    try:
        # Ruta del archivo de dump
        dump_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'defectdojo_db_dump.sql')
        dump_dir = os.path.dirname(dump_file)
        
        # Crear directorio si no existe
        os.makedirs(dump_dir, exist_ok=True)
        
        # Exportar la base de datos usando docker-compose
        compose_cmd = _compose_cmd()
        result = subprocess.run(
            compose_cmd + ['--profile', 'defectdojo', 'exec', '-T', 'defectdojo-db',
                           'pg_dump', '-U', 'defectdojo', 'defectdojo'],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutos máximo
        )
        
        if result.returncode != 0:
            current_app.logger.error(f"Error al exportar dump: {result.stderr}")
            return jsonify({"error": "Error al exportar la base de datos"}), 500
        
        # Guardar el dump en un archivo temporal
        with open(dump_file, 'w', encoding='utf-8') as f:
            f.write(result.stdout)
        
        # Enviar el archivo como descarga
        return send_file(
            dump_file,
            as_attachment=True,
            download_name='defectdojo_db_dump.sql',
            mimetype='application/sql'
        )
        
    except subprocess.TimeoutExpired:
        current_app.logger.error("Timeout al exportar dump")
        return jsonify({"error": "Timeout al exportar la base de datos"}), 500
    except Exception as e:
        current_app.logger.error(f"Error inesperado al exportar dump: {str(e)}")
        return jsonify({"error": f"Error al exportar: {str(e)}"}), 500


@api.route('/defectdojo/import-dump', methods=['POST'])
def import_defectdojo_dump():
    """
    Importar un dump de la base de datos de DefectDojo
    
    Permite cargar un dump SQL previamente exportado en la base de datos de DefectDojo.
    Esto es útil para:
    - Restaurar backups
    - Cargar datos de otro entorno
    - Migrar findings y configuraciones
    
    Después de importar el dump, reinicia DefectDojo para aplicar los cambios.
    El archivo debe tener extensión .sql y se valida antes de importar.
    """
    import subprocess
    import os
    from werkzeug.utils import secure_filename
    
    try:
        # Verificar que se haya enviado un archivo
        if 'file' not in request.files:
            return jsonify({"error": "No se envió ningún archivo"}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"error": "No se seleccionó ningún archivo"}), 400
        
        # Validar extensión
        if not file.filename.endswith('.sql'):
            return jsonify({"error": "El archivo debe ser un dump SQL (.sql)"}), 400
        
        # Guardar el archivo temporalmente
        temp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        filename = secure_filename(file.filename)
        temp_file = os.path.join(temp_dir, filename)
        file.save(temp_file)
        
        try:
            # Leer el contenido del archivo
            with open(temp_file, 'r', encoding='utf-8') as f:
                dump_content = f.read()
            
            # Cargar el dump en PostgreSQL
            compose_cmd = _compose_cmd()
            result = subprocess.run(
                compose_cmd + ['--profile', 'defectdojo', 'exec', '-T', 'defectdojo-db',
                               'psql', '-U', 'defectdojo', '-d', 'defectdojo'],
                input=dump_content,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutos máximo
            )
            
            if result.returncode != 0:
                current_app.logger.error(f"Error al importar dump: {result.stderr}")
                return jsonify({"error": f"Error al importar: {result.stderr}"}), 500
            
            # Reiniciar DefectDojo para aplicar cambios
            restart_result = subprocess.run(
                compose_cmd + ['--profile', 'defectdojo', 'restart', 'defectdojo'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if restart_result.returncode != 0:
                current_app.logger.warning(f"Advertencia al reiniciar DefectDojo: {restart_result.stderr}")
            
            return jsonify({
                "message": "Dump importado correctamente. DefectDojo se está reiniciando.",
                "success": True
            })
            
        finally:
            # Eliminar archivo temporal
            if os.path.exists(temp_file):
                os.remove(temp_file)
        
    except subprocess.TimeoutExpired:
        current_app.logger.error("Timeout al importar dump")
        return jsonify({"error": "Timeout al importar la base de datos"}), 500
    except Exception as e:
        current_app.logger.error(f"Error inesperado al importar dump: {str(e)}")
        return jsonify({"error": f"Error al importar: {str(e)}"}), 500


@api.route('/defectdojo/generate-pdf', methods=['GET'])
def generate_pdf_report():
    """
    Generar PDF del informe de seguridad ASVS y descargarlo
    
    Genera el PDF a partir del Markdown existente (docs/INFORME_SEGURIDAD.md)
    sin regenerar el Markdown. Si el Markdown no existe, devuelve un error.
    
    El PDF se guarda en docs/informes/ con el formato: INFORME_SEGURIDAD_YYYYMMDD.pdf
    y se descarga automáticamente al usuario.
    
    Usado por el botón "Generar PDF Informe" en la interfaz de usuario.
    """
    import subprocess
    import os
    from flask import send_file
    from datetime import datetime
    
    try:
        # Obtener el directorio del proyecto
        project_root = os.path.dirname(os.path.dirname(__file__))
        
        # Verificar que el Markdown existe antes de generar el PDF
        report_md = os.path.join(project_root, 'docs', 'INFORME_SEGURIDAD.md')
        if not os.path.exists(report_md):
            return jsonify({"error": "El archivo INFORME_SEGURIDAD.md no existe. Por favor, genera el informe Markdown primero."}), 500
        
        current_app.logger.info("Generando PDF a partir del Markdown existente...")
        
        # Generar el PDF a partir del Markdown existente
        generate_pdf_script_path = os.path.join(project_root, 'scripts', 'generate_pdf_report.py')
        if not os.path.exists(generate_pdf_script_path):
            return jsonify({"error": "Script de generación de PDF no encontrado"}), 500
        
        current_app.logger.info("Ejecutando generate_pdf_report.py para generar PDF...")
        
        # Intentar ejecutar desde contenedor de DefectDojo si está disponible
        result_pdf = None
        try:
            # Intentar ejecutar desde contenedor de DefectDojo
            compose_cmd = _compose_cmd()
            result_pdf = subprocess.run(
                compose_cmd + ['--profile', 'defectdojo', 'exec', '-T', 'defectdojo', 'python', '/app/scripts/generate_pdf_report.py'],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=project_root
            )
        except (FileNotFoundError, subprocess.SubprocessError):
            # Si docker-compose no está disponible o el contenedor no está corriendo, ejecutar localmente
            current_app.logger.warning("No se pudo ejecutar desde contenedor, ejecutando localmente...")
            result_pdf = subprocess.run(
                ['python3', generate_pdf_script_path],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=project_root
            )
        
        if result_pdf.returncode != 0:
            current_app.logger.error(f"Error al generar PDF: {result_pdf.stderr}")
            return jsonify({"error": f"Error al generar PDF: {result_pdf.stderr}"}), 500
        current_app.logger.info("PDF generado correctamente.")
        
        # Buscar el PDF más reciente generado
        informes_dir = os.path.join(project_root, 'docs', 'informes')
        
        # Crear la carpeta si no existe
        if not os.path.exists(informes_dir):
            os.makedirs(informes_dir, exist_ok=True)
        
        pdf_files = [f for f in os.listdir(informes_dir) if f.startswith('INFORME_SEGURIDAD_') and f.endswith('.pdf')]
        
        if not pdf_files:
            return jsonify({"error": "No se encontró el PDF generado"}), 500
        
        # Obtener el PDF más reciente
        pdf_files_with_time = [(f, os.path.getmtime(os.path.join(informes_dir, f))) for f in pdf_files]
        pdf_files_with_time.sort(key=lambda x: x[1], reverse=True)
        latest_pdf = pdf_files_with_time[0][0]
        
        pdf_path = os.path.join(informes_dir, latest_pdf)
        
        # Enviar el archivo como descarga
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=latest_pdf,
            mimetype='application/pdf'
        )
        
    except subprocess.TimeoutExpired:
        current_app.logger.error("Timeout al generar PDF")
        return jsonify({"error": "Timeout al generar el PDF"}), 500
    except Exception as e:
        current_app.logger.error(f"Error inesperado al generar PDF: {str(e)}")
        return jsonify({"error": f"Error al generar PDF: {str(e)}"}), 500


@api.route('/wstg/sync', methods=['POST'])
def wstg_sync():
    """
    Sincronizar estado desde WSTG Tracker hacia DefectDojo
    Endpoint automático llamado por el tracker cuando cambia un estado
    Guarda la solicitud en un archivo para que el servicio de sincronización la procese
    """
    import json as json_module
    from pathlib import Path
    
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    try:
        # Guardar solicitud en archivo compartido para procesamiento asíncrono
        sync_queue_dir = Path('/app/data/wstg_sync_queue')
        sync_queue_dir.mkdir(parents=True, exist_ok=True)
        
        # Crear archivo con timestamp único
        import time
        filename = f"sync_{int(time.time() * 1000)}_{data.get('wstg_id', 'unknown')}.json"
        filepath = sync_queue_dir / filename
        
        sync_request = {
            'type': 'tracker->dd',
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json_module.dump(sync_request, f)
        
        current_app.logger.info(f"Solicitud de sincronización guardada: {filename}")
        
        # Intentar procesar inmediatamente si DefectDojo está disponible
        # (opcional, puede procesarse de forma asíncrona)
        try:
            import subprocess
            # Ejecutar en contenedor de DefectDojo usando docker-compose desde el host
            # Nota: Esto requiere que docker-compose esté disponible en el host
            # Como alternativa, el servicio de sincronización procesará estos archivos
            compose_cmd = _compose_cmd()
            result = subprocess.run(
                compose_cmd + ['exec', '-T', 'defectdojo', 'python', '/app/scripts/wstg_sync_handler.py',
                               'sync_from_tracker', json_module.dumps(data)],
                capture_output=True,
                text=True,
                timeout=10,
                cwd='/app'  # Asegurar que estamos en el directorio correcto
            )
            
            if result.returncode == 0:
                try:
                    result_data = json_module.loads(result.stdout.strip())
                    # Eliminar archivo si se procesó correctamente
                    if result_data.get('success') and filepath.exists():
                        filepath.unlink()
                    return jsonify(result_data), 200
                except json_module.JSONDecodeError:
                    # Si falla el procesamiento inmediato, el archivo quedará para procesamiento asíncrono
                    pass
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            # Si no se puede procesar inmediatamente, se procesará de forma asíncrona
            current_app.logger.debug(f"No se pudo procesar inmediatamente, se procesará de forma asíncrona: {e}")
        
        # Retornar éxito - la sincronización se procesará de forma asíncrona
        return jsonify({
            "success": True,
            "message": "Solicitud de sincronización recibida y en cola",
            "queued": True
        }), 202  # 202 Accepted - procesamiento asíncrono
        
    except Exception as e:
        current_app.logger.error(f"Error en sincronización WSTG: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@api.route('/wstg/webhook', methods=['POST'])
def wstg_webhook():
    """
    Recibir webhook de DefectDojo y sincronizar con tracker
    Endpoint automático llamado por DefectDojo cuando se actualiza un finding
    Guarda la solicitud para procesamiento asíncrono
    """
    import json as json_module
    from pathlib import Path
    from .config import WSTG_WEBHOOK_KEY
    import os
    
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    # Validar autenticación del webhook (API key)
    api_key = request.headers.get('X-API-Key') or request.headers.get('Authorization', '').replace('Bearer ', '')
    expected_key = os.environ.get('WSTG_WEBHOOK_KEY', WSTG_WEBHOOK_KEY)
    
    if expected_key and expected_key != 'change_me_in_production':
        if not api_key or api_key != expected_key:
            current_app.logger.warning(f"Intento de webhook no autorizado: {api_key}")
            return jsonify({"error": "Unauthorized"}), 401
    
    try:
        # Guardar solicitud en archivo compartido
        sync_queue_dir = Path('/app/data/wstg_sync_queue')
        sync_queue_dir.mkdir(parents=True, exist_ok=True)
        
        import time
        filename = f"webhook_{int(time.time() * 1000)}.json"
        filepath = sync_queue_dir / filename
        
        webhook_request = {
            'type': 'dd->tracker',
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json_module.dump(webhook_request, f)
        
        current_app.logger.info(f"Webhook guardado: {filename}")
        
        return jsonify({
            "success": True,
            "message": "Webhook recibido y en cola",
            "queued": True
        }), 202  # 202 Accepted
        
    except Exception as e:
        current_app.logger.error(f"Error en webhook WSTG: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@api.route('/wstg/status', methods=['GET'])
def wstg_status():
    """
    Obtener estado de sincronización WSTG
    Útil para monitoreo y dashboard
    Lee el estado desde el archivo JSON compartido
    """
    from pathlib import Path
    import json as json_module
    
    try:
        # Leer estado desde archivo compartido
        state_file = Path('/app/data/wstg_sync_state.json')
        if state_file.exists():
            with open(state_file, 'r') as f:
                state = json_module.load(f)
            
            items = state.get('items', {})
            total_items = len(items)
            synced_items = sum(1 for item in items.values() 
                              if item.get('last_sync_timestamp'))
            
            conflicts = 0
            for wstg_id, item_data in items.items():
                wstg_status = item_data.get('wstg_status')
                dd_status = item_data.get('defectdojo_status')
                if wstg_status and dd_status:
                    if (wstg_status == 'Done' and dd_status != 'verified') or \
                       (wstg_status == 'In Progress' and dd_status != 'active'):
                        conflicts += 1
            
            last_sync = None
            if state.get('sync_log'):
                last_sync = state['sync_log'][-1].get('timestamp')
            
            return jsonify({
                "last_sync": last_sync or datetime.now().isoformat(),
                "total_items": total_items,
                "synced_items": synced_items,
                "pending_items": total_items - synced_items,
                "conflicts": conflicts
            }), 200
        else:
            # Estado inicial si no existe archivo
            return jsonify({
                "last_sync": datetime.now().isoformat(),
                "total_items": 0,
                "synced_items": 0,
                "pending_items": 0,
                "conflicts": 0
            }), 200
            
    except Exception as e:
        current_app.logger.error(f"Error obteniendo estado WSTG: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

