import React from 'react';
import { FolderOpen, Keyboard, PlugZap, Sparkles } from 'lucide-react';

interface WelcomeScreenProps {
    onNewPlan: () => void;
    onConnectProvider: () => void;
    onOpenRepo: () => void;
    onOpenCommandPalette: () => void;
}

export const WelcomeScreen: React.FC<WelcomeScreenProps> = ({
    onNewPlan,
    onConnectProvider,
    onOpenRepo,
    onOpenCommandPalette,
}) => {
    return (
        <section className="h-full w-full bg-[#0a0a0a] flex items-center justify-center p-6">
            <div className="w-full max-w-3xl rounded-2xl border border-[#2c2c2e] bg-[#111113] p-8 md:p-10">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-[#2c2c2e] bg-[#1c1c1e] text-[#86868b] text-[10px] uppercase tracking-wider mb-4">
                    <Sparkles size={12} /> PHOENIX Onboarding
                </div>
                <h1 className="text-2xl md:text-3xl font-semibold text-[#f5f5f7]">Bienvenido a GIMO Orchestrator</h1>
                <p className="mt-3 text-sm text-[#86868b] max-w-2xl">
                    No hay nodos activos en el grafo. Puedes iniciar una nueva operación, configurar providers o abrir utilidades del sistema.
                </p>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-8">
                    <button
                        onClick={onNewPlan}
                        className="h-24 rounded-xl border border-[#2c2c2e] bg-[#141414] hover:border-[#0a84ff]/40 hover:bg-[#0a84ff]/10 transition-colors text-left px-4"
                    >
                        <div className="text-[#0a84ff] mb-2"><Sparkles size={16} /></div>
                        <div className="text-sm text-[#f5f5f7] font-medium">Nuevo Plan</div>
                        <div className="text-[11px] text-[#86868b]">Comienza una planificación guiada</div>
                    </button>

                    <button
                        onClick={onConnectProvider}
                        className="h-24 rounded-xl border border-[#2c2c2e] bg-[#141414] hover:border-[#0a84ff]/40 hover:bg-[#0a84ff]/10 transition-colors text-left px-4"
                    >
                        <div className="text-[#0a84ff] mb-2"><PlugZap size={16} /></div>
                        <div className="text-sm text-[#f5f5f7] font-medium">Conectar Provider</div>
                        <div className="text-[11px] text-[#86868b]">Activa modelos y rutas de inferencia</div>
                    </button>

                    <button
                        onClick={onOpenRepo}
                        className="h-24 rounded-xl border border-[#2c2c2e] bg-[#141414] hover:border-[#0a84ff]/40 hover:bg-[#0a84ff]/10 transition-colors text-left px-4"
                    >
                        <div className="text-[#0a84ff] mb-2"><FolderOpen size={16} /></div>
                        <div className="text-sm text-[#f5f5f7] font-medium">Abrir Repo</div>
                        <div className="text-[11px] text-[#86868b]">Ir al centro de mantenimiento</div>
                    </button>
                </div>

                <button
                    onClick={onOpenCommandPalette}
                    className="mt-6 inline-flex items-center gap-2 text-xs text-[#0a84ff] hover:text-[#5aa9ff]"
                >
                    <Keyboard size={14} /> Abrir Command Palette (Ctrl+K)
                </button>
            </div>
        </section>
    );
};
