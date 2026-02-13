import React from 'react';
import { Network, Wrench, ScrollText, Settings, ClipboardList } from 'lucide-react';

export type SidebarTab = 'graph' | 'plans' | 'maintenance' | 'logs' | 'settings';

interface SidebarProps {
    activeTab: SidebarTab;
    onTabChange: (tab: SidebarTab) => void;
}

const tabs: { id: SidebarTab; icon: typeof Network; label: string }[] = [
    { id: 'graph', icon: Network, label: 'Graph' },
    { id: 'plans', icon: ClipboardList, label: 'Plans' },
    { id: 'maintenance', icon: Wrench, label: 'Maintenance' },
    { id: 'logs', icon: ScrollText, label: 'Logs' },
    { id: 'settings', icon: Settings, label: 'Settings' },
];

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, onTabChange }) => {
    return (
        <aside className="w-14 bg-[#000000] border-r border-[#2c2c2e] flex flex-col items-center py-3 gap-1 shrink-0">
            {tabs.map(({ id, icon: Icon, label }) => (
                <button
                    key={id}
                    onClick={() => onTabChange(id)}
                    title={label}
                    className={`
                        w-10 h-10 rounded-xl flex items-center justify-center
                        transition-all duration-200 group relative
                        ${activeTab === id
                            ? 'bg-[#0a84ff]/15 text-[#0a84ff]'
                            : 'text-[#86868b] hover:text-[#f5f5f7] hover:bg-[#1c1c1e]'}
                    `}
                >
                    <Icon size={18} />
                    <span className="absolute left-full ml-2 px-2 py-1 rounded-md bg-[#2c2c2e] text-[10px] text-white font-medium opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap z-50">
                        {label}
                    </span>
                </button>
            ))}
        </aside>
    );
};
