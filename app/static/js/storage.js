/**
 * Sistema de almacenamiento usando localStorage
 * Permite persistir datos en el navegador del cliente
 */

const STORAGE_KEYS = {
    USER: 'imc_app_user',
    WEIGHTS: 'imc_app_weights'
};

class LocalStorageManager {
    static _userId = null;

    static setUserId(userId) {
        this._userId = userId ? String(userId) : null;
    }

    static clearUserContext() {
        this._userId = null;
    }

    static _getScopedKey(baseKey) {
        if (!this._userId) {
            return baseKey;
        }
        return `${baseKey}_${this._userId}`;
    }

    /**
     * Obtiene el usuario almacenado
     */
    static getUser() {
        const userJson = localStorage.getItem(this._getScopedKey(STORAGE_KEYS.USER));
        if (!userJson) return null;
        try {
            const user = JSON.parse(userJson);
            // Convertir fecha de string a Date
            if (user.fecha_nacimiento) {
                user.fecha_nacimiento = new Date(user.fecha_nacimiento);
            }
            return user;
        } catch (error) {
            console.error('Error al leer usuario de localStorage:', error);
            return null;
        }
    }

    /**
     * Guarda el usuario
     */
    static saveUser(user) {
        try {
            localStorage.setItem(this._getScopedKey(STORAGE_KEYS.USER), JSON.stringify(user));
            return true;
        } catch (error) {
            console.error('Error al guardar usuario en localStorage:', error);
            return false;
        }
    }

    /**
     * Obtiene todos los registros de peso
     */
    static getWeights() {
        const weightsJson = localStorage.getItem(this._getScopedKey(STORAGE_KEYS.WEIGHTS));
        if (!weightsJson) return [];
        try {
            const weights = JSON.parse(weightsJson);
            // Convertir fechas de string a Date
            return weights.map(w => ({
                ...w,
                fecha_registro: new Date(w.fecha_registro)
            }));
        } catch (error) {
            console.error('Error al leer pesos de localStorage:', error);
            return [];
        }
    }

    /**
     * Guarda todos los registros de peso
     */
    static saveWeights(weights) {
        try {
            localStorage.setItem(this._getScopedKey(STORAGE_KEYS.WEIGHTS), JSON.stringify(weights));
            return true;
        } catch (error) {
            console.error('Error al guardar pesos en localStorage:', error);
            return false;
        }
    }

    /**
     * Añade un nuevo registro de peso
     * Si ya existe un registro del mismo día, lo reemplaza
     */
    static addWeight(weight) {
        try {
            const weights = this.getWeights();
            const providedDate = weight.fecha_registro ? new Date(weight.fecha_registro) : null;
            const devtoolsDate = window.DevTools && window.DevTools.getCurrentDate
                ? window.DevTools.getCurrentDate()
                : null;
            const currentDate = providedDate || devtoolsDate || new Date();
            const today = currentDate.toISOString().split('T')[0]; // YYYY-MM-DD
            
            // Eliminar registros del mismo día
            const filteredWeights = weights.filter(w => {
                const weightDate = new Date(w.fecha_registro).toISOString().split('T')[0];
                return weightDate !== today;
            });
            
            // Validar que parseFloat() retornó un número válido (no NaN ni Infinity)
            const peso_kg_parsed = parseFloat(weight.peso_kg);
            if (isNaN(peso_kg_parsed) || !isFinite(peso_kg_parsed)) {
                console.error('Error: peso_kg no es un número válido:', weight.peso_kg);
                return null;
            }
            
            const newWeight = {
                id: Date.now(), // ID único basado en timestamp
                peso_kg: peso_kg_parsed,
                fecha_registro: currentDate.toISOString()
            };
            filteredWeights.push(newWeight);
            this.saveWeights(filteredWeights);
            return newWeight;
        } catch (error) {
            console.error('Error al guardar peso en localStorage:', error);
            return null;
        }
    }
    
    /**
     * Obtiene el último registro de peso de un día diferente a la fecha de referencia
     */
    static getLastWeightFromDifferentDate(referenceDate) {
        const weights = this.getWeights();
        if (weights.length === 0) return null;
        
        const refDateStr = new Date(referenceDate).toISOString().split('T')[0];
        
        // Filtrar pesos de fechas diferentes
        const differentDateWeights = weights.filter(w => {
            const weightDate = new Date(w.fecha_registro).toISOString().split('T')[0];
            return weightDate !== refDateStr;
        });
        
        if (differentDateWeights.length === 0) return null;
        
        // Ordenar por fecha descendente y tomar el primero
        return differentDateWeights.sort((a, b) => 
            new Date(b.fecha_registro) - new Date(a.fecha_registro)
        )[0];
    }

    /**
     * Obtiene el último registro de peso
     */
    static getLastWeight() {
        const weights = this.getWeights();
        if (weights.length === 0) return null;
        // Ordenar por fecha descendente y tomar el primero
        return weights.sort((a, b) => 
            new Date(b.fecha_registro) - new Date(a.fecha_registro)
        )[0];
    }

    /**
     * Obtiene estadísticas de pesos
     */
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

    /**
     * Limpia todos los datos (útil para testing o reset)
     */
    static clearAll() {
        localStorage.removeItem(this._getScopedKey(STORAGE_KEYS.USER));
        localStorage.removeItem(this._getScopedKey(STORAGE_KEYS.WEIGHTS));
    }
}

