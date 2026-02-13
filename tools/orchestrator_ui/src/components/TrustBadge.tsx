import React from 'react';
import { ShieldAlert, ShieldCheck, ShieldQuestion } from 'lucide-react';
import { TrustLevel } from '../types';

interface TrustBadgeProps {
    level: TrustLevel;
    size?: number;
    showLabel?: boolean;
}

export const TrustBadge: React.FC<TrustBadgeProps> = ({ level, size = 12, showLabel = false }) => {
    const config = {
        autonomous: {
            icon: ShieldCheck,
            color: 'text-[#32d74b]',
            bg: 'bg-[#32d74b]/10',
            border: 'border-[#32d74b]/20',
            label: 'Autonomous'
        },
        supervised: {
            icon: ShieldQuestion,
            color: 'text-[#ff9f0a]',
            bg: 'bg-[#ff9f0a]/10',
            border: 'border-[#ff9f0a]/20',
            label: 'Supervised'
        },
        restricted: {
            icon: ShieldAlert,
            color: 'text-[#ff453a]',
            bg: 'bg-[#ff453a]/10',
            border: 'border-[#ff453a]/20',
            label: 'Restricted'
        }
    };

    const { icon: Icon, color, bg, border, label } = config[level] || config.supervised;

    return (
        <div className={`
            inline-flex items-center gap-1.5 px-2 py-1 rounded-full border 
            ${bg} ${border} ${color} transition-all duration-300
        `}>
            <Icon size={size} />
            {showLabel && (
                <span className="text-[9px] font-bold uppercase tracking-wider">
                    {label}
                </span>
            )}
        </div>
    );
};
