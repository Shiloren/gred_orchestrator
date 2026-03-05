import React, { useCallback, useEffect, useState } from 'react';
import { API_BASE, Skill, SkillExecuteResponse } from '../types';
import { useToast } from './Toast';
import { Zap, RefreshCw, Play, Clock, ChevronRight, Loader2, Download, Trash2, Code2 } from 'lucide-react';

// ─── Helpers ─────────────────────────────────────────────────────────────────

function relativeTime(iso?: string | null): string {
    if (!iso) return 'Never';
    const diff = Date.now() - new Date(iso).getTime();
    const m = Math.floor(diff / 60000);
    if (m < 1) return 'Just now';
    if (m < 60) return `${m}m ago`;
    const h = Math.floor(m / 60);
    if (h < 24) return `${h}h ago`;
    return `${Math.floor(h / 24)}d ago`;
}

// ─── Sub-components ───────────────────────────────────────────────────────────

interface SkillCardProps {
    skill: Skill;
    onExecute: (id: string, replaceGraph: boolean) => void;
    onLoadToGraph: (skill: Skill) => void;
    onDelete: (id: string) => void;
    executing: boolean;
    deleting: boolean;
}

const SkillCard: React.FC<SkillCardProps> = ({ skill, onExecute, onLoadToGraph, onDelete, executing, deleting }) => {
    return (
        <div className="group relative flex flex-col rounded-2xl border bg-surface-0 p-5 gap-3 transition-all duration-200 hover:border-white/20 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-black/40">
            {/* Header */}
            <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-semibold text-text-primary truncate flex items-center gap-2">
                        <Zap size={16} className="text-violet-400" />
                        {skill.name}
                    </h3>
                    <span className="inline-block text-[10px] font-mono text-text-tertiary mt-1">
                        {skill.command}
                    </span>
                </div>
            </div>

            {/* Description */}
            <p className="text-xs text-text-secondary leading-relaxed line-clamp-2">
                {skill.description || "Sin descripción"}
            </p>

            {/* Tags/Stats */}
            <div className="flex items-center gap-3 text-[10px] text-text-tertiary mt-auto pt-2 border-t border-white/5">
                <span className="flex items-center gap-1">
                    <Clock size={10} />
                    {relativeTime(skill.updated_at)}
                </span>
                <span className="flex items-center gap-1">
                    <Code2 size={10} />
                    {skill.nodes?.length || 0} nodos
                </span>
            </div>

            {/* Actions */}
            <div className="flex items-center justify-between mt-2 pt-2">
                <button
                    onClick={() => onDelete(skill.id)}
                    disabled={deleting}
                    className="flex items-center justify-center p-1.5 rounded-lg text-text-tertiary hover:text-rose-400 hover:bg-rose-500/10 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    title="Eliminar skill"
                >
                    {deleting ? <Loader2 size={14} className="animate-spin" /> : <Trash2 size={14} />}
                </button>
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => onLoadToGraph(skill)}
                        className="flex items-center gap-1.5 text-[11px] font-medium px-2.5 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-text-secondary hover:text-text-primary transition-colors border border-white/10"
                        title="Cargar al grafo visual"
                    >
                        <Download size={12} />
                        Cargar
                    </button>
                    <button
                        onClick={() => onExecute(skill.id, skill.replace_graph)}
                        disabled={executing}
                        className="flex items-center gap-1.5 text-[11px] font-medium px-2.5 py-1.5 rounded-lg bg-violet-500/10 hover:bg-violet-500/20 text-violet-400 transition-colors disabled:opacity-50 border border-violet-500/20"
                        title="Ejecutar logicamente"
                    >
                        {executing ? <Loader2 size={12} className="animate-spin" /> : <Play size={12} />}
                        Run
                    </button>
                </div>
            </div>
        </div>
    );
};

// ─── Main Panel ───────────────────────────────────────────────────────────────

