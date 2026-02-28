import React, { useState } from 'react';
import { Send, ClipboardList } from 'lucide-react';
import { PlanCreateRequest } from '../types';

interface PlanBuilderProps {
    onCreate: (req: PlanCreateRequest) => Promise<void>;
    loading: boolean;
}

export const PlanBuilder: React.FC<PlanBuilderProps> = ({ onCreate, loading }) => {
    const [title, setTitle] = useState('');
    const [description, setDescription] = useState('');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!title || !description) return;
        onCreate({ title, task_description: description });
    };

    return (
        <div className="flex flex-col h-full bg-surface-0">
            <div className="p-6 space-y-6">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-accent-primary/10 flex items-center justify-center text-accent-primary">
                        <ClipboardList size={20} />
                    </div>
                    <div>
                        <h2 className="text-lg font-semibold text-text-primary">Nuevo Plan Orquestado</h2>
                        <p className="text-xs text-text-secondary">Define una tarea para que el orquestador la resuelva</p>
                    </div>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="space-y-1.5">
                        <label htmlFor="plan-title" className="text-[10px] uppercase tracking-widest font-bold text-text-secondary pl-1">
                            Título del Plan
                        </label>
                        <input
                            id="plan-title"
                            type="text"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            placeholder="ej., Refactorizar Módulo de Autenticación"
                            className="w-full bg-surface-2 border border-border-primary rounded-xl px-4 py-2.5 text-sm text-text-primary focus:outline-none focus:border-accent-primary transition-all placeholder:text-text-tertiary"
                            required
                        />
                    </div>

                    <div className="space-y-1.5">
                        <label htmlFor="plan-desc" className="text-[10px] uppercase tracking-widest font-bold text-text-secondary pl-1">
                            Descripción de la Tarea
                        </label>
                        <textarea
                            id="plan-desc"
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            placeholder="Describe qué quieres que haga GIMO..."
                            rows={6}
                            className="w-full bg-surface-2 border border-border-primary rounded-xl px-4 py-3 text-sm text-text-primary focus:outline-none focus:border-accent-primary transition-all placeholder:text-text-tertiary resize-none"
                            required
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={loading || !title || !description}
                        className={`
                            w-full flex items-center justify-center gap-2 py-3 rounded-xl font-bold text-xs uppercase tracking-widest transition-all
                            ${loading || !title || !description
                                ? 'bg-surface-2 text-text-tertiary cursor-not-allowed'
                                : 'bg-accent-primary text-white hover:bg-accent-primary/80 shadow-lg shadow-accent-primary/20 active:scale-[0.98]'}
                        `}
                    >
                        {loading ? (
                            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        ) : (
                            <>
                                <Send size={14} />
                                Generar Plan
                            </>
                        )}
                    </button>
                </form>
            </div>

            <div className="mt-auto p-6 border-t border-surface-2 bg-surface-0/30 mr-2 rounded-tr-3xl">
                <h3 className="text-[10px] uppercase tracking-widest font-bold text-text-tertiary mb-2 text-center">Cómo funciona</h3>
                <div className="grid grid-cols-2 gap-4">
                    <div className="text-[10px] text-text-secondary leading-relaxed">
                        <span className="text-text-primary font-semibold block mb-0.5">1. Análisis</span> GIMO escaneará el código y evaluará el estado actual.
                    </div>
                    <div className="text-[10px] text-text-secondary leading-relaxed">
                        <span className="text-text-primary font-semibold block mb-0.5">2. Delegación</span> Desglosará las tareas y las asignará a agentes especializados.
                    </div>
                </div>
            </div>
        </div>
    );
};
