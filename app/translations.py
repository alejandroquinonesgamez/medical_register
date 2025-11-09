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
    "user_saved": "Usuario Guardado",
    "weight_registered": "Peso Registrado",
}

# Descripciones completas de BMI (clasificación + descripción detallada)
BMI_COMPLETE_DESCRIPTIONS = {
    "underweight": "Peso Bajo - Tu IMC está por debajo del rango considerado saludable. Es recomendable consultar con un profesional de la salud para evaluar tu situación nutricional.",
    "normal": "Peso Normal - Tu IMC está dentro del rango considerado saludable. Mantén una alimentación equilibrada y actividad física regular.",
    "overweight": "Sobrepeso - Tu IMC indica sobrepeso. Se recomienda adoptar hábitos saludables como una dieta balanceada y ejercicio regular. Consulta con un profesional de la salud para un plan personalizado.",
    "obese_class_i": "Obesidad Clase I - Tu IMC indica obesidad de grado I. Es importante adoptar cambios en el estilo de vida con supervisión médica. Una dieta equilibrada y actividad física regular pueden ayudar a mejorar tu salud.",
    "obese_class_ii": "Obesidad Clase II - Tu IMC indica obesidad de grado II. Se recomienda consultar urgentemente con un profesional de la salud para desarrollar un plan de tratamiento personalizado que incluya dieta, ejercicio y posiblemente apoyo médico.",
    "obese_class_iii": "Obesidad Clase III - Tu IMC indica obesidad de grado III (obesidad mórbida). Es fundamental buscar atención médica especializada para desarrollar un plan de tratamiento integral que priorice tu salud y bienestar.",
}

# Descripciones de BMI (clasificaciones) - mantenido para compatibilidad si se necesita
BMI_DESCRIPTIONS = {
    "underweight": "Peso Bajo",
    "normal": "Peso Normal",
    "overweight": "Sobrepeso",
    "obese_class_i": "Obesidad Clase I",
    "obese_class_ii": "Obesidad Clase II",
    "obese_class_iii": "Obesidad Clase III",
}

# Textos de días para validación de peso
# Diccionario que vincula directamente el número de días con su texto formateado
DAYS_TEXT_MAP = {
    0: "mismo día",
    1: "1 día",
    # Para múltiples días, se formatea dinámicamente
}

DAYS_TEXT_TEMPLATE = "{days} días"

# Otros textos
TEXTS = {
    "no_weight_records": "Sin registros de peso",
}

# Mensajes para el frontend (JavaScript)
FRONTEND_MESSAGES = {
    "errors": {
        "save_weight": "Error al guardar el peso",
        "save_user": "Error al guardar usuario",
        "height_out_of_range": "La talla debe estar entre 0.4 y 2.72 metros",
        "weight_out_of_range": "El peso debe estar entre 2 y 650 kg",
        "user_must_be_configured": "Debes configurar tu perfil primero",
    },
    "texts": {
        "no_weight_records": "Sin registros de peso",
    },
    "bmi_descriptions": BMI_COMPLETE_DESCRIPTIONS,
}

# Textos de la interfaz HTML
HTML_TEXTS = {
    "title": "Registro de IMC",
    "welcome_header_loading": "Cargando...",
    "register_weight": "Registrar Peso",
    "current_weight": "Peso Actual (kg):",
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
    """Obtiene la descripción de BMI (clasificación)"""
    return BMI_DESCRIPTIONS.get(key, key)


def get_bmi_complete_description(key):
    """Obtiene la descripción completa de BMI (clasificación + descripción detallada)"""
    return BMI_COMPLETE_DESCRIPTIONS.get(key, "")


def get_days_text(days):
    """Obtiene el texto de días transcurridos"""
    return DAYS_TEXT_MAP.get(days, DAYS_TEXT_TEMPLATE.format(days=days))


def get_text(key, **kwargs):
    """Obtiene un texto general formateado"""
    message = TEXTS.get(key, key)
    if kwargs:
        return message.format(**kwargs)
    return message


def get_frontend_messages():
    """Obtiene todos los mensajes para el frontend"""
    return FRONTEND_MESSAGES


def get_weight_variation_error_message(max_allowed, days):
    """Obtiene el mensaje de error de variación de peso con formato singular/plural"""
    if days == 1:
        return f"El peso no puede variar más de {max_allowed} kg en 1 día"
    else:
        return f"El peso no puede variar más de {max_allowed} kg en {days} días"

