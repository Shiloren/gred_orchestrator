import { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { Cloud } from 'lucide-react';
import { QualityIndicator } from './QualityIndicator';

export const BridgeNode = memo(({ data, selected }: any) => {
    return (
        <div className={`
            px-4 py-3 rounded-xl bg-[#141414] border-2 transition-all duration-200 min-w-[160px]
            ${selected
                ? 'border-[#0a84ff] shadow-[0_0_20px_rgba(10,132,255,0.3)]'
                : 'border-[#2c2c2e] hover:border-[#38383a]'}
        `}>
            <div className="flex items-center gap-3">
                <div className="relative">
                    <div className="w-9 h-9 rounded-lg bg-[#0a84ff]/15 flex items-center justify-center">
                        <Cloud size={18} className="text-[#0a84ff]" />
                    </div>
                    <div className="absolute -top-1 -right-1">
                        <QualityIndicator quality={data.quality} size="sm" />
                    </div>
                </div>
                <div>
                    <div className="text-xs font-semibold text-[#f5f5f7]">{data.label}</div>
                    <div className="text-[10px] text-[#86868b] font-mono">{data.status || 'bridge'}</div>
                </div>
            </div>
            <Handle type="source" position={Position.Right} className="!w-2 !h-2 !bg-[#0a84ff] !border-[#141414] !border-2" />
        </div>
    );
});
