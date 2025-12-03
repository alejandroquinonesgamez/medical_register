"""
Funciones auxiliares para la aplicación médica

Este módulo contiene funciones de utilidad para:
- Cálculo de IMC (Índice de Masa Corporal)
- Clasificación de IMC según categorías de la OMS
- Validación y sanitización de nombres (resuelve CWE-20)
  - Valida longitud (1-100 caracteres)
  - Elimina caracteres peligrosos (< > " ')
  - Normaliza espacios múltiples
  - Valida caracteres permitidos (letras Unicode, espacios, guiones, apóstrofes)
"""
import re
from .translations import get_bmi_complete_description


def calculate_bmi(weight_kg, height_m):
    if height_m <= 0:
        return 0
    return round(weight_kg / (height_m ** 2), 1)


def get_bmi_description(bmi):
    """Devuelve la clasificación de BMI con su descripción detallada"""
    # Diccionario que vincula el rango de BMI con la clave de descripción
    # La descripción está vinculada directamente a la clasificación
    if bmi < 18.5:
        key = "underweight"
    elif 18.5 <= bmi < 25:
        key = "normal"
    elif 25 <= bmi < 30:
        key = "overweight"
    elif 30 <= bmi < 35:
        key = "obese_class_i"
    elif 35 <= bmi < 40:
        key = "obese_class_ii"
    else:  # bmi >= 40
        key = "obese_class_iii"
    
    return get_bmi_complete_description(key)


def validate_and_sanitize_name(name, min_length=1, max_length=100):
    """
    Valida y sanitiza un nombre o apellido.
    
    Permite:
    - Letras (incluyendo acentos y caracteres internacionales)
    - Espacios
    - Guiones (-)
    - Apóstrofes (')
    
    Elimina:
    - Caracteres peligrosos: < > " ' (comillas dobles y simples)
    - Espacios múltiples (normaliza a un solo espacio)
    - Espacios al inicio y final
    
    Args:
        name: String con el nombre a validar
        min_length: Longitud mínima permitida
        max_length: Longitud máxima permitida
    
    Returns:
        tuple: (is_valid: bool, sanitized_name: str, error_key: str or None)
    """
    if not isinstance(name, str):
        return False, "", "invalid_name"
    
    # Eliminar espacios al inicio y final
    name = name.strip()
    
    # Validar que no esté vacío
    if not name:
        return False, "", "name_empty"
    
    # Validar longitud
    if len(name) > max_length:
        return False, "", "name_too_long"
    if len(name) < min_length:
        return False, "", "invalid_name"
    
    # Eliminar caracteres peligrosos que podrían causar problemas de renderizado o seguridad
    # Eliminar: < > " ' (comillas dobles y simples)
    dangerous_chars = ['<', '>', '"', "'"]
    for char in dangerous_chars:
        name = name.replace(char, '')
    
    # Normalizar espacios múltiples a un solo espacio
    name = re.sub(r'\s+', ' ', name)
    
    # Validar que solo contenga caracteres permitidos
    # Permitir: letras (incluyendo Unicode), espacios, guiones, apóstrofes
    # Verificar manualmente que todos los caracteres sean letras, espacios, guiones o apóstrofes
    for char in name:
        if not (char.isalpha() or char.isspace() or char == '-' or char == "'"):
            return False, "", "invalid_name"
    
    # Verificar que no sean solo espacios después de la sanitización
    if not name.strip():
        return False, "", "invalid_name"
    
    return True, name, None


