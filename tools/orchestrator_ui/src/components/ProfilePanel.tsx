import { useMemo } from 'react';
import { X, Copy, ExternalLink, LogOut, RefreshCw } from 'lucide-react';
import { Accordion } from './Accordion';
import { UserProfile } from '../types';
import { useToast } from './Toast';

interface ProfilePanelProps {
    isOpen: boolean;
    onClose: () => void;
    profile: UserProfile | null;
    loading: boolean;
    error: string | null;
    onRefresh: () => void;
    onLogout: () => void;
}

const GIMO_ACCOUNT_URL = 'https://gimo-web.vercel.app/account';

export function ProfilePanel({
    isOpen,
    onClose,
    profile,
    loading,
    error,
    onRefresh,
    onLogout,
}: ProfilePanelProps) {
    const { addToast } = useToast();

    const planLabel = useMemo(() => {
        const plan = profile?.license?.plan?.toLowerCase?.() || 'none';
        if (profile?.license?.isLifetime) return 'Lifetime';
        if (plan === 'standard') return 'Standard';
        if (plan === 'admin') return 'Admin';
        return 'Free';
    }, [profile]);

    const planClass =
        planLabel === 'Standard'
            ? 'bg-accent-primary/15 text-accent-primary border-accent-primary/30'
            : planLabel === 'Admin'
                ? 'bg-accent-purple/15 text-accent-purple border-accent-purple/30'
                : planLabel === 'Lifetime'
                    ? 'bg-accent-approval/15 text-accent-approval border-accent-approval/30'
                    : 'bg-status-pending/15 text-status-pending border-status-pending/30';

    const subscriptionStatus = (profile?.subscription?.status || 'none').toLowerCase();
    const subscriptionClass =
        subscriptionStatus === 'active'
            ? 'bg-accent-trust/15 text-accent-trust border-accent-trust/30'
            : subscriptionStatus === 'expired' || subscriptionStatus === 'past_due'
                ? 'bg-accent-alert/15 text-accent-alert border-accent-alert/30'
                : 'bg-status-pending/15 text-status-pending border-status-pending/30';

    const licenseStatus = (profile?.license?.status || 'none').toLowerCase();
    const licenseClass =
        licenseStatus === 'active'
            ? 'bg-accent-trust/15 text-accent-trust border-accent-trust/30'
            : licenseStatus === 'expired' || licenseStatus === 'suspended'
                ? 'bg-accent-alert/15 text-accent-alert border-accent-alert/30'
                : 'bg-status-pending/15 text-status-pending border-status-pending/30';

    const copyToClipboard = async (value: string, label: string) => {
        try {
            await navigator.clipboard.writeText(value);
            addToast(`${label} copiado`, 'success');
        } catch {
            addToast(`No se pudo copiar ${label.toLowerCase()}`, 'error');
        }
    };

    const formatDate = (value?: string | null) => {
        if (!value) return '—';
        const d = new Date(value);
        if (Number.isNaN(d.getTime())) return '—';
        return d.toLocaleDateString('es-ES', {
            day: '2-digit',
            month: 'short',
            year: 'numeric',
        });
    };

    const formatSeconds = (seconds?: number) => {
        if (!seconds || seconds <= 0) return 'expirada';
        const days = Math.floor(seconds / 86400);
        const hours = Math.floor((seconds % 86400) / 3600);
        return `${days}d ${hours}h`;
    };

    const maskedLicense = profile?.license?.keyPreview ? `••••••••${profile.license.keyPreview}` : 'No disponible';

    return (
        <div
            className={`fixed inset-0 z-[70] transition-opacity ${isOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'}`}
            aria-hidden={!isOpen}
        >
            <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />

            <aside className={`absolute right-0 top-0 h-full w-full max-w-[460px] bg-surface-1 border-l border-border-primary shadow-2xl transition-transform ${isOpen ? 'translate-x-0' : 'translate-x-full'}`}>
                <div className="h-14 border-b border-border-primary px-4 flex items-center justify-between">
                    <h2 className="text-sm font-black uppercase tracking-widest text-text-primary">Mi Perfil</h2>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={onRefresh}
                            className="w-8 h-8 rounded-lg border border-border-primary text-text-secondary hover:text-text-primary hover:bg-surface-3 inline-flex items-center justify-center"
                            title="Actualizar"
                        >
                            <RefreshCw size={14} />
                        </button>
                        <button
                            onClick={onClose}
                            className="w-8 h-8 rounded-lg border border-border-primary text-text-secondary hover:text-text-primary hover:bg-surface-3 inline-flex items-center justify-center"
                            title="Cerrar"
                        >
                            <X size={14} />
                        </button>
                    </div>
                </div>

                <div className="h-[calc(100%-56px)] overflow-y-auto custom-scrollbar p-4 space-y-4">
                    <section className="rounded-2xl border border-border-primary bg-surface-2 p-4">
                        <div className="flex items-center gap-3">
                            <div className="w-14 h-14 rounded-full overflow-hidden bg-surface-3 border border-border-primary flex items-center justify-center">
                                {profile?.user?.photoURL ? (
                                    <img src={profile.user.photoURL} alt="Avatar" className="w-full h-full object-cover" />
                                ) : (
                                    <img src="/logo-icon.png" alt="Logo" className="w-8 h-8 object-contain opacity-90" />
                                )}
                            </div>
                            <div className="min-w-0">
                                <p className="text-sm text-text-primary font-semibold truncate">{profile?.user?.displayName || 'Usuario GIMO'}</p>
                                <p className="text-xs text-text-secondary truncate">{profile?.user?.email || '—'}</p>
                            </div>
                            <span className={`ml-auto px-2 py-1 text-[10px] font-bold uppercase rounded-full border ${planClass}`}>
                                {planLabel}
                            </span>
                        </div>
                    </section>

                    <section className="rounded-2xl border border-border-primary bg-surface-2 p-4 space-y-3">
                        <div className="flex items-center justify-between">
                            <h3 className="text-xs font-black uppercase tracking-wider text-text-primary">Suscripción</h3>
                            <span className={`px-2 py-1 text-[10px] font-bold uppercase rounded-full border ${subscriptionClass}`}>
                                {profile?.subscription?.status || 'none'}
                            </span>
                        </div>
                        <div className="text-xs text-text-secondary space-y-1">
                            <p>Próximo cobro: <span className="text-text-primary">{formatDate(profile?.subscription?.currentPeriodEnd)}</span></p>
                            <p>Tarifa: <span className="text-text-primary">$3/mes</span></p>
                            {profile?.subscription?.cancelAtPeriodEnd && (
                                <p className="text-accent-warning">Se cancela el {formatDate(profile?.subscription?.currentPeriodEnd)}</p>
                            )}
                        </div>
                        <button
                            onClick={() => window.open(GIMO_ACCOUNT_URL, '_blank')}
                            className="inline-flex items-center gap-2 text-xs px-3 py-2 rounded-lg bg-accent-primary/15 text-accent-primary border border-accent-primary/30 hover:bg-accent-primary/25"
                        >
                            Gestionar suscripción
                            <ExternalLink size={12} />
                        </button>
                    </section>

                    <section className="rounded-2xl border border-border-primary bg-surface-2 p-4 space-y-3">
                        <div className="flex items-center justify-between">
                            <h3 className="text-xs font-black uppercase tracking-wider text-text-primary">Licencia</h3>
                            <span className={`px-2 py-1 text-[10px] font-bold uppercase rounded-full border ${licenseClass}`}>
                                {profile?.license?.status || 'none'}
                            </span>
                        </div>

                        <div className="flex items-center justify-between gap-2 rounded-lg border border-border-primary bg-surface-1 px-3 py-2">
                            <span className="text-xs text-text-primary font-mono truncate">{maskedLicense}</span>
                            <button
                                disabled
                                className="text-text-secondary opacity-40 cursor-not-allowed"
                                title="Solo preview (no copiable)"
                            >
                                <Copy size={14} />
                            </button>
                        </div>
                        <p className="text-[11px] text-text-secondary">
                            Se muestra solo un preview parcial por seguridad.
                        </p>

                        <div>
                            <div className="flex items-center justify-between text-[11px] text-text-secondary mb-1">
                                <span>Instalaciones</span>
                                <span>{profile?.license?.installationsUsed ?? 0} / {profile?.license?.installationsMax ?? 0}</span>
                            </div>
                            <div className="h-2 rounded-full bg-surface-3 overflow-hidden">
                                <div
                                    className="h-full bg-accent-primary"
                                    style={{
                                        width: `${Math.min(
                                            100,
                                            (((profile?.license?.installationsUsed ?? 0) / Math.max(profile?.license?.installationsMax ?? 1, 1)) * 100),
                                        )}%`,
                                    }}
                                />
                            </div>
                        </div>

                        <button
                            onClick={() => window.open(GIMO_ACCOUNT_URL, '_blank')}
                            className="inline-flex items-center gap-2 text-xs px-3 py-2 rounded-lg bg-surface-3 text-text-primary border border-border-primary hover:bg-surface-2"
                        >
                            Gestionar licencia
                            <ExternalLink size={12} />
                        </button>
                    </section>

                    <Accordion title="Sesión local" defaultOpen={false}>
                        <div className="space-y-2 text-xs text-text-secondary">
                            <p>Rol: <span className="text-text-primary">{profile?.session?.role || '—'}</span></p>
                            <div className="rounded-lg border border-border-primary bg-surface-1 px-3 py-2 text-[11px]">
                                Token de sesión protegido en cookie httpOnly (no expuesto en UI).
                            </div>
                            <p>Tiempo restante: <span className="text-text-primary">{formatSeconds(profile?.session?.expiresInSeconds)}</span></p>
                        </div>
                        <button
                            onClick={onLogout}
                            className="inline-flex items-center gap-2 text-xs px-3 py-2 rounded-lg bg-accent-alert/15 text-accent-alert border border-accent-alert/30 hover:bg-accent-alert/25"
                        >
                            <LogOut size={12} />
                            Cerrar sesión
                        </button>
                    </Accordion>

                    <Accordion title="Setup rápido" defaultOpen={false}>
                        <div className="rounded-lg border border-border-primary bg-surface-1 p-3 text-xs text-text-primary font-mono break-all">
                            gimo auth --key &lt;TU_LICENSE_KEY&gt;
                        </div>
                        <button
                            onClick={() => copyToClipboard('gimo auth --key <TU_LICENSE_KEY>', 'Comando CLI')}
                            className="inline-flex items-center gap-2 text-xs px-3 py-2 rounded-lg bg-accent-primary/15 text-accent-primary border border-accent-primary/30 hover:bg-accent-primary/25"
                        >
                            <Copy size={12} />
                            Copiar comando
                        </button>
                    </Accordion>

                    {(loading || error) && (
                        <section className="rounded-xl border border-border-primary bg-surface-2 p-3 text-xs">
                            {loading && <p className="text-text-secondary">Cargando perfil…</p>}
                            {error && <p className="text-accent-alert">{error}</p>}
                        </section>
                    )}
                </div>
            </aside>
        </div>
    );
}
