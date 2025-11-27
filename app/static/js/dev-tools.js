/**
 * Herramientas de desarrollo para testing del frontend
 * Solo se activa en modo desarrollo (cuando FLASK_ENV=development)
 */

class DevTools {
    /**
     * Verifica si estamos en modo desarrollo
     * @returns {boolean}
     */
    static isDevelopmentMode() {
        // Verificar si existe la variable de entorno o si estamos en localhost
        return window.location.hostname === 'localhost' || 
               window.location.hostname === '127.0.0.1' ||
               window.location.hostname === '';
    }

    /**
     * Elimina todos los datos del usuario (usuario y pesos)
     * Útil para resetear el estado durante pruebas
     */
    static clearAllData() {
        if (!this.isDevelopmentMode()) {
            console.warn('DevTools solo está disponible en modo desarrollo');
            return false;
        }

        if (confirm('¿Estás seguro de que quieres eliminar todos los datos? Esta acción no se puede deshacer.')) {
            try {
                // Marcar que se están eliminando datos para evitar sincronización del backend
                // Esta bandera se eliminará después de la recarga
                sessionStorage.setItem('_skip_backend_sync', 'true');
                
                // Usar el método de LocalStorageManager si está disponible, o las claves correctas
                if (typeof LocalStorageManager !== 'undefined' && LocalStorageManager.clearAll) {
                    LocalStorageManager.clearAll();
                    console.log('Datos eliminados usando LocalStorageManager.clearAll()');
                } else {
                    // Fallback: usar las claves correctas directamente
                    localStorage.removeItem('imc_app_user');
                    localStorage.removeItem('imc_app_weights');
                    console.log('Datos eliminados usando localStorage.removeItem()');
                }
                
                // También eliminar la fecha simulada si existe
                delete window._mockDate;
                
                // Verificar que los datos se eliminaron correctamente
                const userStillExists = localStorage.getItem('imc_app_user');
                const weightsStillExist = localStorage.getItem('imc_app_weights');
                
                if (userStillExists || weightsStillExist) {
                    console.warn('Algunos datos no se eliminaron correctamente. Forzando eliminación...');
                    localStorage.removeItem('imc_app_user');
                    localStorage.removeItem('imc_app_weights');
                }
                
                console.log('Datos eliminados correctamente. Recargando página...');
                
                // Recargar la página de forma forzada para asegurar que se muestre el modal
                // Usar location.href para forzar una recarga completa desde el servidor
                setTimeout(() => {
                    window.location.href = window.location.href;
                }, 200);
                
                return true;
            } catch (error) {
                console.error('Error al eliminar datos:', error);
                alert('Error al eliminar datos. Por favor, recarga la página manualmente.');
                return false;
            }
        }
        return false;
    }

    /**
     * Simula una fecha específica para testing
     * Permite registrar pesos con fechas del pasado o futuro
     * @param {Date} mockDate - Fecha a simular (null para desactivar)
     */
    static setMockDate(mockDate) {
        if (!this.isDevelopmentMode()) {
            console.warn('DevTools solo está disponible en modo desarrollo');
            return;
        }

        if (mockDate) {
            window._mockDate = mockDate;
            console.log('Fecha simulada activada:', mockDate.toISOString());
        } else {
            delete window._mockDate;
            console.log('Fecha simulada desactivada');
        }
    }

    /**
     * Obtiene la fecha actual (real o simulada)
     * @returns {Date}
     */
    static getCurrentDate() {
        return window._mockDate ? new Date(window._mockDate) : new Date();
    }

