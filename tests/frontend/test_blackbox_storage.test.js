/**
 * Tests de CAJA NEGRA para LocalStorageManager
 * Prueban el almacenamiento sin conocer la implementación interna
 * Equivalentes a tests/test_blackbox.py del backend
 */

// Importar LocalStorageManager
// En un entorno real, esto debería importarse desde el módulo
// Por ahora, copiamos la clase aquí para testing
const STORAGE_KEYS = {
    USER: 'imc_app_user',
    WEIGHTS: 'imc_app_weights'
};

class LocalStorageManager {
    static getUser() {
        const userJson = localStorage.getItem(STORAGE_KEYS.USER);
        if (!userJson) return null;
        try {
            const user = JSON.parse(userJson);
            if (user.fecha_nacimiento) {
                user.fecha_nacimiento = new Date(user.fecha_nacimiento);
            }
            return user;
        } catch (error) {
            console.error('Error al leer usuario de localStorage:', error);
            return null;
        }
    }

    static saveUser(user) {
        try {
            localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(user));
            return true;
        } catch (error) {
            console.error('Error al guardar usuario en localStorage:', error);
            return false;
        }
    }

    static getWeights() {
        const weightsJson = localStorage.getItem(STORAGE_KEYS.WEIGHTS);
        if (!weightsJson) return [];
        try {
            const weights = JSON.parse(weightsJson);
            return weights.map(w => ({
                ...w,
                fecha_registro: new Date(w.fecha_registro)
            }));
        } catch (error) {
            console.error('Error al leer pesos de localStorage:', error);
            return [];
        }
    }

    static addWeight(weight) {
        try {
            const weights = this.getWeights();
            const providedDate = weight.fecha_registro ? new Date(weight.fecha_registro) : null;
            const currentDate = providedDate || new Date();
            const today = currentDate.toISOString().split('T')[0];
            const filteredWeights = weights.filter(w => {
                const weightDate = new Date(w.fecha_registro).toISOString().split('T')[0];
                return weightDate !== today;
            });
            const newWeight = {
                id: Date.now(),
                peso_kg: parseFloat(weight.peso_kg),
                fecha_registro: currentDate.toISOString()
            };
            filteredWeights.push(newWeight);
            localStorage.setItem(STORAGE_KEYS.WEIGHTS, JSON.stringify(filteredWeights));
            return newWeight;
        } catch (error) {
            console.error('Error al guardar peso en localStorage:', error);
            return null;
        }
    }

    static getLastWeightFromDifferentDate(referenceDate) {
        const weights = this.getWeights();
        if (weights.length === 0) return null;
        const refDateStr = new Date(referenceDate).toISOString().split('T')[0];
        const differentDateWeights = weights.filter(w => {
            const weightDate = new Date(w.fecha_registro).toISOString().split('T')[0];
            return weightDate !== refDateStr;
        });
        if (differentDateWeights.length === 0) return null;
        return differentDateWeights.sort((a, b) => 
            new Date(b.fecha_registro) - new Date(a.fecha_registro)
        )[0];
    }

    static getLastWeight() {
        const weights = this.getWeights();
        if (weights.length === 0) return null;
        return weights.sort((a, b) => 
            new Date(b.fecha_registro) - new Date(a.fecha_registro)
        )[0];
    }

    static getStats() {
        const weights = this.getWeights();
        if (weights.length === 0) {
            return {
                num_pesajes: 0,
                peso_max: 0,
                peso_min: 0
            };
        }
        const pesos = weights.map(w => w.peso_kg);
        return {
            num_pesajes: weights.length,
            peso_max: Math.max(...pesos),
            peso_min: Math.min(...pesos)
        };
    }

    static clearAll() {
        localStorage.removeItem(STORAGE_KEYS.USER);
        localStorage.removeItem(STORAGE_KEYS.WEIGHTS);
    }
}

describe('TestUserStorageBlackBox', () => {
    beforeEach(() => {
        LocalStorageManager.clearAll();
    });

    test('test_create_user_complete_flow - Test flujo completo de creación de usuario', () => {
        const user = {
            nombre: 'Juan',
            apellidos: 'Pérez García',
            fecha_nacimiento: '1990-05-15',
            talla_m: 1.75
        };

        const saved = LocalStorageManager.saveUser(user);
        expect(saved).toBe(true);

        const retrieved = LocalStorageManager.getUser();
        expect(retrieved).not.toBeNull();
        expect(retrieved.nombre).toBe('Juan');
        expect(retrieved.apellidos).toBe('Pérez García');
        expect(retrieved.talla_m).toBe(1.75);
    });

    test('test_update_user_existing - Test actualización de usuario existente', () => {
        const user1 = {
            nombre: 'Juan',
            apellidos: 'Pérez',
            fecha_nacimiento: '1990-05-15',
            talla_m: 1.75
        };
        LocalStorageManager.saveUser(user1);

        const user2 = {
            nombre: 'Juan',
            apellidos: 'Pérez García',
            fecha_nacimiento: '1990-05-15',
            talla_m: 1.80
        };
        LocalStorageManager.saveUser(user2);

        const retrieved = LocalStorageManager.getUser();
        expect(retrieved.talla_m).toBe(1.80);
        expect(retrieved.apellidos).toBe('Pérez García');
    });

    test('test_get_user_not_found - Test obtener usuario cuando no existe', () => {
        const user = LocalStorageManager.getUser();
        expect(user).toBeNull();
    });
});

