import { useState, useEffect, useRef } from 'react';
import { Search, Plus, Play, Workflow, Activity, ShieldAlert, Wrench, Settings, Wallet, Network } from 'lucide-react';

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

    const commands: CommandItem[] = [
        {
            id: 'new_plan',
            icon: <Plus className="w-4 h-4" />,
            label: 'Nuevo plan',
            shortcut: 'N',
            action: () => onAction('new_plan')
        },
        {
            id: 'goto_graph',
            icon: <Network className="w-4 h-4" />,
            label: 'Ir a Graph',
            action: () => onAction('goto_graph')
        },
        {
            id: 'goto_plans',
            icon: <Workflow className="w-4 h-4" />,
            label: 'Ir a Plans',
            action: () => onAction('goto_plans')
        },
        {
            id: 'goto_evals',
            icon: <Play className="w-4 h-4" />,
            label: 'Ir a Evaluations',
            action: () => onAction('goto_evals')
        },
        {
            id: 'goto_metrics',
            icon: <Activity className="w-4 h-4" />,
            label: 'Ir a Metrics',
            action: () => onAction('goto_metrics')
        },
        {
            id: 'goto_security',
            icon: <ShieldAlert className="w-4 h-4" />,
            label: 'Ir a Security',
            action: () => onAction('goto_security')
        },
        {
            id: 'goto_maintenance',
            icon: <Wrench className="w-4 h-4" />,
            label: 'Ir a Maintenance',
            action: () => onAction('goto_maintenance')
        },
        {
            id: 'goto_settings',
            icon: <Settings className="w-4 h-4" />,
            label: 'Ir a Settings',
            action: () => onAction('goto_settings')
        },
        {
            id: 'goto_mastery',
            icon: <Wallet className="w-4 h-4" />,
            label: 'Ir a Token Mastery',
            action: () => onAction('goto_mastery')
        },
        {
            id: 'search_repo',
            icon: <Search className="w-4 h-4" />,
            label: 'Buscar repositorio',
            action: () => onAction('search_repo', { query })
        },
        {
            id: 'mcp_sync',
            icon: <Workflow className="w-4 h-4" />,
            label: 'Sincronizar MCP tools',
            action: () => onAction('mcp_sync')
        },
        {
            id: 'view_runs',
            icon: <Play className="w-4 h-4" />,
            label: 'Ver ejecuciones activas',
            shortcut: 'R',
            action: () => onAction('view_runs')
        },
        {
            id: 'view_plan',
            icon: <Workflow className="w-4 h-4" />,
            label: 'Volver al plan',
            shortcut: 'P',
            action: () => onAction('view_plan')
        },
    ];

    const filtered = commands.filter(c =>
        c.label.toLowerCase().includes(query.toLowerCase())
    );

    if (!isOpen) return null;

    return (
        <div
            onClick={onClose}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 px-4 pt-[20vh] flex justify-center items-start"
        >
            <div
                onClick={(e: React.MouseEvent<HTMLDivElement>) => e.stopPropagation()}
                className="w-full max-w-2xl bg-zinc-900/90 border border-white/10 rounded-2xl shadow-2xl overflow-hidden flex flex-col"
            >
                {/* Search Header */}
                <div className="flex items-center px-4 border-b border-white/5 p-4">
                    <Search className="w-5 h-5 text-zinc-500 mr-3" />
                    <input
                        ref={inputRef}
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Escribe un comando o busca una vista..."
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
                            No se encontraron comandos.
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
                    <span>Tip: Usa Ctrl+K / Cmd+K para abrir rápidamente</span>
                    <span>GIMO Orchestrator v2.0</span>
                </div>
            </div>
        </div>
    );
};
