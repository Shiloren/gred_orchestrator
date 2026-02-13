import { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { Bot, Cpu, Layers } from 'lucide-react';
import { SubAgent, TrustLevel } from '../types';
import { TrustBadge } from './TrustBadge';
import { QualityIndicator } from './QualityIndicator';

export const ClusterNode = memo(({ data, selected }: any) => {
    // data.subAgents is assumed to be passed in
    const subAgents: SubAgent[] = data.subAgents || [];
    const activeCount = subAgents.filter(a => a.status === 'working').length;

    return (
        <div className={`
            p-1 rounded-2xl bg-[#141414]/90 backdrop-blur-xl border-2 transition-all duration-300
            ${selected
                ? 'border-[#0a84ff] shadow-[0_0_40px_rgba(10,132,255,0.3)] scale-105'
                : 'border-[#2c2c2e] hover:border-[#424245] shadow-xl'}
        `}>
            {/* Header / Parent Agent Representation */}
            <div className="bg-[#1c1c1e] px-4 py-3 rounded-xl flex items-center gap-3 min-w-[220px] relative overflow-hidden">
                <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#0a84ff]/20 to-[#0a84ff]/5 border border-[#0a84ff]/20 flex items-center justify-center relative">
                    <Cpu size={20} className="text-[#0a84ff]" />
                    {data.quality && (
                        <div className="absolute -top-1 -right-1">
                            <QualityIndicator quality={data.quality} size="sm" />
                        </div>
                    )}
                </div>
                <div className="flex-1">
                    <div className="text-sm font-bold text-[#f5f5f7] flex items-center justify-between">
                        {data.label}
                        <div className="flex items-center gap-2">
                            {data.trustLevel && <TrustBadge level={data.trustLevel as TrustLevel} size={8} />}
                            {activeCount > 0 && (
                                <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-blue-500/10 border border-blue-500/20">
                                    <span className="relative flex h-2 w-2">
                                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                                        <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
                                    </span>
                                    <span className="text-[9px] font-bold text-blue-400">{activeCount}</span>
                                </div>
                            )}
                        </div>
                    </div>
                    <div className="text-[10px] text-[#86868b] font-mono mt-0.5 uppercase tracking-wide flex items-center gap-2">
                        <Layers size={10} />
                        Fractal Cluster
                    </div>
                </div>
            </div>

            {/* Sub-Agent List Visualization */}
            {subAgents.length > 0 && (
                <div className="mt-2 space-y-1 px-1 pb-1">
                    <div className="text-[9px] font-bold text-[#424245] uppercase tracking-widest pl-2 mb-1">Sub-Delegates</div>
                    {subAgents.map((agent: SubAgent) => (
                        <div
                            key={agent.id}
                            className={`
                                flex items-center gap-2 px-3 py-2 rounded-lg border text-xs transition-all
                                ${agent.status === 'working'
                                    ? 'bg-blue-500/10 border-blue-500/20 text-[#f5f5f7]'
                                    : 'bg-[#000000]/40 border-transparent text-[#86868b]'}
                            `}
                        >
                            <Bot size={12} className={agent.status === 'working' ? 'animate-pulse text-blue-400' : 'text-[#424245]'} />
                            <span className="flex-1 truncate">{agent.name}</span>
                            <span className={`text-[9px] uppercase font-mono ${agent.status === 'working' ? 'text-blue-400' : 'text-[#424245]'}`}>
                                {agent.model}
                            </span>
                        </div>
                    ))}
                </div>
            )}

            <Handle type="target" position={Position.Left} className="!w-2 !h-2 !bg-[#0a84ff] !border-[#141414] !border-2" />
            <Handle type="source" position={Position.Right} className="!w-2 !h-2 !bg-[#32d74b] !border-[#141414] !border-2" />
        </div>
    );
});