    /**
     * Añade un peso con una fecha específica (para testing)
     * @param {number} weight_kg - Peso en kilogramos
     * @param {Date} date - Fecha específica para el registro
     * @returns {object|null} El peso añadido o null si falla
     */
    static addWeightWithDate(weight_kg, date) {
        if (!this.isDevelopmentMode()) {
            console.warn('DevTools solo está disponible en modo desarrollo');
            return null;
        }

        // Validar peso (misma validación que el formulario normal)
        const limits = AppConfig.getValidationLimits();
        if (!AppConfig.validateWeight(weight_kg)) {
            console.warn(`Peso fuera de rango: ${weight_kg} kg (rango: ${limits.weight_min}-${limits.weight_max})`);
            alert(`El peso debe estar entre ${limits.weight_min} y ${limits.weight_max} kg`);
            return null;
        }

        // Validar variación de peso (misma validación que el formulario normal)
        const lastWeightDifferentDate = LocalStorageManager.getLastWeightFromDifferentDate(date);
        if (lastWeightDifferentDate) {
            const lastDate = new Date(lastWeightDifferentDate.fecha_registro);
            const daysElapsed = Math.floor((date - lastDate) / (1000 * 60 * 60 * 24));
            
            if (daysElapsed > 0) {
                const maxAllowedDifference = AppConfig.getMaxWeightVariation(daysElapsed);
                const weightDifference = Math.abs(weight_kg - lastWeightDifferentDate.peso_kg);
                
                if (weightDifference > maxAllowedDifference) {
                    const errorMsg = `La variación de peso no puede ser mayor a ${maxAllowedDifference} kg (${daysElapsed} día(s) x ${limits.weight_variation_per_day} kg/día)`;
                    console.warn(errorMsg);
                    alert(errorMsg);
                    return null;
                }
            }
        }

        try {
            const weights = LocalStorageManager.getWeights();
            const dateStr = date.toISOString().split('T')[0]; // YYYY-MM-DD
            
            // Eliminar registros del mismo día
            const filteredWeights = weights.filter(w => {
                const weightDate = new Date(w.fecha_registro).toISOString().split('T')[0];
                return weightDate !== dateStr;
            });
            
            const newWeight = {
                id: Date.now(),
                peso_kg: parseFloat(weight_kg),
                fecha_registro: date.toISOString()
            };
            filteredWeights.push(newWeight);
            localStorage.setItem('imc_app_weights', JSON.stringify(filteredWeights));
            
            console.log('Peso añadido con fecha simulada:', newWeight);
            return newWeight;
        } catch (error) {
            console.error('Error al añadir peso con fecha simulada:', error);
            return null;
        }
    }

    /**
     * Crea el panel de herramientas de desarrollo en la UI
     */
    static createDevPanel() {
        if (!this.isDevelopmentMode()) {
            return; // No crear panel en producción
        }

        // Buscar el sidebar derecho donde insertar el panel
        const sidebarRight = document.getElementById('dev-tools-sidebar');
        if (!sidebarRight) {
            console.warn('No se encontró el sidebar derecho para herramientas de desarrollo');
            return;
        }

        // Crear contenedor del panel con el mismo estilo que la aplicación
        const devPanel = document.createElement('div');
        devPanel.id = 'dev-tools-panel';
        devPanel.className = 'panel';
        devPanel.style.cssText = `
            font-size: 14px;
            width: 100%;
            box-sizing: border-box;
        `;

        devPanel.innerHTML = `
            <h2 style="margin-top: 0; margin-bottom: 12px; color: #e2e8f0;">
                🛠️ Herramientas de Desarrollo
            </h2>
            <div id="dev-sync-status" style="margin-bottom: 12px; padding: 8px; background: #0d152c; border: 1px solid #1e293b; border-radius: 8px; font-size: 12px;">
                <span style="color: #e2e8f0;">Sincronización: </span>
                <span id="dev-sync-status-text" style="font-weight: 600;">-</span>
            </div>
            <button id="dev-toggle-sync" style="width: 100%; margin-bottom: 16px;">
                🔄 Activar/Desactivar Sincronización
            </button>
            <button id="dev-clear-data" style="width: 100%; background: #dc2626; margin-bottom: 16px;">
                🗑️ Eliminar Todos los Datos
            </button>
            <div style="margin: 16px 0; padding-top: 16px; border-top: 1px solid #1e293b;">
                <label style="display: block; margin-bottom: 4px; color: #e2e8f0;">Simular Fecha:</label>
                <input type="date" id="dev-mock-date" style="margin-bottom: 8px;">
                <div style="display: flex; gap: 8px;">
                    <button id="dev-set-date" style="flex: 1; margin: 0;">
                        Activar
                    </button>
                    <button id="dev-clear-date" style="flex: 1; margin: 0;">
                        Desactivar
                    </button>
                </div>
            </div>
            <div style="margin: 16px 0; padding-top: 16px; border-top: 1px solid #1e293b;">
                <label style="display: block; margin-bottom: 4px; color: #e2e8f0;">Añadir Peso con Fecha:</label>
                <input type="number" id="dev-weight-input" step="0.1" placeholder="Peso (kg)" style="margin-bottom: 8px;">
                <input type="date" id="dev-weight-date" style="margin-bottom: 8px;">
                <button id="dev-add-weight" style="width: 100%; margin: 0;">
                    ➕ Añadir Peso
                </button>
            </div>
            <div id="dev-status" style="margin-top: 16px; padding: 10px; background: #0d152c; border: 1px solid #1e293b; border-radius: 10px; font-size: 12px; color: #e2e8f0;">
                Fecha actual: <span id="dev-current-date" style="font-weight: 600;">-</span>
            </div>
        `;

        // Insertar el panel en el sidebar derecho
        sidebarRight.appendChild(devPanel);

        // Event listeners
        document.getElementById('dev-toggle-sync').addEventListener('click', () => {
            this.toggleSync();
        });

        document.getElementById('dev-clear-data').addEventListener('click', () => {
            this.clearAllData();
        });

        document.getElementById('dev-set-date').addEventListener('click', () => {
            const dateInput = document.getElementById('dev-mock-date');
            if (dateInput.value) {
                const mockDate = new Date(dateInput.value + 'T12:00:00');
                this.setMockDate(mockDate);
                this.updateStatus();
            }
        });

        document.getElementById('dev-clear-date').addEventListener('click', () => {
            this.setMockDate(null);
            this.updateStatus();
        });

        document.getElementById('dev-add-weight').addEventListener('click', () => {
            const weightInput = document.getElementById('dev-weight-input');
            const dateInput = document.getElementById('dev-weight-date');
            
            if (weightInput.value && dateInput.value) {
                const weight = parseFloat(weightInput.value);
                const date = new Date(dateInput.value + 'T12:00:00');
                
                if (this.addWeightWithDate(weight, date)) {
                    alert('Peso añadido correctamente');
                    weightInput.value = '';
                    dateInput.value = '';
                    // Recargar dashboard si existe la función
                    if (typeof updateDashboard === 'function') {
                        updateDashboard();
                    } else {
                        window.location.reload();
                    }
                }
            } else {
                alert('Por favor, completa peso y fecha');
            }
        });

        // Actualizar estado periódicamente
        this.updateStatus();
        this.updateSyncStatus();
        setInterval(() => {
            this.updateStatus();
            this.updateSyncStatus();
        }, 1000);
    }

