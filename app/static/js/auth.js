class AuthManager {
    static _currentUser = null;
    static _ui = null;
    static onAuthChange = null;
    static _csrfToken = null;

    static async init() {
        try {
            const response = await fetch('/api/auth/me', { credentials: 'same-origin' });
            if (!response.ok) {
                this._currentUser = null;
                return;
            }
            const data = await response.json();
            this._currentUser = { user_id: data.user_id, username: data.username };
            this._csrfToken = data.csrf_token || null;
            if (typeof LocalStorageManager !== 'undefined') {
                LocalStorageManager.setUserId(data.user_id);
            }
        } catch (error) {
            console.error('Error al inicializar sesión:', error);
            this._currentUser = null;
        }
    }

    static isAuthenticated() {
        return !!this._currentUser;
    }

    static getCurrentUser() {
        return this._currentUser;
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

    static async login(usernameInput, password) {
        const username = this._normalizeUsername(usernameInput);
        if (!username) {
            throw new Error('El usuario no es válido');
        }
        if (!password) {
            throw new Error('La contraseña es obligatoria');
        }
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify({ username, password })
        });
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || 'Usuario o contraseña incorrectos');
        }
        const data = await response.json();
        this._currentUser = { user_id: data.user_id, username: data.username };
        this._csrfToken = data.csrf_token || null;
        this._updateUI();
        if (typeof LocalStorageManager !== 'undefined') {
            LocalStorageManager.setUserId(data.user_id);
        }
    }

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
        const response = await fetch('/api/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify({ username, password })
        });
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || 'Error al registrar');
        }
        const data = await response.json();
        this._currentUser = { user_id: data.user_id, username: data.username };
        this._csrfToken = data.csrf_token || null;
        this._updateUI();
        if (typeof LocalStorageManager !== 'undefined') {
            LocalStorageManager.setUserId(data.user_id);
        }
    }

    static logout() {
        fetch('/api/auth/logout', {
            method: 'POST',
            credentials: 'same-origin',
            headers: this._csrfToken ? { 'X-CSRF-Token': this._csrfToken } : {}
        }).catch(() => {});
        this._currentUser = null;
        this._csrfToken = null;
        this._updateUI();
        if (typeof LocalStorageManager !== 'undefined') {
            LocalStorageManager.clearUserContext();
        }
    }

    static getCsrfToken() {
        return this._csrfToken;
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
