/**
 * Funciones de cálculo de IMC (mismo algoritmo que el backend)
 */
function calculateBMI(weight_kg, height_m) {
    if (height_m <= 0) return 0;
    return Math.round((weight_kg / (height_m ** 2)) * 10) / 10; // Redondear a 1 decimal
}

/**
 * Obtiene la descripción completa de BMI (clasificación + descripción detallada)
 * Usa un diccionario para vincular directamente el rango de BMI con su descripción
 * Mantiene consistencia con el backend
 */
function getBMIDescription(bmi) {
    // Determinar la clave según el rango de BMI
    let key;
    if (bmi < 18.5) {
        key = 'underweight';
    } else if (bmi < 25) {
        key = 'normal';
    } else if (bmi < 30) {
        key = 'overweight';
    } else if (bmi < 35) {
        key = 'obese_class_i';
    } else if (bmi < 40) {
        key = 'obese_class_ii';
    } else {
        key = 'obese_class_iii';
    }
    
    // Obtener la descripción del diccionario
    return MESSAGES.bmi_descriptions[key] || `IMC: ${bmi}`;
}

document.addEventListener('DOMContentLoaded', () => {
    const dateInput = document.getElementById('fecha_nacimiento');
    if (dateInput) {
        const today = new Date().toISOString().split('T')[0];
        dateInput.setAttribute('max', today);
    }

    const userModal = document.getElementById('user-modal');
    const userForm = document.getElementById('user-form');
    const weightForm = document.getElementById('weight-form');

    const welcomeHeader = document.getElementById('welcome-header');
    const imcValue = document.getElementById('imc-value');
    const imcDescription = document.getElementById('imc-description');
    const statCount = document.getElementById('stat-count');
    const statMax = document.getElementById('stat-max');
    const statMin = document.getElementById('stat-min');

    function loadUser() {
        const user = LocalStorageManager.getUser();
        if (!user) {
            userModal.style.display = 'flex';
            return;
        }
        welcomeHeader.textContent = MESSAGES.texts.greeting(user.nombre);
        userModal.style.display = 'none';
    }

    function loadIMC() {
        const user = LocalStorageManager.getUser();
        const lastWeight = LocalStorageManager.getLastWeight();
        
        if (!user || !lastWeight) {
            imcValue.textContent = '0';
            imcDescription.textContent = MESSAGES.texts.no_weight_records || "Sin registros de peso";
            return;
        }

        const bmi = calculateBMI(lastWeight.peso_kg, user.talla_m);
        const description = getBMIDescription(bmi);
        
        imcValue.textContent = bmi;
        imcDescription.textContent = description;
    }

    function loadStats() {
        const stats = LocalStorageManager.getStats();
        statCount.textContent = stats.num_pesajes;
        statMax.textContent = stats.peso_max + ' kg';
        statMin.textContent = stats.peso_min + ' kg';
    }

    function updateDashboard() {
        loadUser();
        loadIMC();
        loadStats();
    }

    userForm.addEventListener('submit', (e) => {
        e.preventDefault();
        
        const talla_m = parseFloat(document.getElementById('talla_m').value);
        if (talla_m < 0.4 || talla_m > 2.72) {
            alert(MESSAGES.errors.height_out_of_range || 'La talla debe estar entre 0.4 y 2.72 metros');
            return;
        }

        const user = {
            nombre: document.getElementById('nombre').value,
            apellidos: document.getElementById('apellidos').value,
            fecha_nacimiento: document.getElementById('fecha_nacimiento').value,
            talla_m: talla_m
        };

        if (LocalStorageManager.saveUser(user)) {
            userModal.style.display = 'none';
            updateDashboard();
        } else {
            alert(MESSAGES.errors.save_user || 'Error al guardar usuario');
        }
    });

    weightForm.addEventListener('submit', (e) => {
        e.preventDefault();
        
        const user = LocalStorageManager.getUser();
        if (!user) {
            alert(MESSAGES.errors.user_must_be_configured || 'Debes configurar tu perfil primero');
            userModal.style.display = 'flex';
            return;
        }

        const weight_kg = parseFloat(document.getElementById('peso').value);
        if (!weight_kg) return;

        if (weight_kg < 2 || weight_kg > 650) {
            alert(MESSAGES.errors.weight_out_of_range || 'El peso debe estar entre 2 y 650 kg');
            return;
        }

        const today = new Date();
        const lastWeightDifferentDate = LocalStorageManager.getLastWeightFromDifferentDate(today);
        
        if (lastWeightDifferentDate) {
            const lastDate = new Date(lastWeightDifferentDate.fecha_registro);
            const daysElapsed = Math.floor((today - lastDate) / (1000 * 60 * 60 * 24));
            
            // Validar variación respecto al último peso de un día diferente
            const maxAllowedDifference = daysElapsed * 5;
            const weightDifference = Math.abs(weight_kg - lastWeightDifferentDate.peso_kg);
            
            if (weightDifference > maxAllowedDifference) {
                const errorMsg = typeof MESSAGES.errors.weightVariationExceeded === 'function'
                    ? MESSAGES.errors.weightVariationExceeded(maxAllowedDifference, daysElapsed)
                    : `La variación de peso no puede ser mayor a ${maxAllowedDifference} kg (${daysElapsed} día(s) x 5 kg/día)`;
                alert(errorMsg);
                return;
            }
        }

        const newWeight = LocalStorageManager.addWeight({ peso_kg: weight_kg });
        if (newWeight) {
            document.getElementById('peso').value = '';
            updateDashboard();
        } else {
            alert(MESSAGES.errors.save_weight || 'Error al guardar peso');
        }
    });

    updateDashboard();
});


