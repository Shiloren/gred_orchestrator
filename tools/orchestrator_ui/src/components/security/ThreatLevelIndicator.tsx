import React from 'react';

interface ThreatLevelIndicatorProps {
    level: number;
    label: string;
    lockdown: boolean;
}

export const ThreatLevelIndicator: React.FC<ThreatLevelIndicatorProps> = ({ level, label, lockdown }) => {
    let colorClass = 'bg-green-100 text-green-800 border-green-200';
    let icon = '🛡️';

    if (lockdown) {
        colorClass = 'bg-red-900 text-white border-red-700 animate-pulse';
        icon = '🔒';
    } else if (level >= 2) {
        colorClass = 'bg-red-100 text-red-800 border-red-200';
        icon = '⚠️';
    } else if (level === 1) {
        colorClass = 'bg-yellow-100 text-yellow-800 border-yellow-200';
        icon = '👁️';
    }

    return (
        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full border ${colorClass} text-sm font-medium transition-colors duration-300`}>
            <span className="text-base">{icon}</span>
            <span>{label}</span>
            {lockdown && <span className="ml-1 text-xs opacity-80">(LOCKDOWN ACTIVE)</span>}
        </div>
    );
};
