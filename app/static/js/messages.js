/**
 * Archivo de mensajes para la interfaz de usuario
 * Contiene todos los textos que se muestran al usuario en JavaScript
 */

const MESSAGES = {
    errors: {
        saveWeight: 'Error al guardar el peso',
        saveUser: 'Error al guardar usuario',
        heightOutOfRange: 'La talla debe estar entre 0.4 y 2.72 metros',
        weightOutOfRange: 'El peso debe estar entre 2 y 650 kg',
        weightVariationExceeded: (maxAllowed, days) => 
            `La variación de peso no puede ser mayor a ${maxAllowed} kg (${days} día(s) x 5 kg/día)`,
        userMustBeConfigured: 'Debes configurar tu perfil primero',
    },
    texts: {
        greeting: (name) => `¡Hola, ${name}!`,
        noWeightRecords: 'Sin registros de peso',
        bmiUnderweight: 'Bajo peso',
        bmiNormal: 'Peso normal',
        bmiOverweight: 'Sobrepeso',
        bmiObese: 'Obesidad',
    }
};