describe('TestWeightStorageBlackBox', () => {
    beforeEach(() => {
        LocalStorageManager.clearAll();
        // Crear usuario de prueba
        LocalStorageManager.saveUser({
            nombre: 'Juan',
            apellidos: 'Pérez',
            fecha_nacimiento: '1990-05-15',
            talla_m: 1.75
        });
    });

    test('test_add_weight_complete_flow - Test flujo completo de registro de peso', () => {
        const weight = { peso_kg: 70.5 };
        const result = LocalStorageManager.addWeight(weight);

        expect(result).not.toBeNull();
        expect(result.peso_kg).toBe(70.5);
        expect(result.id).toBeDefined();
        expect(result.fecha_registro).toBeDefined();

        const lastWeight = LocalStorageManager.getLastWeight();
        expect(lastWeight).not.toBeNull();
        expect(lastWeight.peso_kg).toBe(70.5);
    });

    test('test_add_multiple_weights - Test múltiples registros de peso', () => {
        const pesos = [70.0, 72.5, 75.0];
        const results = [];

        for (const peso of pesos) {
            // Simular diferentes días añadiendo un día entre cada peso
            const result = LocalStorageManager.addWeight({ peso_kg: peso });
            results.push(result);
            // Simular paso de tiempo modificando la fecha
            if (results.length < pesos.length) {
                const weights = LocalStorageManager.getWeights();
                const lastWeight = weights[weights.length - 1];
                const lastDate = new Date(lastWeight.fecha_registro);
                lastDate.setDate(lastDate.getDate() - 1);
                lastWeight.fecha_registro = lastDate.toISOString();
                weights[weights.length - 1] = lastWeight;
                localStorage.setItem(STORAGE_KEYS.WEIGHTS, JSON.stringify(weights));
            }
        }

        expect(results.length).toBe(3);
        const allWeights = LocalStorageManager.getWeights();
        expect(allWeights.length).toBe(3);
    });

    test('test_add_weight_same_day_replaces - Test que registros del mismo día se reemplazan', () => {
        const weight1 = { peso_kg: 70.0 };
        LocalStorageManager.addWeight(weight1);

        const weight2 = { peso_kg: 71.0 };
        LocalStorageManager.addWeight(weight2);

        const weights = LocalStorageManager.getWeights();
        expect(weights.length).toBe(1);
        expect(weights[0].peso_kg).toBe(71.0);
    });

    test('test_add_weight_without_user - Test que se puede añadir peso sin usuario (solo verifica que no crashea)', () => {
        LocalStorageManager.clearAll();
        const weight = { peso_kg: 70.0 };
        const result = LocalStorageManager.addWeight(weight);
        // El frontend permite esto, aunque el backend no
        expect(result).not.toBeNull();
    });
});

describe('TestIMCStorageBlackBox', () => {
    beforeEach(() => {
        LocalStorageManager.clearAll();
    });

    test('test_get_imc_without_user - Test cálculo de IMC sin usuario', () => {
        const user = LocalStorageManager.getUser();
        expect(user).toBeNull();
        // Sin usuario, no se puede calcular IMC
    });

    test('test_get_imc_without_weights - Test cálculo de IMC sin pesos', () => {
        LocalStorageManager.saveUser({
            nombre: 'Juan',
            apellidos: 'Pérez',
            fecha_nacimiento: '1990-05-15',
            talla_m: 1.75
        });

        const lastWeight = LocalStorageManager.getLastWeight();
        expect(lastWeight).toBeNull();
    });

    test('test_get_imc_correct_calculation - Test cálculo correcto de IMC', () => {
        LocalStorageManager.saveUser({
            nombre: 'Juan',
            apellidos: 'Pérez',
            fecha_nacimiento: '1990-05-15',
            talla_m: 1.75
        });

        LocalStorageManager.addWeight({ peso_kg: 75.0 });
        const lastWeight = LocalStorageManager.getLastWeight();
        const user = LocalStorageManager.getUser();

        // IMC = 75 / (1.75^2) = 24.5
        const bmi = Math.round((lastWeight.peso_kg / (user.talla_m ** 2)) * 10) / 10;
        expect(bmi).toBe(24.5);
    });
});

describe('TestStatsStorageBlackBox', () => {
    beforeEach(() => {
        LocalStorageManager.clearAll();
        LocalStorageManager.saveUser({
            nombre: 'Juan',
            apellidos: 'Pérez',
            fecha_nacimiento: '1990-05-15',
            talla_m: 1.75
        });
    });

    test('test_stats_empty - Test estadísticas sin pesos', () => {
        const stats = LocalStorageManager.getStats();
        expect(stats.num_pesajes).toBe(0);
        expect(stats.peso_max).toBe(0);
        expect(stats.peso_min).toBe(0);
    });

    test('test_stats_single_weight - Test estadísticas con un peso', () => {
        LocalStorageManager.addWeight({ peso_kg: 70.0 });
        const stats = LocalStorageManager.getStats();
        expect(stats.num_pesajes).toBe(1);
        expect(stats.peso_max).toBe(70.0);
        expect(stats.peso_min).toBe(70.0);
    });

    test('test_stats_multiple_weights - Test estadísticas con múltiples pesos', () => {
        const weights_data = [
            { peso_kg: 70.0 },
            { peso_kg: 72.5 },
            { peso_kg: 75.0 },
            { peso_kg: 73.0 }
        ];

        const baseDate = new Date();
        weights_data.forEach((weight, index) => {
            const date = new Date(baseDate);
            date.setDate(baseDate.getDate() - index);
            LocalStorageManager.addWeight({
                ...weight,
                fecha_registro: date.toISOString()
            });
        });

        const stats = LocalStorageManager.getStats();
        expect(stats.num_pesajes).toBe(4);
        expect(stats.peso_max).toBe(75.0);
        expect(stats.peso_min).toBe(70.0);
    });
});

