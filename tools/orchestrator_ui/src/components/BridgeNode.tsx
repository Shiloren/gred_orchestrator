import { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { Cloud } from 'lucide-react';
import { QualityIndicator } from './QualityIndicator';

export const BridgeNode = memo(({ data, selected }: any) => {
    return (
        <div className={`
            px-3 py-2 rounded-xl bg-surface-1 border-2 transition-all duration-200 min-w-[140px] max-w-[200px]
            ${selected
                ? 'border-accent-primary shadow-[0_0_20px_rgba(10,132,255,0.3)]'
                : 'border-border-primary hover:border-surface-3'}
        `}>
            <div className="flex items-center gap-2">
                <div className="relative">
                    <div className="w-7 h-7 rounded-lg bg-accent-primary/15 flex items-center justify-center">
                        <Cloud size={14} className="text-accent-primary" />
                    </div>
                    <div className="absolute -top-1 -right-1">
                        <QualityIndicator quality={data.quality} size="sm" />
                    </div>
                </div>
                <div>
                    <div className="text-xs font-semibold text-text-primary">{data.label}</div>
                    <div className="text-[10px] text-text-secondary font-mono">{data.status || 'bridge'}</div>
                </div>
            </div>
            <Handle type="source" position={Position.Right} className="!w-2 !h-2 !bg-accent-primary !border-surface-1 !border-2" />
        </div>
    );
});
