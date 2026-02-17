/**
 * Gestor de autenticación JWT
 *
 * Esquema de seguridad:
 * - Access token (corta vida ~15 min): almacenado SOLO en memoria (_accessToken).
 *   No se guarda en localStorage ni cookies accesibles desde JS → mitiga XSS.
 * - Refresh token (larga vida ~7 días): cookie HttpOnly establecida por el servidor.
 *   No accesible desde JavaScript → protegido contra XSS.
 * - Al recargar la página: se llama a /api/auth/refresh para obtener un nuevo
 *   access token usando la cookie HttpOnly del refresh token.
 * - authenticatedFetch(): wrapper de fetch() que añade Authorization: Bearer
 *   y reintenta automáticamente con refresh si recibe 401.
 */
class AuthManager {
    static _currentUser = null;
    static _ui = null;
    static onAuthChange = null;
    static _accessToken = null;
    static _refreshing = null;

    /**
     * Inicializa la sesión intentando obtener un access token
     * desde el refresh token (cookie HttpOnly).
     */
    static async init() {
        try {
            const refreshed = await this._refreshAccessToken();
            if (!refreshed) {
                this._currentUser = null;
                this._accessToken = null;
            }
        } catch (error) {
            console.error('Error al inicializar sesión:', error);
            this._currentUser = null;
            this._accessToken = null;
        }
    }

    static isAuthenticated() {
        return !!this._currentUser && !!this._accessToken;
    }

    static getCurrentUser() {
        return this._currentUser;
    }

    /**
     * Devuelve el rol del usuario actual ("admin" o "user").
     * Retorna null si no está autenticado.
     */
    static getCurrentRole() {
        return this._currentUser ? this._currentUser.role : null;
    }

    static isAdmin() {
        return this.getCurrentRole() === 'admin';
    }