    /**
     * Activa o desactiva la sincronización con el backend
     */
    static toggleSync() {
        if (!this.isDevelopmentMode()) {
            console.warn('DevTools solo está disponible en modo desarrollo');
            return;
        }

        const isCurrentlyDisabled = SyncManager.isSyncDisabled();
        SyncManager.setSyncDisabled(!isCurrentlyDisabled);
        this.updateSyncStatus();
        
        const status = !isCurrentlyDisabled ? 'DESACTIVADA' : 'ACTIVADA';
        alert(`Sincronización con backend ${status}`);
    }

    /**
     * Actualiza el estado de sincronización mostrado en el panel
     */
    static updateSyncStatus() {
        const statusTextEl = document.getElementById('dev-sync-status-text');
        const toggleButton = document.getElementById('dev-toggle-sync');
        
        if (statusTextEl && toggleButton) {
            const isDisabled = SyncManager.isSyncDisabled();
            if (isDisabled) {
                statusTextEl.textContent = 'DESACTIVADA';
                statusTextEl.style.color = '#f87171';
                toggleButton.textContent = '🔄 Activar Sincronización';
                toggleButton.style.background = '#10b981';
            } else {
                statusTextEl.textContent = 'ACTIVADA';
                statusTextEl.style.color = '#10b981';
                toggleButton.textContent = '🔄 Desactivar Sincronización';
                toggleButton.style.background = '#4f46e5';
            }
        }
    }

    /**
     * Actualiza el estado mostrado en el panel
     */
    static updateStatus() {
        const statusEl = document.getElementById('dev-current-date');
        if (statusEl) {
            const currentDate = this.getCurrentDate();
            const isMocked = !!window._mockDate;
            statusEl.textContent = isMocked 
                ? `${currentDate.toLocaleDateString()} (SIMULADA)`
                : currentDate.toLocaleDateString();
            // Usar colores del tema oscuro
            statusEl.style.color = isMocked ? '#f87171' : '#e2e8f0';
        }
    }
}

// Hacer DevTools disponible globalmente
window.DevTools = DevTools;

// Auto-inicializar en modo desarrollo
if (DevTools.isDevelopmentMode()) {
    // Esperar a que el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            DevTools.createDevPanel();
        });
    } else {
        DevTools.createDevPanel();
    }
}

