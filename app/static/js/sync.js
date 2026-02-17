/**
 * Sistema de sincronización entre frontend (localStorage) y backend (API)
 * Mantiene los datos sincronizados entre ambos sistemas
 */

class SyncManager {
    /**
     * Indica si se debe forzar modo offline en frontend
     * @returns {boolean}
     */
    static shouldForceOffline() {
        return typeof window !== 'undefined' && window.__FORCE_API_OFFLINE__ === true;
    }

    /**
     * Marca el estado de sincronización
     * @param {boolean} synced
     */
    static setSyncStatus(synced) {
        this._lastSyncOk = synced === true;
    }

    /**
     * Indica si el último intento de sync fue exitoso
     * @returns {boolean}
     */
    static isSynced() {
        return this._lastSyncOk === true;
    }
    /**
     * Verifica si la sincronización está desactivada
     * @returns {boolean}
     */
    static isSyncDisabled() {
        return localStorage.getItem('_sync_disabled') === 'true';
    }

    /**
     * Activa o desactiva la sincronización con el backend
     * @param {boolean} disabled - true para desactivar, false para activar
     */
    static setSyncDisabled(disabled) {
        if (disabled) {
            localStorage.setItem('_sync_disabled', 'true');
            this.setSyncStatus(false);
            console.log('Sincronización con backend DESACTIVADA');
        } else {
            localStorage.removeItem('_sync_disabled');
            this.setSyncStatus(false);
            console.log('Sincronización con backend ACTIVADA');
        }
    }

    /**
     * Sincroniza los datos del backend al frontend (localStorage)
     * @returns {Promise<boolean>} true si la sincronización fue exitosa
     */
    static async syncFromBackend() {
        if (this.shouldForceOffline()) {
            this.setSyncStatus(false);
            console.warn('Modo local: simulando error de comunicación con el servidor');
            return false;
        }
        // Verificar si la sincronización está desactivada manualmente
        if (this.isSyncDisabled()) {
            console.log('Sincronización omitida: desactivada manualmente');
            this.setSyncStatus(false);
            return false;
        }

        // Verificar si se debe omitir la sincronización (por ejemplo, después de eliminar datos)
        const skipSync = sessionStorage.getItem('_skip_backend_sync');
        if (skipSync === 'true') {
            console.log('Sincronización omitida: se acaban de eliminar datos localmente');
            // Eliminar la bandera después de usarla
            sessionStorage.removeItem('_skip_backend_sync');
            this.setSyncStatus(false);
            return false;
        }
        
        try {
            let syncOk = true;
            // Sincronizar usuario
            const userResponse = await AuthManager.authenticatedFetch('/api/user');
            if (userResponse.ok) {
                const userData = await userResponse.json();
                // Convertir formato del backend al formato del frontend
                const user = {
                    nombre: userData.nombre,
                    apellidos: userData.apellidos,
                    fecha_nacimiento: userData.fecha_nacimiento,
                    talla_m: userData.talla_m
                };
                LocalStorageManager.saveUser(user);
            } else if (userResponse.status !== 404) {
                // Si es 404, simplemente no hay usuario (normal)
                // Otros errores se registran
                console.warn('Error al sincronizar usuario desde backend:', userResponse.status);
                syncOk = false;
            }

            // Sincronizar pesos
            const weightsResponse = await AuthManager.authenticatedFetch('/api/weights');
            if (weightsResponse.ok) {
                const weightsData = await weightsResponse.json();
                const backendWeights = weightsData.weights || [];
                
                // Convertir formato del backend al formato del frontend
                const frontendWeights = backendWeights.map(w => ({
                    id: w.id,
                    peso_kg: w.peso_kg,
                    fecha_registro: w.fecha_registro
                }));
                
                // Fusionar pesos del backend con los locales
                // Prioridad: backend (más reciente y autoritativo)
                const localWeights = LocalStorageManager.getWeights();
                const mergedWeights = [...frontendWeights];
                
                // Añadir pesos locales que no estén en el backend (por fecha)
                const backendDates = new Set(
                    frontendWeights.map(w => new Date(w.fecha_registro).toISOString().split('T')[0])
                );
                
                localWeights.forEach(localWeight => {
                    const localDate = new Date(localWeight.fecha_registro).toISOString().split('T')[0];
                    if (!backendDates.has(localDate)) {
                        // Si no hay peso del backend para esta fecha, añadir el local
                        mergedWeights.push(localWeight);
                    }
                });
                
                // Ordenar por fecha descendente
                mergedWeights.sort((a, b) => 
                    new Date(b.fecha_registro) - new Date(a.fecha_registro)
                );
                
                // Guardar pesos fusionados
                if (mergedWeights.length > 0) {
                    LocalStorageManager.saveWeights(mergedWeights);
                } else if (frontendWeights.length > 0) {
                    // Si no hay pesos locales pero sí del backend, usar solo los del backend
                    LocalStorageManager.saveWeights(frontendWeights);
                }
            } else if (weightsResponse.status === 404) {
                // Si no hay usuario en el backend, mantener pesos locales
                // Esto es normal si el usuario aún no se ha sincronizado
            } else {
                console.warn('Error al sincronizar pesos desde backend:', weightsResponse.status);
                syncOk = false;
            }

            this.setSyncStatus(syncOk);
            return syncOk;
        } catch (error) {
            this.setSyncStatus(false);
            // Diferenciar tipos de errores para mejor debugging
            if (error instanceof TypeError) {
                console.warn('Error de tipo al sincronizar desde backend:', error.message);
            } else if (error instanceof SyntaxError) {
                console.warn('Error de sintaxis al sincronizar desde backend:', error.message);
            } else if (error instanceof NetworkError || error.name === 'NetworkError') {
                console.warn('Error de red al sincronizar desde backend (modo offline):', error.message);
            } else {
                console.warn('Error al sincronizar desde backend (modo offline):', error);
            }
            return false;
        }
    }