export const SkillsPanel: React.FC = () => {
    const { addToast } = useToast();
    const [skills, setSkills] = useState<Skill[]>([]);
    const [loading, setLoading] = useState(true);
    const [executingId, setExecutingId] = useState<string | null>(null);
    const [deletingId, setDeletingId] = useState<string | null>(null);

    const fetchSkills = useCallback(async () => {
        try {
            const res = await fetch(`${API_BASE}/ops/skills`, { credentials: 'include' });
            if (res.ok) setSkills(await res.json());
        } catch {
            addToast('No se pudieron cargar las skills.', 'error');
        } finally {
            setLoading(false);
        }
    }, [addToast]);

    useEffect(() => { fetchSkills(); }, [fetchSkills]);

    const handleExecute = async (skillId: string, replaceGraph: boolean) => {
        setExecutingId(skillId);
        try {
            const res = await fetch(`${API_BASE}/ops/skills/${skillId}/execute`, {
                method: 'POST',
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ replace_graph: replaceGraph, context: {} }),
            });
            if (res.ok) {
                const data: SkillExecuteResponse = await res.json();
                addToast(`Ejecución en background iniciada: ${data.skill_run_id}`, 'success');
            } else {
                addToast('Fallo al ejecutar skill.', 'error');
            }
        } catch {
            addToast('Error de red al ejecutar skill.', 'error');
        } finally {
            setExecutingId(null);
        }
    };

    const handleDelete = async (skillId: string) => {
        if (!globalThis.confirm('¿Seguro de que quieres eliminar esta skill?')) return;
        setDeletingId(skillId);
        try {
            const res = await fetch(`${API_BASE}/ops/skills/${skillId}`, {
                method: 'DELETE',
                credentials: 'include',
            });
            if (res.ok) {
                addToast('Skill eliminada con éxito', 'success');
                fetchSkills();
            } else {
                addToast('No se pudo eliminar la skill.', 'error');
            }
        } catch {
            addToast('Error de red al eliminar.', 'error');
        } finally {
            setDeletingId(null);
        }
    };

    const handleLoadToGraph = (skill: Skill) => {
        // Hydrate graph via custom event to GraphCanvas
        const event = new CustomEvent('ops:load_skill_to_graph', { detail: skill });
        globalThis.dispatchEvent(event);
        addToast(`Skill ${skill.name} cargada al editor visual.`, 'info');
    };

    const renderContent = () => {
        if (loading) {
            return (
                <div className="flex items-center justify-center h-48 text-text-tertiary">
                    <Loader2 size={24} className="animate-spin" />
                </div>
            );
        }
        if (skills.length === 0) {
            return (
                <div className="flex flex-col items-center justify-center h-48 gap-3 text-text-tertiary border border-dashed border-white/8 rounded-2xl flex-1">
                    <Code2 size={24} className="text-white/20" />
                    <p className="text-xs text-center">No hay skills creadas aún.<br /><span className="text-text-tertiary/70 mt-1 block">Crea una desde el editor de Grafo ("Guardar como Skill")</span></p>
                </div>
            );
        }
        return (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {skills.map(skill => (
                    <SkillCard
                        key={skill.id}
                        skill={skill}
                        onExecute={handleExecute}
                        onLoadToGraph={handleLoadToGraph}
                        onDelete={handleDelete}
                        executing={executingId === skill.id}
                        deleting={deletingId === skill.id}
                    />
                ))}
            </div>
        );
    };

    return (
        <div className="h-full overflow-y-auto custom-scrollbar bg-surface-0 p-6 flex flex-col">
            {/* Header */}
            <div className="max-w-6xl mx-auto w-full flex flex-col flex-1">
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h1 className="text-lg font-black text-text-primary flex items-center gap-2">
                            <Zap size={20} className="text-violet-400" />
                            Skills Library
                        </h1>
                        <p className="text-xs text-text-tertiary mt-0.5">Automatizaciones reutilizables de grafo visual.</p>
                    </div>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={fetchSkills}
                            className="p-2 rounded-xl bg-white/5 hover:bg-white/10 text-text-secondary hover:text-text-primary border border-white/8 transition-colors"
                            title="Actualizar"
                        >
                            <RefreshCw size={14} />
                        </button>
                    </div>
                </div>

                {/* Grid */}
                {renderContent()}

                {/* Info callout */}
                <div className="mt-8 flex items-start gap-3 rounded-2xl border border-violet-500/15 bg-violet-500/5 p-4 mx-auto w-full">
                    <ChevronRight size={14} className="text-violet-400 mt-0.5 flex-shrink-0" />
                    <p className="text-xs text-text-secondary leading-relaxed">
                        Puedes invocar cualquier skill en el chat usando su prefijo <strong className="text-text-primary font-mono text-[10px]">/command</strong>.
                        La ejecución de fondo puede ser monitoreada desde los widgets.
                    </p>
                </div>
            </div>
        </div>
    );
};
