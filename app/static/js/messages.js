/**
 * Archivo de mensajes para la interfaz de usuario
 * Estructura modular similar a translations.py del backend
 * Puede cargar mensajes desde el backend o usar valores por defecto
 */

// Mensajes por defecto (fallback si no se pueden cargar del backend)
const DEFAULT_MESSAGES = {
    errors: {
        save_weight: 'Error al guardar el peso',
        save_user: 'Error al guardar usuario',
        height_out_of_range: 'La talla debe estar entre 0.4 y 2.72 metros',
        weight_out_of_range: 'El peso debe estar entre 2 y 650 kg',
        user_must_be_configured: 'Debes configurar tu perfil primero',
    },
    texts: {
        no_weight_records: 'Sin registros de peso',
    },
    bmi_descriptions: {
        underweight: 'Peso Bajo - Tu IMC está por debajo del rango considerado saludable. Es recomendable consultar con un profesional de la salud para evaluar tu situación nutricional.',
        normal: 'Peso Normal - Tu IMC está dentro del rango considerado saludable. Mantén una alimentación equilibrada y actividad física regular.',
        overweight: 'Sobrepeso - Tu IMC indica sobrepeso. Se recomienda adoptar hábitos saludables como una dieta balanceada y ejercicio regular. Consulta con un profesional de la salud para un plan personalizado.',
        obese_class_i: 'Obesidad Clase I - Tu IMC indica obesidad de grado I. Es importante adoptar cambios en el estilo de vida con supervisión médica. Una dieta equilibrada y actividad física regular pueden ayudar a mejorar tu salud.',
        obese_class_ii: 'Obesidad Clase II - Tu IMC indica obesidad de grado II. Se recomienda consultar urgentemente con un profesional de la salud para desarrollar un plan de tratamiento personalizado que incluya dieta, ejercicio y posiblemente apoyo médico.',
        obese_class_iii: 'Obesidad Clase III - Tu IMC indica obesidad de grado III (obesidad mórbida). Es fundamental buscar atención médica especializada para desarrollar un plan de tratamiento integral que priorice tu salud y bienestar.',
    }
};

// Objeto global de mensajes (se inicializa con valores por defecto)
let MESSAGES = JSON.parse(JSON.stringify(DEFAULT_MESSAGES));

// Funciones helper que no pueden venir del backend
MESSAGES.errors.weightVariationExceeded = (maxAllowed, days) => {
    if (days === 1) {
        return `El peso no puede variar más de ${maxAllowed} kg en 1 día`;
    } else {
        return `El peso no puede variar más de ${maxAllowed} kg en ${days} días`;
    }
};

MESSAGES.texts.greeting = (name) => `¡Hola, ${name}!`;

/**
 * Carga los mensajes desde el backend
 * Si falla, usa los mensajes por defecto
 */
async function loadMessagesFromBackend() {
    try {
        const response = await fetch('/api/messages');
        if (response.ok) {
            const backendMessages = await response.json();
            // Fusionar mensajes del backend con los helpers locales
            MESSAGES = {
                errors: {
                    ...backendMessages.errors,
                    weightVariationExceeded: MESSAGES.errors.weightVariationExceeded
                },
                texts: {
                    ...backendMessages.texts,
                    greeting: MESSAGES.texts.greeting
                },
                bmi_descriptions: backendMessages.bmi_descriptions
            };
        }
    } catch (error) {
        console.warn('No se pudieron cargar los mensajes del backend, usando valores por defecto:', error);
    }
}

// Cargar mensajes del backend al inicializar (opcional, no bloqueante)
loadMessagesFromBackend();

