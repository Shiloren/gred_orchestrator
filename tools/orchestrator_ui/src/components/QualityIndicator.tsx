import React from 'react';
import { QualityMetrics } from '../types';

interface QualityIndicatorProps {
    quality?: QualityMetrics;
    size?: 'sm' | 'md' | 'lg';
}

export const QualityIndicator: React.FC<QualityIndicatorProps> = ({ quality, size = 'md' }) => {
    if (!quality) return null;

    const { score } = quality;

    // Determine color based on score
    let colorClass = 'bg-[#32d74b]'; // Green
    let pulseClass = '';

    if (score < 50) {
        colorClass = 'bg-[#ff453a]'; // Red
        pulseClass = 'animate-ping opacity-75';
    } else if (score < 80) {
        colorClass = 'bg-[#ffd60a]'; // Amber
        pulseClass = 'animate-pulse';
    }

    const sizeMap = {
        sm: 'w-2 h-2',
        md: 'w-3 h-3',
        lg: 'w-4 h-4',
    };

    return (
        <div className="relative flex items-center justify-center">
            {pulseClass && (
                <div className={`absolute inline-flex rounded-full ${sizeMap[size]} ${colorClass} ${pulseClass}`}></div>
            )}
            <div
                className={`relative inline-flex rounded-full ${sizeMap[size]} ${colorClass} border border-black/20`}
                title={`Quality Score: ${score}%`}
            ></div>
        </div>
    );
};
