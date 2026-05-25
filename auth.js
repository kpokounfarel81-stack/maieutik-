/**
 * Gestionnaire d'authentification
 */

class AuthManager {
    constructor() {
        this.user = null;
        this.profile = null;
        this._initialized = false;
        // Ne pas initialiser ici - utiliser ensureInitialized()
    }

    /**
     * S'assurer que supabase est prêt avant d'accéder aux données
     */
    async ensureInitialized() {
        if (this._initialized) return;

        try {
            const sb = window.supabase;
            // Guard: éviter l'accès à null/undefined pendant le démarrage
            if (!sb) {
            console.warn('AuthManager: window.supabase est null (env.js probablement pas prêt).');
                this._initialized = true;
                return;
            }
            if (sb && sb.ensureReady) {
                await sb.ensureReady();
                this.initializeFromStorage();
            }
            if (sb && !sb.ensureReady) {
                this.initializeFromStorage();
            }
        } catch (e) {
            console.warn('AuthManager init:', e?.message || e);
        }

        this._initialized = true;
    }

    /**
     * Initialiser à partir du stockage local
     */
    initializeFromStorage() {
        try {
            const sb = window.supabase;
            if (!sb || !sb?.getSession) return;
            const session = sb.getSession();

            if (session && session.user) {
                this.user = session.user;
            }
        } catch {
            // ignore
        }
    }

    /**
     * Vérifier si l'utilisateur est authentifié
     */
    isAuthenticated() {
        const sb = window.supabase;
        return !!this.user && !!sb?.authToken;
    }

    /**
     * Inscription
     */
    async signup(email, password, fullName) {
        await this.ensureInitialized();
        try {
            const sb = window.supabase;
            if (!sb) {
                return { success: false, error: 'Supabase indisponible (initialisation en cours). Recharge la page et réessaie.' };
            }
            const user = await sb.signup(email, password, fullName);

            this.user = user;
            return { success: true, user };
        } catch (error) {
            console.error('Erreur inscription:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Connexion
     */
    async login(email, password) {
        await this.ensureInitialized();
        try {
            const sb = window.supabase;
            if (!sb) {
                return { success: false, error: 'Supabase indisponible (initialisation en cours). Recharge la page et réessaie.' };
            }
            const user = await sb.login(email, password);
            this.user = user;
            // Charger le profil
            this.profile = await sb.getUserProfile(user.id);
            return { success: true, user };
        } catch (error) {
            console.error('Erreur connexion:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Déconnexion
     */
    logout() {
        const sb = window.supabase;
        if (sb) sb.logout();
        this.user = null;
        this.profile = null;
        if (typeof router !== 'undefined') {
            router.navigate('home');
        }
    }

    /**
     * Récupérer l'ID utilisateur
     */
    getUserId() {
        return this.user?.id || null;
    }

    /**
     * Récupérer l'email utilisateur
     */
    getUserEmail() {
        return this.user?.email || null;
    }

    /**
     * Charger le profil utilisateur
     */
    async loadProfile() {
        await this.ensureInitialized();
        if (!this.isAuthenticated()) return null;
        const sb = window.supabase;
        this.profile = await sb.getUserProfile(this.getUserId());
        return this.profile;
    }

    /**
     * Récupérer le profil
     */
    getProfile() {
        return this.profile;
    }
}

// Initialiser le gestionnaire d'authentification
const authManager = new AuthManager();
window.authManager = authManager;