    static setupUI() {
        const modal = document.getElementById('auth-modal');
        const loginForm = document.getElementById('login-form');
        const registerForm = document.getElementById('register-form');
        const loginOpenBtn = document.getElementById('login-open-btn');
        const registerOpenBtn = document.getElementById('register-open-btn');
        const logoutBtn = document.getElementById('logout-btn');
        const currentUser = document.getElementById('current-user');
        const currentUsername = document.getElementById('current-username');
        const authError = document.getElementById('auth-error');
        const tabButtons = document.querySelectorAll('[data-auth-tab]');
        const tabPanels = document.querySelectorAll('[data-auth-panel]');

        const showError = (message) => {
            if (!authError) return;
            authError.textContent = message;
            authError.style.display = 'block';
        };
        const clearError = () => {
            if (!authError) return;
            authError.textContent = '';
            authError.style.display = 'none';
        };

        const setActiveTab = (tabId) => {
            tabButtons.forEach(button => {
                button.classList.toggle('active', button.dataset.authTab === tabId);
            });
            tabPanels.forEach(panel => {
                panel.style.display = panel.dataset.authPanel === tabId ? 'block' : 'none';
            });
            clearError();
        };

        const openModal = (tabId) => {
            if (!modal) return;
            setActiveTab(tabId);
            modal.style.display = 'flex';
        };

        const closeModal = () => {
            if (!modal) return;
            modal.style.display = 'none';
            clearError();
        };

        if (loginOpenBtn) {
            loginOpenBtn.addEventListener('click', () => openModal('login'));
        }
        if (registerOpenBtn) {
            registerOpenBtn.addEventListener('click', () => openModal('register'));
        }
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => {
                AuthManager.logout();
                if (typeof AuthManager.onAuthChange === 'function') {
                    AuthManager.onAuthChange(null);
                }
                openModal('login');
            });
        }

        if (modal) {
            modal.addEventListener('click', (event) => {
                if (event.target === modal) {
                    closeModal();
                }
            });
        }

        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                openModal(button.dataset.authTab);
            });
        });

        if (loginForm) {
            loginForm.addEventListener('submit', async (event) => {
                event.preventDefault();
                clearError();
                const username = loginForm.querySelector('#login-username').value;
                const password = loginForm.querySelector('#login-password').value;
                try {
                    await AuthManager.login(username, password);
                    closeModal();
                    if (typeof AuthManager.onAuthChange === 'function') {
                        AuthManager.onAuthChange(AuthManager.getCurrentUser());
                    }
                } catch (error) {
                    showError(error.message || 'Error al iniciar sesión');
                }
            });
        }

        if (registerForm) {
            registerForm.addEventListener('submit', async (event) => {
                event.preventDefault();
                clearError();
                const username = registerForm.querySelector('#register-username').value;
                const password = registerForm.querySelector('#register-password').value;
                const confirmPassword = registerForm.querySelector('#register-password-confirm').value;
                try {
                    await AuthManager.register(username, password, confirmPassword);
                    closeModal();
                    if (typeof AuthManager.onAuthChange === 'function') {
                        AuthManager.onAuthChange(AuthManager.getCurrentUser());
                    }
                } catch (error) {
                    showError(error.message || 'Error al registrar');
                }
            });
        }

        this._ui = {
            currentUser,
            currentUsername,
            loginOpenBtn,
            registerOpenBtn,
            logoutBtn
        };
        this._updateUI();
        if (!this.isAuthenticated()) {
            openModal('login');
        }
    }

    static _updateUI() {
        if (!this._ui) return;
        const { currentUser, currentUsername, loginOpenBtn, registerOpenBtn, logoutBtn } = this._ui;
        const isAuthed = this.isAuthenticated();
        if (currentUser && currentUsername) {
            currentUser.style.display = isAuthed ? 'inline-flex' : 'none';
            currentUsername.textContent = isAuthed ? this._currentUser.username : '-';
        }
        if (loginOpenBtn) loginOpenBtn.style.display = isAuthed ? 'none' : 'inline-flex';
        if (registerOpenBtn) registerOpenBtn.style.display = isAuthed ? 'none' : 'inline-flex';
        if (logoutBtn) logoutBtn.style.display = isAuthed ? 'inline-flex' : 'none';
    }

    static async _getRecaptchaToken(action) {
        const siteKey = (typeof AppConfig !== 'undefined' && AppConfig.getRecaptchaSiteKey) ? AppConfig.getRecaptchaSiteKey() : '';
        if (!siteKey) return '';
        await this._loadRecaptchaScript(siteKey);
        return new Promise((resolve) => {
            if (window.grecaptcha && window.grecaptcha.execute) {
                window.grecaptcha.ready(() => {
                    window.grecaptcha.execute(siteKey, { action }).then(resolve).catch(() => resolve(''));
                });
            } else {
                resolve('');
            }
        });
    }

    static _loadRecaptchaScript(siteKey) {
        if (window.grecaptcha) return Promise.resolve();
        if (document.querySelector('script[src*="recaptcha/api.js"]')) {
            return new Promise((resolve) => {
                if (window.grecaptcha) return resolve();
                const t = setInterval(() => {
                    if (window.grecaptcha) { clearInterval(t); resolve(); }
                }, 50);
            });
        }
        return new Promise((resolve) => {
            const script = document.createElement('script');
            script.src = `https://www.google.com/recaptcha/api.js?render=${encodeURIComponent(siteKey)}`;
            script.async = true;
            script.onload = () => resolve();
            script.onerror = () => resolve();
            document.head.appendChild(script);
        });
    }

    /**
     * Inicia sesión. El servidor devuelve access_token en el body
     * y establece el refresh_token como cookie HttpOnly.
     */
    static async login(usernameInput, password) {
        const username = this._normalizeUsername(usernameInput);
        if (!username) {
            throw new Error('El usuario no es válido');
        }
        if (!password) {
            throw new Error('La contraseña es obligatoria');
        }
        const recaptchaToken = await this._getRecaptchaToken('login');
        const body = { username, password };
        if (recaptchaToken) body.recaptcha_token = recaptchaToken;
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify(body)
        });
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || 'Usuario o contraseña incorrectos');
        }
        const data = await response.json();
        this._accessToken = data.access_token;
        this._currentUser = { user_id: data.user_id, username: data.username, role: data.role || 'user' };
        this._updateUI();
        if (typeof LocalStorageManager !== 'undefined') {
            LocalStorageManager.setUserId(data.user_id);
        }
    }

    /**
     * Registra un nuevo usuario. Mismo esquema que login.
     */
    static async register(usernameInput, password, confirmPassword) {
        const username = this._normalizeUsername(usernameInput);
        if (!username) {
            throw new Error('El usuario no es válido');
        }
        if (!password || password.length < 10) {
            throw new Error('La contraseña debe tener al menos 10 caracteres');
        }
        if (password !== confirmPassword) {
            throw new Error('Las contraseñas no coinciden');
        }
        const recaptchaToken = await this._getRecaptchaToken('register');
        const body = { username, password };
        if (recaptchaToken) body.recaptcha_token = recaptchaToken;
        const response = await fetch('/api/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify(body)
        });
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || 'Error al registrar');
        }
        const data = await response.json();
        this._accessToken = data.access_token;
        this._currentUser = { user_id: data.user_id, username: data.username, role: data.role || 'user' };
        this._updateUI();
        if (typeof LocalStorageManager !== 'undefined') {
            LocalStorageManager.setUserId(data.user_id);
        }
    }

    /**
     * Cierra sesión. Envía el access token para autorizar la operación.
     * El servidor blacklistea el refresh token y limpia la cookie.
     */
    static logout() {
        if (this._accessToken) {
            fetch('/api/auth/logout', {
                method: 'POST',
                credentials: 'same-origin',
                headers: { 'Authorization': `Bearer ${this._accessToken}` }
            }).catch(() => {});
        }
        this._currentUser = null;
        this._accessToken = null;
        this._updateUI();
        if (typeof LocalStorageManager !== 'undefined') {
            LocalStorageManager.clearUserContext();
        }
    }

    /**
     * Obtiene el access token actual (solo para uso interno de authenticatedFetch).
     */
    static getAccessToken() {
        return this._accessToken;
    }

    /**
     * Intenta obtener un nuevo access token usando el refresh token cookie.
     * Devuelve true si se obtuvo correctamente.
     */
    static async _refreshAccessToken() {
        // Evitar refresh concurrentes
        if (this._refreshing) {
            return this._refreshing;
        }
        this._refreshing = (async () => {
            try {
                const response = await fetch('/api/auth/refresh', {
                    method: 'POST',
                    credentials: 'same-origin',
                });
                if (!response.ok) {
                    this._accessToken = null;
                    this._currentUser = null;
                    return false;
                }
                const data = await response.json();
                this._accessToken = data.access_token;
                this._currentUser = { user_id: data.user_id, username: data.username, role: data.role || 'user' };
                if (typeof LocalStorageManager !== 'undefined') {
                    LocalStorageManager.setUserId(data.user_id);
                }
                return true;
            } catch {
                this._accessToken = null;
                this._currentUser = null;
                return false;
            } finally {
                this._refreshing = null;
            }
        })();
        return this._refreshing;
    }

    /**
     * Wrapper de fetch() que:
     * 1. Añade Authorization: Bearer <access_token>
     * 2. Si recibe 401 (token expirado), hace refresh y reintenta UNA vez
     *
     * Usar en lugar de fetch() para todas las peticiones autenticadas.
     */
    static async authenticatedFetch(url, options = {}) {
        if (!this._accessToken) {
            const refreshed = await this._refreshAccessToken();
            if (!refreshed) {
                throw new Error('No autenticado');
            }
        }

        options.headers = {
            ...options.headers,
            'Authorization': `Bearer ${this._accessToken}`
        };
        options.credentials = 'same-origin';

        let response = await fetch(url, options);

        // Si el access token expiró, intentar refresh y reintentar
        if (response.status === 401) {
            const refreshed = await this._refreshAccessToken();
            if (refreshed) {
                options.headers['Authorization'] = `Bearer ${this._accessToken}`;
                response = await fetch(url, options);
            }
        }

        return response;
    }

    static _normalizeUsername(username) {
        if (!username || typeof username !== 'string') return '';
        const normalized = username.trim().toLowerCase();
        if (!/^[a-z0-9._-]{3,30}$/.test(normalized)) {
            return '';
        }
        return normalized;
    }
}

window.AuthManager = AuthManager;
