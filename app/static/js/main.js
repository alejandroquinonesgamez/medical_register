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

document.addEventListener('DOMContentLoaded', async () => {
    const userModal = document.getElementById('user-modal');
    const userForm = document.getElementById('user-form');
    const weightForm = document.getElementById('weight-form');

    const welcomeHeader = document.getElementById('welcome-header');
    const imcValue = document.getElementById('imc-value');
    const imcDescription = document.getElementById('imc-description');
    const statCount = document.getElementById('stat-count');
    const statMax = document.getElementById('stat-max');
    const statMin = document.getElementById('stat-min');

    // Cargar configuración compartida desde el backend
    await AppConfig.loadConfigFromBackend();
    
    // Actualizar límites de inputs HTML con constantes compartidas
    const limits = AppConfig.getValidationLimits();
    const tallaInput = document.getElementById('talla_m');
    if (tallaInput) {
        tallaInput.setAttribute('min', limits.height_min);
        tallaInput.setAttribute('max', limits.height_max);
    }
    
    const pesoInput = document.getElementById('peso');
    if (pesoInput) {
        pesoInput.setAttribute('min', limits.weight_min);
        pesoInput.setAttribute('max', limits.weight_max);
    }
    
    const dateInput = document.getElementById('fecha_nacimiento');
    if (dateInput) {
        const today = new Date().toISOString().split('T')[0];
        dateInput.setAttribute('max', today);
        dateInput.setAttribute('min', limits.birth_date_min);
    }
    
    // Sincronizar datos del backend al cargar la página
    try {
        await SyncManager.syncFromBackend();
    } catch (error) {
        console.warn('Error al sincronizar desde backend:', error);
        // Continuar con datos locales si falla la sincronización
    }

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

        // Validación defensiva: verificar que los datos estén dentro de los límites
        // antes de calcular el IMC (protege contra datos antiguos o corruptos)
        const limits = AppConfig.getValidationLimits();
        if (!AppConfig.validateWeight(lastWeight.peso_kg)) {
            imcValue.textContent = '0';
            imcDescription.textContent = MESSAGES.errors.weight_out_of_range || 
                `Peso fuera de rango: ${lastWeight.peso_kg} kg`;
            console.warn('Peso fuera de rango al calcular IMC:', lastWeight.peso_kg);
            return;
        }
        if (!AppConfig.validateHeight(user.talla_m)) {
            imcValue.textContent = '0';
            imcDescription.textContent = MESSAGES.errors.height_out_of_range || 
                `Talla fuera de rango: ${user.talla_m} m`;
            console.warn('Talla fuera de rango al calcular IMC:', user.talla_m);
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

    userForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const talla_m_raw = document.getElementById('talla_m').value;
        const talla_m = parseFloat(talla_m_raw);
        
        // Validar que parseFloat() retornó un número válido (no NaN ni Infinity)
        if (isNaN(talla_m) || !isFinite(talla_m)) {
            alert(MESSAGES.errors.invalid_height || 'La talla debe ser un número válido');
            return;
        }
        
        const limits = AppConfig.getValidationLimits();
        if (!AppConfig.validateHeight(talla_m)) {
            alert(MESSAGES.errors.height_out_of_range || 
                  `La talla debe estar entre ${limits.height_min} y ${limits.height_max} metros`);
            return;
        }

        // Validar y sanitizar nombre
        const nombreInput = document.getElementById('nombre').value;
        const nombreValidation = AppConfig.validateAndSanitizeName(nombreInput);
        if (!nombreValidation.isValid) {
            const errorMsg = MESSAGES.errors[nombreValidation.errorKey] || 
                           MESSAGES.errors.invalid_name || 
                           'El nombre no es válido';
            alert(errorMsg);
            return;
        }

        // Validar y sanitizar apellidos
        const apellidosInput = document.getElementById('apellidos').value;
        const apellidosValidation = AppConfig.validateAndSanitizeName(apellidosInput);
        if (!apellidosValidation.isValid) {
            const errorMsg = MESSAGES.errors[apellidosValidation.errorKey] || 
                           MESSAGES.errors.invalid_last_name || 
                           'Los apellidos no son válidos';
            alert(errorMsg);
            return;
        }

        const user = {
            nombre: nombreValidation.sanitized,
            apellidos: apellidosValidation.sanitized,
            fecha_nacimiento: document.getElementById('fecha_nacimiento').value,
            talla_m: talla_m
        };

        // Guardar en localStorage primero
        if (!LocalStorageManager.saveUser(user)) {
            alert(MESSAGES.errors.save_user || 'Error al guardar usuario');
            return;
        }

        // Sincronizar con backend
        try {
            const synced = await SyncManager.syncUserToBackend(user);
            if (!synced) {
                console.warn('Usuario guardado localmente pero no sincronizado con backend');
            }
        } catch (error) {
            console.warn('Error al sincronizar usuario:', error);
            // Continuar aunque falle la sincronización
        }

        userModal.style.display = 'none';
        updateDashboard();
    });

    weightForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const user = LocalStorageManager.getUser();
        if (!user) {
            alert(MESSAGES.errors.user_must_be_configured || 'Debes configurar tu perfil primero');
            userModal.style.display = 'flex';
            return;
        }

        const weight_kg_raw = document.getElementById('peso').value;
        const weight_kg = parseFloat(weight_kg_raw);
        
        // Validar que parseFloat() retornó un número válido (no NaN ni Infinity)
        if (isNaN(weight_kg) || !isFinite(weight_kg)) {
            alert(MESSAGES.errors.invalid_weight || 'El peso debe ser un número válido');
            return;
        }
        
        if (!weight_kg) return;

        const limits = AppConfig.getValidationLimits();
        if (!AppConfig.validateWeight(weight_kg)) {
            alert(MESSAGES.errors.weight_out_of_range || 
                  `El peso debe estar entre ${limits.weight_min} y ${limits.weight_max} kg`);
            return;
        }

        // Usar fecha simulada si está disponible (para testing)
        const today = window.DevTools && window.DevTools.getCurrentDate 
            ? window.DevTools.getCurrentDate() 
            : new Date();
        const lastWeightDifferentDate = LocalStorageManager.getLastWeightFromDifferentDate(today);
        
        if (lastWeightDifferentDate) {
            const lastDate = new Date(lastWeightDifferentDate.fecha_registro);
            const daysElapsed = Math.floor((today - lastDate) / (1000 * 60 * 60 * 24));
            
            // Validar variación respecto al último peso de un día diferente
            const maxAllowedDifference = AppConfig.getMaxWeightVariation(daysElapsed);
            const weightDifference = Math.abs(weight_kg - lastWeightDifferentDate.peso_kg);
            
            if (weightDifference > maxAllowedDifference) {
                const limits = AppConfig.getValidationLimits();
                const errorMsg = typeof MESSAGES.errors.weightVariationExceeded === 'function'
                    ? MESSAGES.errors.weightVariationExceeded(maxAllowedDifference, daysElapsed)
                    : `La variación de peso no puede ser mayor a ${maxAllowedDifference} kg (${daysElapsed} día(s) x ${limits.weight_variation_per_day} kg/día)`;
                alert(errorMsg);
                return;
            }
        }

        // Intentar sincronizar con backend primero (para validación del servidor)
        try {
            await SyncManager.syncWeightToBackend({ peso_kg: weight_kg });
            // Si la sincronización fue exitosa, guardar localmente también
        const newWeight = LocalStorageManager.addWeight({ peso_kg: weight_kg });
        if (newWeight) {
            document.getElementById('peso').value = '';
            updateDashboard();
        } else {
            alert(MESSAGES.errors.save_weight || 'Error al guardar peso');
            }
        } catch (error) {
            // Si hay error de validación del backend, mostrar el mensaje
            alert(error.message || MESSAGES.errors.save_weight || 'Error al guardar peso');
            return;
        }
    });

    updateDashboard();
});


