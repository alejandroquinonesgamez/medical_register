"""
Archivo de traducciones para la aplicación
Contiene todos los mensajes de texto que se muestran al usuario
"""

# Mensajes de error y validación
ERRORS = {
    "user_not_found": "Usuario no encontrado",
    "invalid_height": "Altura no válida",
    "height_out_of_range": "Talla fuera de rango (0.4 - 2.72 m)",
    "invalid_birth_date": "Fecha de nacimiento no válida",
    "birth_date_out_of_range": "Fecha de nacimiento fuera de rango (1900 - hoy)",
    "user_not_configured": "Usuario no configurado",
    "user_must_be_configured": "Debe configurar el usuario primero",
    "invalid_weight": "Peso no válido",
    "weight_out_of_range": "Peso fuera de rango (2 - 650 kg)",
    "weight_variation_exceeded": "El peso no puede variar más de 5 kg por día desde el último registro. Han pasado {days_text}, por lo que la variación máxima permitida es {max_allowed_difference:.1f} kg. Diferencia actual: {weight_difference:.1f} kg",
}

# Mensajes de éxito
MESSAGES = {
    "user_saved": "Usuario guardado",
    "weight_registered": "Peso registrado",
}

# Descripciones de BMI
BMI_DESCRIPTIONS = {
    "underweight": "Bajo peso",
    "normal": "Peso normal",
    "overweight": "Sobrepeso",
    "obese": "Obesidad",
}

# Textos de días para validación de peso
DAYS_TEXT = {
    "same_day": "mismo día",
    "one_day": "1 día",
    "multiple_days": "{days} días",
}

# Otros textos
TEXTS = {
    "no_weight_records": "Sin registros de peso",
}

# Textos de la interfaz HTML
HTML_TEXTS = {
    "title": "Registro de IMC",
    "welcome_header_loading": "Cargando...",
    "register_weight": "Registrar Peso",
    "current_weight": "Peso actual (kg):",
    "save_weight": "Guardar Peso",
    "current_status": "Tu Estado Actual",
    "imc_loading": "Cargando...",
    "statistics": "Estadísticas",
    "total_weighings": "Pesajes Totales:",
    "max_weight": "Peso Máximo:",
    "min_weight": "Peso Mínimo:",
    "welcome_modal_title": "Bienvenido",
    "welcome_modal_message": "Por favor, introduce tus datos para comenzar.",
    "name": "Nombre:",
    "last_name": "Apellidos:",
    "birth_date": "Fecha de Nacimiento:",
    "height": "Talla (en metros):",
    "save_profile": "Guardar Perfil",
}

def get_error(key, **kwargs):
    """Obtiene un mensaje de error formateado"""
    message = ERRORS.get(key, key)
    if kwargs:
        return message.format(**kwargs)
    return message


def get_message(key):
    """Obtiene un mensaje de éxito"""
    return MESSAGES.get(key, key)


def get_bmi_description(key):
    """Obtiene la descripción de BMI"""
    return BMI_DESCRIPTIONS.get(key, key)


def get_days_text(days):
    """Obtiene el texto de días transcurridos"""
    if days == 0:
        return DAYS_TEXT["same_day"]
    elif days == 1:
        return DAYS_TEXT["one_day"]
    else:
        return DAYS_TEXT["multiple_days"].format(days=days)


def get_text(key, **kwargs):
    """Obtiene un texto general formateado"""
    message = TEXTS.get(key, key)
    if kwargs:
        return message.format(**kwargs)
    return message

