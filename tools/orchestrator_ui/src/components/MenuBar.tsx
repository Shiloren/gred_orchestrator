import React, { useEffect, useMemo, useRef, useState } from 'react';
import { ChevronDown } from 'lucide-react';
import type { SidebarTab } from './Sidebar';

type MenuId = 'file' | 'edit' | 'view' | 'tools' | 'help';

interface MenuBarProps {
    onNewPlan: () => void;
    onSelectView: (tab: SidebarTab) => void;
    onSelectSettingsView: (tab: SidebarTab) => void;
    onRefreshSession: () => void;
    onOpenCommandPalette: () => void;
    onMcpSync: () => void;
}

interface MenuAction {
    label: string;
    onClick: () => void;
}

export const MenuBar: React.FC<MenuBarProps> = ({
    onNewPlan,
    onSelectView,
    onSelectSettingsView,
    onRefreshSession,
    onOpenCommandPalette,
    onMcpSync,
}) => {
    const [openMenu, setOpenMenu] = useState<MenuId | null>(null);
    const rootRef = useRef<HTMLDivElement | null>(null);

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (rootRef.current && !rootRef.current.contains(event.target as Node)) {
                setOpenMenu(null);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const menus = useMemo<Record<MenuId, MenuAction[]>>(() => ({
        file: [
            { label: 'Nuevo Plan', onClick: onNewPlan },
            { label: 'Abrir Repo', onClick: () => onSelectView('maintenance') },
            { label: 'Exportar Logs', onClick: () => onSelectView('logs') },
            { label: 'Revalidar sesión', onClick: onRefreshSession },
        ],
        edit: [
            { label: 'Config Economía', onClick: () => onSelectSettingsView('mastery') },
            { label: 'Config Providers', onClick: () => onSelectSettingsView('settings') },
            { label: 'Políticas / Seguridad', onClick: () => onSelectSettingsView('security') },
        ],
        view: [
            { label: 'Graph', onClick: () => onSelectView('graph') },
            { label: 'Plans', onClick: () => onSelectView('plans') },
            { label: 'Evaluations', onClick: () => onSelectView('evals') },
            { label: 'Metrics', onClick: () => onSelectView('metrics') },
            { label: 'Security', onClick: () => onSelectView('security') },
            { label: 'Maintenance', onClick: () => onSelectView('maintenance') },
        ],
        tools: [
            { label: 'Command Palette (Ctrl+K)', onClick: onOpenCommandPalette },
            { label: 'MCP Sync', onClick: onMcpSync },
            { label: 'Run Evaluation', onClick: () => onSelectView('evals') },
        ],
        help: [
            { label: 'Documentación', onClick: () => window.open('/docs', '_blank') },
            { label: 'Acerca de', onClick: () => onSelectView('graph') },
        ],
    }), [onMcpSync, onNewPlan, onOpenCommandPalette, onRefreshSession, onSelectSettingsView, onSelectView]);

    const labels: Record<MenuId, string> = {
        file: 'File',
        edit: 'Edit',
        view: 'View',
        tools: 'Tools',
        help: 'Help',
    };

    return (
        <header className="h-10 border-b border-[#2c2c2e] bg-[#000000]/90 backdrop-blur-xl px-3 flex items-center justify-between shrink-0 z-50">
            <div ref={rootRef} className="flex items-center gap-1">
                {(Object.keys(labels) as MenuId[]).map((id) => (
                    <div key={id} className="relative">
                        <button
                            onClick={() => setOpenMenu(prev => prev === id ? null : id)}
                            className={`h-7 px-2.5 rounded-md text-xs font-medium inline-flex items-center gap-1 transition-colors ${openMenu === id
                                ? 'bg-[#1c1c1e] text-[#f5f5f7]'
                                : 'text-[#86868b] hover:text-[#f5f5f7] hover:bg-[#1c1c1e]'
                                }`}
                        >
                            {labels[id]}
                            <ChevronDown size={12} className={`transition-transform ${openMenu === id ? 'rotate-180' : ''}`} />
                        </button>

                        {openMenu === id && (
                            <div className="absolute top-full left-0 mt-1 w-56 rounded-xl border border-[#2c2c2e] bg-[#101011] shadow-2xl overflow-hidden">
                                {menus[id].map((entry) => (
                                    <button
                                        key={entry.label}
                                        onClick={() => {
                                            entry.onClick();
                                            setOpenMenu(null);
                                        }}
                                        className="w-full text-left px-3 py-2 text-xs text-[#f5f5f7] hover:bg-[#1c1c1e]"
                                    >
                                        {entry.label}
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>
                ))}
            </div>

            <div className="text-[10px] text-[#86868b] font-mono uppercase tracking-wider">GIMO PHOENIX</div>
        </header>
    );
};
