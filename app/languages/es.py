"""
Traducciones en español
Contiene todos los mensajes de texto en español que se muestran al usuario
"""

# Mensajes de error y validación
ERRORS = {
    "auth_required": "Autenticación requerida",
    "user_not_found": "Usuario no encontrado",
    "invalid_username": "El usuario no es válido",
    "username_too_short": "El usuario es demasiado corto",
    "username_too_long": "El usuario es demasiado largo",
    "user_already_exists": "El usuario ya existe",
    "invalid_password": "La contraseña no es válida",
    "password_too_short": "La contraseña es demasiado corta",
    "password_common": "La contraseña es demasiado común",
    "password_pwned": "La contraseña aparece en filtraciones conocidas",
    "invalid_credentials": "Usuario o contraseña incorrectos",
    "recaptcha_failed": "No se pudo verificar la validación de seguridad. Inténtalo de nuevo.",
    "invalid_height": "Altura no válida",
    "height_out_of_range": "Talla fuera de rango (0.4 - 2.72 m)",
    "invalid_birth_date": "Fecha de nacimiento no válida",
    "birth_date_out_of_range": "Fecha de nacimiento fuera de rango (1900 - hoy)",
    "user_not_configured": "Usuario no configurado",
    "user_must_be_configured": "Debe configurar el usuario primero",
    "invalid_weight": "Peso no válido",
    "weight_out_of_range": "Peso fuera de rango (2 - 650 kg)",
    "weight_variation_exceeded": "El peso no puede variar más de 5 kg por día desde el último registro. Han pasado {days_text}, por lo que la variación máxima permitida es {max_allowed_difference:.1f} kg. Diferencia actual: {weight_difference:.1f} kg",
    "invalid_name": "El nombre no es válido. Debe tener entre 1 y 100 caracteres y contener solo letras, espacios, guiones y apóstrofes.",
    "invalid_last_name": "Los apellidos no son válidos. Deben tener entre 1 y 100 caracteres y contener solo letras, espacios, guiones y apóstrofes.",
    "name_too_long": "El nombre es demasiado largo (máximo 100 caracteres)",
    "last_name_too_long": "Los apellidos son demasiado largos (máximo 100 caracteres)",
    "name_empty": "El nombre no puede estar vacío",
    "last_name_empty": "Los apellidos no pueden estar vacíos",
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

# Descripciones de BMI (clasificaciones)
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
        "invalid_username": "El usuario no es válido",
        "invalid_password": "La contraseña no es válida",
        "password_too_short": "La contraseña debe tener al menos 10 caracteres",
        "password_common": "La contraseña es demasiado común",
        "password_pwned": "La contraseña aparece en filtraciones conocidas",
        "invalid_credentials": "Usuario o contraseña incorrectos",
        "recaptcha_failed": "No se pudo verificar la validación de seguridad. Inténtalo de nuevo.",
        "height_out_of_range": "La talla debe estar entre 0.4 y 2.72 metros",
        "weight_out_of_range": "El peso debe estar entre 2 y 650 kg",
        "user_must_be_configured": "Debes configurar tu perfil primero",
        "invalid_name": "El nombre no es válido. Debe tener entre 1 y 100 caracteres y contener solo letras, espacios, guiones y apóstrofes.",
        "invalid_last_name": "Los apellidos no son válidos. Deben tener entre 1 y 100 caracteres y contener solo letras, espacios, guiones y apóstrofes.",
        "name_too_long": "El nombre es demasiado largo (máximo 100 caracteres)",
        "last_name_too_long": "Los apellidos son demasiado largos (máximo 100 caracteres)",
        "name_empty": "El nombre no puede estar vacío",
        "last_name_empty": "Los apellidos no pueden estar vacíos",
    },
    "texts": {
        "no_weight_records": "Sin registros de peso",
    },
    "bmi_descriptions": BMI_COMPLETE_DESCRIPTIONS,
}

# Textos de la interfaz HTML
HTML_TEXTS = {
    "title": "Registro de IMC",
    "subtitle": "Seguimiento de salud personal con sincronización segura",
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
    "recent_weights_title": "Últimos registros de peso",
    "welcome_modal_title": "Bienvenido",
    "welcome_modal_message": "Por favor, introduce tus datos para comenzar.",
    "name": "Nombre:",
    "last_name": "Apellidos:",
    "birth_date": "Fecha de Nacimiento:",
    "height": "Talla (en metros):",
    "save_profile": "Guardar Perfil",
    "current_user_label": "Hola,",
    "login": "Iniciar sesión",
    "register": "Registrarse",
    "logout": "Cerrar sesión",
    "username": "Usuario:",
    "password": "Contraseña:",
    "password_confirm": "Confirmar contraseña:",
    "login_action": "Iniciar sesión",
    "register_action": "Crear cuenta",
}

