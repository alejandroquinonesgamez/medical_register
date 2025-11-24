/**
 * Sistema de configuración compartida entre frontend y backend
 * Carga constantes de validación desde el backend con fallback local
 */

// Valores por defecto (fallback si el backend no está disponible)
const DEFAULT_VALIDATION_LIMITS = {
    height_min: 0.4,
    height_max: 2.72,
    weight_min: 2,
    weight_max: 650,
    birth_date_min: '1900-01-01',
    weight_variation_per_day: 5,
    name_min_length: 1,
    name_max_length: 100
};

// Configuración actual (se actualiza desde el backend)
let VALIDATION_LIMITS = { ...DEFAULT_VALIDATION_LIMITS };

/**
 * Carga la configuración desde el backend
 * @returns {Promise<boolean>} true si se cargó exitosamente
 */
async function loadConfigFromBackend() {
    try {
        const response = await fetch('/api/config');
        if (response.ok) {
            const config = await response.json();
            VALIDATION_LIMITS = {
                height_min: config.validation_limits.height_min,
                height_max: config.validation_limits.height_max,
                weight_min: config.validation_limits.weight_min,
                weight_max: config.validation_limits.weight_max,
                birth_date_min: config.validation_limits.birth_date_min,
                weight_variation_per_day: config.validation_limits.weight_variation_per_day,
                name_min_length: config.validation_limits.name_min_length || 1,
                name_max_length: config.validation_limits.name_max_length || 100
            };
            return true;
        }
    } catch (error) {
        console.warn('No se pudo cargar configuración desde backend, usando valores por defecto:', error);
    }
    return false;
}

/**
 * Obtiene los límites de validación actuales
 * @returns {object} Objeto con los límites de validación
 */
function getValidationLimits() {
    return { ...VALIDATION_LIMITS };
}

/**
 * Valida la altura
 * @param {number} height_m - Altura en metros
 * @returns {boolean} true si es válida
 */
function validateHeight(height_m) {
    return height_m >= VALIDATION_LIMITS.height_min && 
           height_m <= VALIDATION_LIMITS.height_max;
}

/**
 * Valida el peso
 * @param {number} weight_kg - Peso en kilogramos
 * @returns {boolean} true si es válido
 */
function validateWeight(weight_kg) {
    return weight_kg >= VALIDATION_LIMITS.weight_min && 
           weight_kg <= VALIDATION_LIMITS.weight_max;
}

/**
 * Valida la fecha de nacimiento
 * @param {string} dateString - Fecha en formato YYYY-MM-DD
 * @returns {boolean} true si es válida
 */
function validateBirthDate(dateString) {
    const date = new Date(dateString);
    const minDate = new Date(VALIDATION_LIMITS.birth_date_min);
    const maxDate = new Date();
    return date >= minDate && date <= maxDate;
}

/**
 * Calcula la variación máxima permitida de peso
 * @param {number} daysElapsed - Días transcurridos
 * @returns {number} Variación máxima permitida en kg
 */
function getMaxWeightVariation(daysElapsed) {
    return daysElapsed * VALIDATION_LIMITS.weight_variation_per_day;
}

/**
 * Valida y sanitiza un nombre o apellido
 * @param {string} name - Nombre o apellido a validar
 * @param {number} minLength - Longitud mínima (opcional)
 * @param {number} maxLength - Longitud máxima (opcional)
 * @returns {object} {isValid: boolean, sanitized: string, errorKey: string|null}
 */
function validateAndSanitizeName(name, minLength = null, maxLength = null) {
    const limits = getValidationLimits();
    const min = minLength !== null ? minLength : limits.name_min_length;
    const max = maxLength !== null ? maxLength : limits.name_max_length;
    
    // Verificar que sea string
    if (typeof name !== 'string') {
        return { isValid: false, sanitized: '', errorKey: 'invalid_name' };
    }
    
    // Eliminar espacios al inicio y final
    let sanitized = name.trim();
    
    // Validar que no esté vacío
    if (!sanitized) {
        return { isValid: false, sanitized: '', errorKey: 'name_empty' };
    }
    
    // Validar longitud
    if (sanitized.length > max) {
        return { isValid: false, sanitized: '', errorKey: 'name_too_long' };
    }
    if (sanitized.length < min) {
        return { isValid: false, sanitized: '', errorKey: 'invalid_name' };
    }
    
    // Eliminar caracteres peligrosos: < > " '
    sanitized = sanitized.replace(/[<>"']/g, '');
    
    // Normalizar espacios múltiples a un solo espacio
    sanitized = sanitized.replace(/\s+/g, ' ');
    
    // Validar que solo contenga caracteres permitidos: letras, espacios, guiones, apóstrofes
    // Permitir letras Unicode (incluye acentos y caracteres internacionales)
    for (let i = 0; i < sanitized.length; i++) {
        const char = sanitized[i];
        if (!(char.match(/[\p{L}]/u) || char === ' ' || char === '-' || char === "'")) {
            return { isValid: false, sanitized: '', errorKey: 'invalid_name' };
        }
    }
    
    // Verificar que no sean solo espacios después de la sanitización
    if (!sanitized.trim()) {
        return { isValid: false, sanitized: '', errorKey: 'invalid_name' };
    }
    
    return { isValid: true, sanitized: sanitized.trim(), errorKey: null };
}

// Inicializar configuración cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        loadConfigFromBackend();
    });
} else {
    loadConfigFromBackend();
}

// Exportar para uso global
window.AppConfig = {
    getValidationLimits,
    validateHeight,
    validateWeight,
    validateBirthDate,
    getMaxWeightVariation,
    validateAndSanitizeName,
    loadConfigFromBackend
};

