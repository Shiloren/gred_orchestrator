import { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { Cpu } from 'lucide-react';
import { QualityIndicator } from './QualityIndicator';

export const OrchestratorNode = memo(({ data, selected }: any) => {
    return (
        <div className={`
            px-5 py-4 rounded-xl bg-[#141414] border-2 transition-all duration-200 min-w-[180px]
            ${selected
                ? 'border-[#0a84ff] shadow-[0_0_30px_rgba(10,132,255,0.4)]'
                : 'border-[#0a84ff]/40 shadow-[0_0_15px_rgba(10,132,255,0.15)]'}
        `}>
            <div className="flex items-center gap-3">
                <div className="relative">
                    <div className="w-10 h-10 rounded-xl bg-[#0a84ff]/20 flex items-center justify-center ring-1 ring-[#0a84ff]/30">
                        <Cpu size={20} className="text-[#0a84ff]" />
                    </div>
                    <div className="absolute -top-1 -right-1">
                        <QualityIndicator quality={data.quality} size="sm" />
                    </div>
                </div>
                <div>
                    <div className="text-sm font-semibold text-[#f5f5f7]">{data.label}</div>
                    <div className="text-[10px] text-[#32d74b] uppercase tracking-wider font-bold font-mono">{data.status}</div>
                </div>
            </div>
            <Handle type="target" position={Position.Left} className="!w-2 !h-2 !bg-[#0a84ff] !border-[#141414] !border-2" />
            <Handle type="source" position={Position.Right} className="!w-2 !h-2 !bg-[#32d74b] !border-[#141414] !border-2" />
        </div>
    );
});
