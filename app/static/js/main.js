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
    const userGreetingText = document.getElementById('user-greeting-text');
    const syncIndicator = document.getElementById('data-sync-indicator');

    // Inicializar autenticación antes de continuar
    if (window.AuthManager) {
        await AuthManager.init();
        AuthManager.onAuthChange = () => {
            updateDashboard();
        };
        AuthManager.setupUI();
    }

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
    
    function loadUser() {
        if (AuthManager && !AuthManager.isAuthenticated()) {
            if (welcomeHeader) {
                welcomeHeader.textContent = '';
            }
            if (userGreetingText) {
                userGreetingText.textContent = '';
            }
            userModal.style.display = 'none';
            return;
        }
        const user = LocalStorageManager.getUser();
        if (!user) {
            if (userGreetingText && AuthManager) {
                const authUser = AuthManager.getCurrentUser();
                userGreetingText.textContent = authUser ? `Hola, ${authUser.username}` : '';
            }
            if (welcomeHeader) {
                welcomeHeader.textContent = '';
            }
            userModal.style.display = 'flex';
            return;
        }
        if (userGreetingText) {
            userGreetingText.textContent = MESSAGES.texts.greeting(user.nombre);
        }
        if (welcomeHeader) {
            welcomeHeader.textContent = '';
        }
        userModal.style.display = 'none';
    }

    function loadIMC() {
        if (AuthManager && !AuthManager.isAuthenticated()) {
            imcValue.textContent = '--.-';
            imcDescription.textContent = 'Inicia sesión para ver tu IMC';
            return;
        }
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
        if (AuthManager && !AuthManager.isAuthenticated()) {
            statCount.textContent = '0';
            statMax.textContent = '0 kg';
            statMin.textContent = '0 kg';
            return;
        }
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

    function updateSyncIndicator() {
        if (!syncIndicator) return;
        const isSynced = typeof SyncManager !== 'undefined' && SyncManager.isSynced
            ? SyncManager.isSynced()
            : false;
        if (!isSynced) {
            syncIndicator.textContent = '💻';
            syncIndicator.title = 'Datos no sincronizados';
            syncIndicator.classList.remove('sync-indicator--remote');
            syncIndicator.classList.add('sync-indicator--local');
        } else {
            syncIndicator.textContent = '🌐';
            syncIndicator.title = 'Datos sincronizados';
            syncIndicator.classList.remove('sync-indicator--local');
            syncIndicator.classList.add('sync-indicator--remote');
        }
    }

    userForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        if (AuthManager && !AuthManager.isAuthenticated()) {
            alert('Debes iniciar sesión para guardar tu perfil');
            return;
        }
        
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

        if (AuthManager && !AuthManager.isAuthenticated()) {
            alert('Debes iniciar sesión para guardar tu peso');
            return;
        }
        
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

    // Funcionalidad de DefectDojo: Exportar e Importar Dump
    const exportDumpBtn = document.getElementById('export-dump-btn');
    const importDumpInput = document.getElementById('import-dump-input');

    if (exportDumpBtn) {
        exportDumpBtn.addEventListener('click', async () => {
            try {
                exportDumpBtn.disabled = true;
                exportDumpBtn.textContent = '⏳ Exportando...';
                
                const response = await fetch('/api/defectdojo/export-dump');
                
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.error || 'Error al exportar el dump');
                }
                
                // Descargar el archivo
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'defectdojo_db_dump.sql';
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
                exportDumpBtn.textContent = '✅ Exportado';
                setTimeout(() => {
                    exportDumpBtn.textContent = '📥 Exportar Dump';
                    exportDumpBtn.disabled = false;
                }, 2000);
                
            } catch (error) {
                alert('Error al exportar dump: ' + error.message);
                exportDumpBtn.textContent = '📥 Exportar Dump';
                exportDumpBtn.disabled = false;
            }
        });
    }

    if (importDumpInput) {
        importDumpInput.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;
            
            // Validar extensión
            if (!file.name.endsWith('.sql')) {
                alert('El archivo debe ser un dump SQL (.sql)');
                importDumpInput.value = '';
                return;
            }
            
            // Confirmar acción
            if (!confirm('¿Estás seguro de que quieres importar este dump? Esto reemplazará los datos actuales de DefectDojo.')) {
                importDumpInput.value = '';
                return;
            }
            
            try {
                const formData = new FormData();
                formData.append('file', file);
                
                const label = document.querySelector('label[for="import-dump-input"]');
                label.textContent = '⏳ Importando...';
                label.style.pointerEvents = 'none';
                
                const response = await fetch('/api/defectdojo/import-dump', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (!response.ok) {
                    throw new Error(result.error || 'Error al importar el dump');
                }
                
                alert(result.message || 'Dump importado correctamente. DefectDojo se está reiniciando.');
                label.textContent = '✅ Importado';
                
                setTimeout(() => {
                    label.textContent = '📤 Importar Dump';
                    label.style.pointerEvents = 'auto';
                    importDumpInput.value = '';
                }, 3000);
                
            } catch (error) {
                alert('Error al importar dump: ' + error.message);
                const label = document.querySelector('label[for="import-dump-input"]');
                label.textContent = '📤 Importar Dump';
                label.style.pointerEvents = 'auto';
                importDumpInput.value = '';
            }
        });
    }

    // Botón para generar PDF del informe ASVS
    const generatePdfBtn = document.getElementById('generate-pdf-btn');
    if (generatePdfBtn) {
        generatePdfBtn.addEventListener('click', async () => {
            try {
                generatePdfBtn.disabled = true;
                generatePdfBtn.textContent = '⏳ Generando...';
                
                const response = await fetch('/api/defectdojo/generate-pdf');
                
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.error || 'Error al generar el PDF');
                }
                
                // Descargar el archivo
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                
                // Obtener el nombre del archivo del header Content-Disposition o usar un nombre por defecto
                const contentDisposition = response.headers.get('Content-Disposition');
                let filename = 'INFORME_SEGURIDAD.pdf';
                if (contentDisposition) {
                    const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
                    if (filenameMatch) {
                        filename = filenameMatch[1];
                    }
                }
                
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
                generatePdfBtn.textContent = '✅ Generado';
                setTimeout(() => {
                    generatePdfBtn.textContent = '📄 Generar PDF Informe';
                    generatePdfBtn.disabled = false;
                }, 2000);
                
            } catch (error) {
                alert('Error al generar PDF: ' + error.message);
                generatePdfBtn.textContent = '📄 Generar PDF Informe';
                generatePdfBtn.disabled = false;
            }
        });
    }

    // Función para cargar y mostrar los últimos pesos
    async function loadRecentWeights() {
        const recentWeightsList = document.getElementById('recent-weights-list');
        if (!recentWeightsList) return;
        if (AuthManager && !AuthManager.isAuthenticated()) {
            recentWeightsList.innerHTML = '<li class="no-data">Inicia sesión para ver tus registros</li>';
            return;
        }

        let weights = [];

        // Función auxiliar para cargar desde localStorage
        const loadFromLocalStorage = () => {
            try {
                const allWeights = LocalStorageManager.getWeights();
                console.log('Pesos obtenidos de localStorage:', allWeights);
                
                if (allWeights.length === 0) {
                    console.log('No hay pesos en localStorage');
                    return [];
                }
                
                // Ordenar por fecha descendente y tomar los últimos 5
                const sortedWeights = allWeights.sort((a, b) => {
                    // getWeights() ya devuelve objetos Date, pero por si acaso normalizamos
                    const dateA = a.fecha_registro instanceof Date ? a.fecha_registro : new Date(a.fecha_registro);
                    const dateB = b.fecha_registro instanceof Date ? b.fecha_registro : new Date(b.fecha_registro);
                    return dateB - dateA; // Descendente
                });
                
                return sortedWeights.slice(0, 5).map(w => {
                    // Normalizar fecha a string ISO para consistencia
                    let fechaStr;
                    if (w.fecha_registro instanceof Date) {
                        fechaStr = w.fecha_registro.toISOString();
                    } else if (typeof w.fecha_registro === 'string') {
                        fechaStr = w.fecha_registro;
                    } else {
                        fechaStr = new Date(w.fecha_registro).toISOString();
                    }
                    
                    return {
                        peso_kg: w.peso_kg,
                        fecha_registro: fechaStr
                    };
                });
            } catch (localError) {
                console.error('Error al cargar desde localStorage:', localError);
                return [];
            }
        };

        // Intentar cargar desde el backend primero
        try {
            const response = await fetch('/api/weights/recent');
            if (response.ok) {
                const data = await response.json();
                weights = data.weights || [];
                
                // Si el backend devuelve un array vacío, usar localStorage como respaldo
                if (weights.length === 0) {
                    console.log('Backend devolvió array vacío, cargando desde localStorage...');
                    weights = loadFromLocalStorage();
                } else {
                    console.log('Pesos cargados desde backend:', weights);
                }
            } else {
                throw new Error('Backend no disponible');
            }
        } catch (error) {
            // Si falla el backend, usar localStorage como respaldo
            console.log('Error al cargar desde backend, usando localStorage:', error);
            weights = loadFromLocalStorage();
        }
        
        if (weights.length > 0) {
            console.log('Pesos procesados para mostrar:', weights);
        }

        // Mostrar los pesos
        if (weights.length === 0) {
            recentWeightsList.innerHTML = '<li class="no-data">No hay registros de peso aún</li>';
            return;
        }

        // Formatear y mostrar los pesos
        recentWeightsList.innerHTML = weights.map(entry => {
            try {
                // Normalizar fecha: puede venir como string ISO o como objeto Date
                let date;
                if (entry.fecha_registro instanceof Date) {
                    date = entry.fecha_registro;
                } else if (typeof entry.fecha_registro === 'string') {
                    date = new Date(entry.fecha_registro);
                } else {
                    date = new Date(entry.fecha_registro);
                }
                
                // Validar que la fecha es válida
                if (isNaN(date.getTime())) {
                    console.error('Fecha inválida:', entry.fecha_registro);
                    return `
                        <li class="recent-weight-item">
                            <span class="weight-value">${entry.peso_kg} kg</span>
                            <span class="weight-date">Fecha inválida</span>
                        </li>
                    `;
                }
                
                const formattedDate = date.toLocaleDateString('es-ES', {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric'
                });
                const formattedTime = date.toLocaleTimeString('es-ES', {
                    hour: '2-digit',
                    minute: '2-digit'
                });
                
                return `
                    <li class="recent-weight-item">
                        <span class="weight-value">${entry.peso_kg} kg</span>
                        <span class="weight-date">${formattedDate} ${formattedTime}</span>
                    </li>
                `;
            } catch (error) {
                console.error('Error al formatear peso:', entry, error);
                return `
                    <li class="recent-weight-item">
                        <span class="weight-value">${entry.peso_kg || 'N/A'} kg</span>
                        <span class="weight-date">Error al formatear fecha</span>
                    </li>
                `;
            }
        }).join('');
    }

    // Modificar updateDashboard para incluir la carga de últimos pesos
    const originalUpdateDashboard = updateDashboard;
    updateDashboard = async function() {
        originalUpdateDashboard();
        await loadRecentWeights();
    };

    // Cargar los últimos pesos al iniciar
    updateDashboard();
    updateSyncIndicator();
    setInterval(updateSyncIndicator, 2000);
});


