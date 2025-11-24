"""
Archivo de configuración de la aplicación
Centraliza todos los valores de configuración y constantes
"""
from datetime import datetime

# Configuración de usuario (monousuario)
USER_ID = 1

# Límites de validación
VALIDATION_LIMITS = {
    "height_min": 0.4,  # metros
    "height_max": 2.72,  # metros
    "weight_min": 2,  # kilogramos
    "weight_max": 650,  # kilogramos
    "birth_date_min": datetime(1900, 1, 1).date(),
    "weight_variation_per_day": 5,  # kg por día
    "name_min_length": 1,  # caracteres mínimos
    "name_max_length": 100,  # caracteres máximos
}

# Configuración del servidor
SERVER_CONFIG = {
    "port": 5001,
    "host": "0.0.0.0",
}

# Configuración de idioma
ACTIVE_LANGUAGE = 'es'

# Lista de idiomas disponibles (códigos de idioma)
AVAILABLE_LANGUAGES = ['es']

