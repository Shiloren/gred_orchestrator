import React, { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Zap, CheckCircle2, XCircle, Loader2, Clock } from 'lucide-react';
import { useAppStore } from '../stores/appStore';
import { SkillRun } from '../types';

interface RunItemProps {
    run: SkillRun;
    onDismiss: (id: string) => void;
}

const RunItem: React.FC<RunItemProps> = ({ run, onDismiss }) => {
    const isFinished = run.status === 'completed' || run.status === 'failed' || run.status === 'error';

    useEffect(() => {
        if (isFinished) {
            const timer = setTimeout(() => {
                onDismiss(run.id);
            }, 5000);
            return () => {
                clearTimeout(timer);
            };
        }
    }, [isFinished, run.id, onDismiss]);

    const getStatusIcon = () => {
        if (run.status === 'completed') return <CheckCircle2 size={14} className="text-emerald-400" />;
        if (run.status === 'failed' || run.status === 'error') return <XCircle size={14} className="text-rose-400" />;
        return <Loader2 size={14} className="text-violet-400 animate-spin" />;
    };

    const getProgressBarColor = () => {
        if (run.status === 'completed') return 'bg-emerald-500';
        if (run.status === 'failed' || run.status === 'error') return 'bg-rose-500';
        return 'bg-violet-500';
    };

    return (
        <motion.div
            layout
            initial={{ opacity: 0, x: 20, scale: 0.95 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            exit={{ opacity: 0, x: 20, scale: 0.95 }}
            className="flex flex-col gap-2 p-3 rounded-xl border border-white/10 bg-surface-2/80 backdrop-blur-xl shadow-2xl"
        >
            <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-2 min-w-0">
                    <div className="p-1.5 rounded-lg bg-violet-500/10 text-violet-400 shrink-0">
                        <Zap size={14} />
                    </div>
                    <div className="min-w-0">
                        <h4 className="text-[11px] font-bold text-text-primary truncate uppercase tracking-wider">
                            {run.command}
                        </h4>
                        <p className="text-[10px] text-text-tertiary truncate">
                            Run ID: {run.id.split('_').pop()}
                        </p>
                    </div>
                </div>
                <div className="shrink-0">
                    {getStatusIcon()}
                </div>
            </div>

            <div className="space-y-1.5">
                <div className="flex justify-between items-center text-[10px]">
                    <span className="text-text-secondary truncate pr-2">{run.message || 'Procesando...'}</span>
                    <span className="text-text-tertiary font-mono">{Math.round(run.progress * 100)}%</span>
                </div>
                <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
                    <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${run.progress * 100}%` }}
                        className={`h-full transition-all duration-500 ${getProgressBarColor()}`}
                    />
                </div>
            </div>

            <div className="flex items-center gap-2 pt-1">
                <div className="flex items-center gap-1 text-[9px] text-text-tertiary">
                    <Clock size={10} />
                    <span>Started {new Date(run.started_at).toLocaleTimeString()}</span>
                </div>
            </div>
        </motion.div>
    );
};

export const BackgroundRunner: React.FC = () => {
    const skillRuns = useAppStore(s => s.skillRuns);
    const removeSkillRun = useAppStore(s => s.removeSkillRun);

    const activeRuns = Object.values(skillRuns).sort((a, b) =>
        new Date(b.started_at).getTime() - new Date(a.started_at).getTime()
    );

    if (activeRuns.length === 0) return null;

    return (
        <div className="fixed bottom-20 right-6 w-72 z-50 flex flex-col gap-3 pointer-events-none">
            <div className="flex items-center justify-between mb-1 px-1">
                <span className="text-[10px] font-black text-text-tertiary uppercase tracking-[0.2em] flex items-center gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-violet-500 animate-pulse" />
                    Background Skills
                </span>
                <span className="text-[9px] px-1.5 py-0.5 rounded-md bg-white/5 border border-white/5 text-text-tertiary font-bold">
                    {activeRuns.length}
                </span>
            </div>

            <div className="flex flex-col gap-3 pointer-events-auto">
                <AnimatePresence mode="popLayout">
                    {activeRuns.map(run => (
                        <RunItem
                            key={run.id}
                            run={run}
                            onDismiss={removeSkillRun}
                        />
                    ))}
                </AnimatePresence>
            </div>
        </div>
    );
};
