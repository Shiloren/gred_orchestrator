import { useState, useEffect, useRef } from 'react';
import { Search, Plus, Play, Workflow } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface CommandItem {
    id: string;
    icon: React.ReactNode;
    label: string;
    shortcut?: string;
    action: () => void;
}

interface CommandPaletteProps {
    isOpen: boolean;
    onClose: () => void;
    onAction: (actionId: string, payload?: any) => void;
}

export const CommandPalette = ({ isOpen, onClose, onAction }: CommandPaletteProps) => {
    const [query, setQuery] = useState('');
    const inputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        if (isOpen) {
            setTimeout(() => inputRef.current?.focus(), 50);
        }
    }, [isOpen]);

    // Mock commands for now
    const commands: CommandItem[] = [
        {
            id: 'new_draft',
            icon: <Plus className="w-4 h-4" />,
            label: 'New Draft Workflow...',
            shortcut: 'N',
            action: () => onAction('open_draft_modal')
        },
        {
            id: 'view_runs',
            icon: <Play className="w-4 h-4" />,
            label: 'View Active Runs',
            shortcut: 'R',
            action: () => onAction('view_runs')
        },
        {
            id: 'view_plan',
            icon: <Workflow className="w-4 h-4" />,
            label: 'Back to Plan',
            shortcut: 'P',
            action: () => onAction('view_plan')
        },
    ];

    const filtered = commands.filter(c =>
        c.label.toLowerCase().includes(query.toLowerCase())
    );

    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 px-4 pt-[20vh] flex justify-center items-start"
                    >
                        {/* Palette */}
                        <motion.div
                            initial={{ scale: 0.95, opacity: 0, y: -20 }}
                            animate={{ scale: 1, opacity: 1, y: 0 }}
                            exit={{ scale: 0.95, opacity: 0, y: -20 }}
                            onClick={(e) => e.stopPropagation()}
                            className="w-full max-w-2xl bg-zinc-900/90 border border-white/10 rounded-2xl shadow-2xl overflow-hidden flex flex-col"
                        >
                            {/* Search Header */}
                            <div className="flex items-center px-4 border-b border-white/5 p-4">
                                <Search className="w-5 h-5 text-zinc-500 mr-3" />
                                <input
                                    ref={inputRef}
                                    value={query}
                                    onChange={(e) => setQuery(e.target.value)}
                                    placeholder="Type a command or search..."
                                    className="flex-1 bg-transparent text-lg text-white placeholder-zinc-600 outline-none"
                                />
                                <div className="flex items-center space-x-2">
                                    <kbd className="hidden sm:inline-flex h-6 items-center gap-1 rounded border border-white/10 bg-white/5 px-2 font-mono text-[10px] font-medium text-zinc-400">
                                        ESC
                                    </kbd>
                                </div>
                            </div>

                            {/* Results */}
                            <div className="max-h-[300px] overflow-y-auto p-2 custom-scrollbar">
                                {filtered.length === 0 ? (
                                    <div className="p-8 text-center text-zinc-500 text-sm">
                                        No commands found.
                                    </div>
                                ) : (
                                    <div className="space-y-1">
                                        {filtered.map((cmd) => (
                                            <button
                                                key={cmd.id}
                                                onClick={() => {
                                                    cmd.action();
                                                    onClose();
                                                }}
                                                className="w-full flex items-center justify-between px-3 py-3 rounded-xl hover:bg-blue-500/10 hover:text-blue-400 text-zinc-400 text-sm transition-colors group text-left"
                                            >
                                                <div className="flex items-center space-x-3">
                                                    <div className="p-2 rounded-lg bg-white/5 group-hover:bg-blue-500/20 transition-colors">
                                                        {cmd.icon}
                                                    </div>
                                                    <span className="font-medium group-hover:text-white transition-colors">
                                                        {cmd.label}
                                                    </span>
                                                </div>
                                                {cmd.shortcut && (
                                                    <span className="text-[10px] font-mono opacity-50 bg-white/5 px-2 py-0.5 rounded">
                                                        {cmd.shortcut}
                                                    </span>
                                                )}
                                            </button>
                                        ))}
                                    </div>
                                )}
                            </div>

                            {/* Footer hint */}
                            <div className="bg-black/20 p-2 px-4 text-[10px] text-zinc-600 border-t border-white/5 flex justify-between">
                                <span>Pro Tip: Use Natural Language to generate drafts</span>
                                <span>GIMO Orchestrator v2.0</span>
                            </div>
                        </motion.div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
};
