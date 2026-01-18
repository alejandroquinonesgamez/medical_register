/**
 * Tests de CAJA NEGRA para SyncManager
 * Prueban la sincronización entre frontend y backend
 */

// Importar SyncManager (copiamos la clase para testing)
class SyncManager {
    static async syncFromBackend() {
        try {
            const userResponse = await fetch('/api/user');
            if (userResponse.ok) {
                const userData = await userResponse.json();
                const user = {
                    nombre: userData.nombre,
                    apellidos: userData.apellidos,
                    fecha_nacimiento: userData.fecha_nacimiento,
                    talla_m: userData.talla_m
                };
                // Simular LocalStorageManager.saveUser
                localStorage.setItem('imc_app_user', JSON.stringify(user));
            } else if (userResponse.status !== 404) {
                console.warn('Error al sincronizar usuario desde backend:', userResponse.status);
            }

            const weightsResponse = await fetch('/api/weights');
            if (weightsResponse.ok) {
                const weightsData = await weightsResponse.json();
                const backendWeights = weightsData.weights || [];
                const frontendWeights = backendWeights.map(w => ({
                    id: w.id,
                    peso_kg: w.peso_kg,
                    fecha_registro: w.fecha_registro
                }));
                if (frontendWeights.length > 0) {
                    localStorage.setItem('imc_app_weights', JSON.stringify(frontendWeights));
                }
            } else if (weightsResponse.status === 404) {
                // Mantener pesos locales
            } else {
                console.warn('Error al sincronizar pesos desde backend:', weightsResponse.status);
            }
            return true;
        } catch (error) {
            console.warn('Error al sincronizar desde backend (modo offline):', error);
            return false;
        }
    }

    static async syncUserToBackend(user) {
        try {
            const response = await fetch('/api/user', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    nombre: user.nombre,
                    apellidos: user.apellidos,
                    fecha_nacimiento: user.fecha_nacimiento,
                    talla_m: user.talla_m
                })
            });

            if (response.ok) {
                return true;
            } else {
                const errorData = await response.json();
                console.error('Error al sincronizar usuario al backend:', errorData.error);
                return false;
            }
        } catch (error) {
            console.warn('Error al sincronizar usuario al backend (modo offline):', error);
            return false;
        }
    }

    static async syncWeightToBackend(weight) {
        try {
            const response = await fetch('/api/weight', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    peso_kg: weight.peso_kg
                })
            });

            if (response.ok) {
                return true;
            } else {
                const errorData = await response.json();
                if (response.status === 400) {
                    const validationError = new Error(errorData.error || 'Error de validación');
                    validationError.isValidationError = true;
                    throw validationError;
                }
                return false;
            }
        } catch (error) {
            if (error.isValidationError) {
                throw error;
            }
            console.warn('Error al sincronizar peso al backend (modo offline):', error);
            return false;
        }
    }
}

describe('TestSyncManager', () => {
    beforeEach(() => {
        localStorage.clear();
        fetch.mockClear();
    });

    describe('syncFromBackend', () => {
        test('test_sync_from_backend_success - Sincronización exitosa desde backend', async () => {
            const userData = {
                nombre: 'Juan',
                apellidos: 'Pérez',
                fecha_nacimiento: '1990-05-15',
                talla_m: 1.75
            };

            const weightsData = {
                weights: [
                    { id: 1, peso_kg: 70.0, fecha_registro: '2024-01-01T10:00:00' },
                    { id: 2, peso_kg: 72.5, fecha_registro: '2024-01-15T10:00:00' }
                ]
            };

            fetch
                .mockResolvedValueOnce({
                    ok: true,
                    json: async () => userData
                })
                .mockResolvedValueOnce({
                    ok: true,
                    json: async () => weightsData
                });

            const result = await SyncManager.syncFromBackend();
            expect(result).toBe(true);
            expect(fetch).toHaveBeenCalledTimes(2);
            expect(fetch).toHaveBeenCalledWith('/api/user');
            expect(fetch).toHaveBeenCalledWith('/api/weights');

            const savedUser = JSON.parse(localStorage.getItem('imc_app_user'));
            expect(savedUser.nombre).toBe('Juan');
            expect(savedUser.talla_m).toBe(1.75);
        });

        test('test_sync_from_backend_no_user - Sincronización cuando no hay usuario en backend', async () => {
            fetch
                .mockResolvedValueOnce({
                    ok: false,
                    status: 404
                })
                .mockResolvedValueOnce({
                    ok: false,
                    status: 404
                });

            const result = await SyncManager.syncFromBackend();
            expect(result).toBe(true);
            expect(fetch).toHaveBeenCalledTimes(2);
        });

        test('test_sync_from_backend_offline - Sincronización falla (modo offline)', async () => {
            fetch.mockRejectedValueOnce(new Error('Network error'));

            const result = await SyncManager.syncFromBackend();
            expect(result).toBe(false);
        });
    });

    describe('syncUserToBackend', () => {
        test('test_sync_user_to_backend_success - Sincronización exitosa de usuario al backend', async () => {
            const user = {
                nombre: 'Juan',
                apellidos: 'Pérez',
                fecha_nacimiento: '1990-05-15',
                talla_m: 1.75
            };

            fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => ({ message: 'Usuario Guardado' })
            });

            const result = await SyncManager.syncUserToBackend(user);
            expect(result).toBe(true);
            expect(fetch).toHaveBeenCalledWith('/api/user', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(user)
            });
        });

        test('test_sync_user_to_backend_error - Error al sincronizar usuario', async () => {
            const user = {
                nombre: 'Juan',
                apellidos: 'Pérez',
                fecha_nacimiento: '1990-05-15',
                talla_m: 1.75
            };

            fetch.mockResolvedValueOnce({
                ok: false,
                status: 400,
                json: async () => ({ error: 'Altura no válida' })
            });

            const result = await SyncManager.syncUserToBackend(user);
            expect(result).toBe(false);
        });

        test('test_sync_user_to_backend_offline - Error de red (modo offline)', async () => {
            const user = {
                nombre: 'Juan',
                apellidos: 'Pérez',
                fecha_nacimiento: '1990-05-15',
                talla_m: 1.75
            };

            fetch.mockRejectedValueOnce(new Error('Network error'));

            const result = await SyncManager.syncUserToBackend(user);
            expect(result).toBe(false);
        });
    });

    describe('syncWeightToBackend', () => {
        test('test_sync_weight_to_backend_success - Sincronización exitosa de peso al backend', async () => {
            const weight = { peso_kg: 70.5 };

            fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => ({ message: 'Peso Registrado' })
            });

            const result = await SyncManager.syncWeightToBackend(weight);
            expect(result).toBe(true);
            expect(fetch).toHaveBeenCalledWith('/api/weight', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(weight)
            });
        });

        test('test_sync_weight_to_backend_validation_error - Error de validación del backend', async () => {
            const weight = { peso_kg: 1000 }; // Peso inválido

            fetch.mockResolvedValueOnce({
                ok: false,
                status: 400,
                json: async () => ({ error: 'Peso fuera de rango' })
            });

            await expect(SyncManager.syncWeightToBackend(weight)).rejects.toThrow('Peso fuera de rango');
        });

        test('test_sync_weight_to_backend_offline - Error de red (modo offline)', async () => {
            const weight = { peso_kg: 70.5 };

            fetch.mockRejectedValueOnce(new Error('Network error'));

            const result = await SyncManager.syncWeightToBackend(weight);
            expect(result).toBe(false);
        });
    });
});

