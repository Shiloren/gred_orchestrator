import { useState, type FormEvent } from 'react';
import { signInWithPopup } from 'firebase/auth';
import { API_BASE } from '../types';
import { auth, googleProvider, isFirebaseConfigured } from '../lib/firebase';
import { useToast } from './Toast';
import { AuthGraphBackground } from './AuthGraphBackground';

interface Props {
    onAuthenticated: () => void;
}

export function LoginModal({ onAuthenticated }: Props) {
    const { addToast } = useToast();
    const [token, setToken] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [googleLoading, setGoogleLoading] = useState(false);
    const [loading, setLoading] = useState(false);

    const handleGoogleLogin = async () => {
        if (!isFirebaseConfigured() || !auth || !googleProvider) {
            setError('Firebase no está configurado. Revisa variables VITE_FIREBASE_*');
            return;
        }

        setError(null);
        setGoogleLoading(true);

        try {
            const credentials = await signInWithPopup(auth, googleProvider);
            const idToken = await credentials.user.getIdToken();

            const res = await fetch(`${API_BASE}/auth/firebase-login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ idToken }),
            });

            if (!res.ok) {
                const data = await res.json().catch(() => ({ detail: 'Error de conexion' }));
                setError(data.detail || `HTTP ${res.status}`);
                return;
            }

            addToast('Sesión iniciada con Google', 'success');
            onAuthenticated();
        } catch {
            setError('No se pudo iniciar sesión con Google');
        } finally {
            setGoogleLoading(false);
        }
    };

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        setError(null);
        setLoading(true);

        try {
            const res = await fetch(`${API_BASE}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ token: token.trim() }),
            });

            if (!res.ok) {
                const data = await res.json().catch(() => ({ detail: 'Error de conexion' }));
                setError(data.detail || `HTTP ${res.status}`);
                return;
            }

            onAuthenticated();
        } catch {
            setError('No se puede conectar al servidor');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="relative min-h-screen overflow-hidden bg-[#090c14] flex items-center justify-center p-6">
            <AuthGraphBackground />

            <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(66,176,255,0.16),transparent_42%),radial-gradient(circle_at_80%_80%,rgba(13,110,253,0.10),transparent_38%),linear-gradient(180deg,rgba(5,8,16,0.35),rgba(5,8,16,0.82))]" />

            <div className="relative z-10 w-full max-w-sm bg-[#2c2c2e]/88 backdrop-blur-xl rounded-2xl border border-[#3a3a3c]/90 shadow-[0_25px_80px_rgba(0,0,0,0.55)] p-8 space-y-6">
                <div className="text-center space-y-1">
                    <h1 className="text-xl font-semibold text-white">GIMO</h1>
                    <p className="text-sm text-[#b0b6c3]">Inicia sesión con tu cuenta de Google</p>
                </div>

                <button
                    type="button"
                    onClick={handleGoogleLogin}
                    disabled={googleLoading}
                    className="w-full py-3 bg-[#0a84ff] text-white text-sm font-medium rounded-xl hover:bg-[#0a84ff]/80 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                    {googleLoading ? 'Conectando con Google...' : 'Iniciar sesión con Google'}
                </button>

                <details className="rounded-xl border border-[#3a3a3c] bg-[#1b1f2a]/92 p-3">
                    <summary className="cursor-pointer text-xs text-[#9aa3b6]">Acceso por token local (desarrollo)</summary>
                    <form onSubmit={handleSubmit} className="space-y-3 mt-3">
                        <div className="space-y-2">
                            <input
                                type="password"
                                value={token}
                                onChange={(e) => setToken(e.target.value)}
                                placeholder="Token"
                                className="w-full px-4 py-3 bg-[#131722] border border-[#3a3a3c] rounded-xl text-white text-sm placeholder-[#636b7c] focus:outline-none focus:border-[#0a84ff] transition-colors"
                            />
                        </div>
                        <button
                            type="submit"
                            disabled={loading || !token.trim()}
                            className="w-full py-3 bg-[#3a3a3c] text-white text-sm font-medium rounded-xl hover:bg-[#48484a] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                        >
                            {loading ? 'Verificando...' : 'Entrar con token'}
                        </button>
                    </form>
                </details>

                {error && (
                    <p className="text-xs text-[#ff5d55]">{error}</p>
                )}

                <p className="text-[10px] text-[#6a7080] text-center">
                    Si usas token local, revisa <code className="text-[#8a93a6]">.orch_token</code>
                </p>
            </div>
        </div>
    );
}