    /**
     * Sincroniza el usuario al backend
     * @param {object} user - Objeto usuario
     * @returns {Promise<boolean>} true si la sincronización fue exitosa
     */
    static async syncUserToBackend(user) {
        if (this.shouldForceOffline()) {
            this.setSyncStatus(false);
            console.warn('Modo local: simulando error de comunicación con el servidor');
            return false;
        }
        if (this.isSyncDisabled()) {
            console.log('Sincronización omitida: desactivada manualmente');
            this.setSyncStatus(false);
            return true; // Retornar true para que el frontend continúe normalmente
        }

        try {
            const response = await AuthManager.authenticatedFetch('/api/user', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    nombre: user.nombre,
                    apellidos: user.apellidos,
                    fecha_nacimiento: user.fecha_nacimiento,
                    talla_m: user.talla_m
                })
            });

            if (response.ok) {
                this.setSyncStatus(true);
                return true;
            } else {
                const errorData = await response.json();
                console.error('Error al sincronizar usuario al backend:', errorData.error);
                this.setSyncStatus(false);
                return false;
            }
        } catch (error) {
            this.setSyncStatus(false);
            console.warn('Error al sincronizar usuario al backend (modo offline):', error);
            return false;
        }
    }

    /**
     * Sincroniza un peso al backend
     * @param {object} weight - Objeto peso con peso_kg
     * @returns {Promise<boolean>} true si la sincronización fue exitosa
     */
    static async syncWeightToBackend(weight) {
        if (this.shouldForceOffline()) {
            this.setSyncStatus(false);
            console.warn('Modo local: simulando error de comunicación con el servidor');
            return false;
        }
        if (this.isSyncDisabled()) {
            console.log('Sincronización omitida: desactivada manualmente');
            this.setSyncStatus(false);
            return true; // Retornar true para que el frontend continúe normalmente
        }

        try {
            const response = await AuthManager.authenticatedFetch('/api/weight', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    peso_kg: weight.peso_kg
                })
            });

            if (response.ok) {
                this.setSyncStatus(true);
                return true;
            } else {
                const errorData = await response.json();
                console.error('Error al sincronizar peso al backend:', errorData.error);
                // Si el error es de validación, lanzamos el error para que el frontend lo maneje
                if (response.status === 400) {
                    this.setSyncStatus(false);
                    throw new Error(errorData.error || 'Error de validación');
                }
                this.setSyncStatus(false);
                return false;
            }
        } catch (error) {
            // Si es un error de validación, lo relanzamos
            if (error.message && error.message.includes('Error')) {
                this.setSyncStatus(false);
                throw error;
            }
            this.setSyncStatus(false);
            console.warn('Error al sincronizar peso al backend (modo offline):', error);
            return false;
        }
    }

    /**
     * Sincroniza todos los pesos locales al backend
     * Útil para sincronización inicial o recuperación
     * @returns {Promise<number>} Número de pesos sincronizados exitosamente
     */
    static async syncAllWeightsToBackend() {
        if (this.shouldForceOffline()) {
            this.setSyncStatus(false);
            console.warn('Modo local: simulando error de comunicación con el servidor');
            return 0;
        }
        if (this.isSyncDisabled()) {
            console.log('Sincronización omitida: desactivada manualmente');
            this.setSyncStatus(false);
            return 0;
        }

        const weights = LocalStorageManager.getWeights();
        let syncedCount = 0;

        for (const weight of weights) {
            try {
                const success = await this.syncWeightToBackend(weight);
                if (success) {
                    syncedCount++;
                }
                // Pequeña pausa para no sobrecargar el servidor
                await new Promise(resolve => setTimeout(resolve, 100));
            } catch (error) {
                // Si hay error de validación, lo registramos pero continuamos
                console.warn(`Error al sincronizar peso ${weight.id}:`, error.message);
            }
        }

        return syncedCount;
    }
}

// Exportar para uso global
window.SyncManager = SyncManager;
SyncManager._lastSyncOk = false;

