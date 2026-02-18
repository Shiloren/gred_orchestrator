import React, { useMemo } from 'react';
import { X, Activity } from 'lucide-react';
import { AgentPlanPanel } from './AgentPlanPanel';
import { TrustBadge } from './TrustBadge';
import { AgentQuestionCard } from './AgentQuestionCard';
import { QualityAlertPanel } from './QualityAlertPanel';
import AgentChat from './AgentChat';
import { SubAgentCluster } from './SubAgentCluster';
import { useNodes } from 'reactflow';
import { GraphNode, TrustLevel } from '../types';

interface InspectPanelProps {
    selectedNodeId: string | null;
    onClose: () => void;
}

export const InspectPanel: React.FC<InspectPanelProps> = ({
    selectedNodeId,
    onClose,
}) => {
    const nodes = useNodes<GraphNode['data']>();
    const selectedNode = useMemo(() =>
        nodes.find(n => n.id === selectedNodeId),
        [nodes, selectedNodeId]);

    const planData = selectedNode?.data?.plan;
    const qualityData = selectedNode?.data?.quality;

    const [view, setView] = React.useState<'overview' | 'plan' | 'logs' | 'quality' | 'chat' | 'delegation'>('overview');

    return (
        <aside className="w-[380px] bg-[#0a0a0a] border-l border-[#2c2c2e] flex flex-col shrink-0 overflow-hidden shadow-2xl z-40">
            <div className="h-12 px-4 flex items-center justify-between border-b border-[#1c1c1e] shrink-0 bg-[#000000]/50">
                <div className="flex items-center gap-2 min-w-0">
                    <span className="text-xs font-semibold text-[#f5f5f7] truncate uppercase tracking-wider">
                        {`Node: ${selectedNode?.data?.label || selectedNodeId}`}
                    </span>
                    {selectedNode?.data?.trustLevel && (
                        <TrustBadge level={selectedNode.data.trustLevel} />
                    )}
                </div>
                <button
                    onClick={onClose}
                    className="w-7 h-7 rounded-lg flex items-center justify-center text-[#86868b] hover:text-[#f5f5f7] hover:bg-[#1c1c1e] transition-all"
                >
                    <X size={14} />
                </button>
            </div>

            <div className="flex px-4 pt-4 gap-4 border-b border-[#1c1c1e] bg-[#000000]/20">
                <button
                    onClick={() => setView('plan')}
                    className={`pb-2 text-[10px] font-bold uppercase tracking-widest transition-all relative ${view === 'plan' ? 'text-[#0a84ff]' : 'text-[#424245] hover:text-[#86868b]'}`}
                >
                    Active Plan
                    {view === 'plan' && <div className="absolute bottom-0 left-0 w-full h-0.5 bg-[#0a84ff]" />}
                </button>
                {(selectedNode?.type === 'orchestrator' || selectedNode?.type === 'bridge') && (
                    <>
                        <button
                            onClick={() => setView('chat')}
                            className={`pb-2 text-[10px] font-bold uppercase tracking-widest transition-all relative ${view === 'chat' ? 'text-[#0a84ff]' : 'text-[#424245] hover:text-[#86868b]'}`}
                        >
                            Chat
                            {view === 'chat' && <div className="absolute bottom-0 left-0 w-full h-0.5 bg-[#0a84ff]" />}
                        </button>
                        <button
                            onClick={() => setView('quality')}
                            className={`pb-2 text-[10px] font-bold uppercase tracking-widest transition-all relative ${view === 'quality' ? 'text-[#0a84ff]' : 'text-[#424245] hover:text-[#86868b]'}`}
                        >
                            Quality
                            {view === 'quality' && <div className="absolute bottom-0 left-0 w-full h-0.5 bg-[#0a84ff]" />}
                        </button>
                        <button
                            onClick={() => setView('delegation')}
                            className={`pb-2 text-[10px] font-bold uppercase tracking-widest transition-all relative ${view === 'delegation' ? 'text-[#0a84ff]' : 'text-[#424245] hover:text-[#86868b]'}`}
                        >
                            Sub-Agents
                            {view === 'delegation' && <div className="absolute bottom-0 left-0 w-full h-0.5 bg-[#0a84ff]" />}
                        </button>
                    </>
                )}
                <button
                    onClick={() => setView('overview')}
                    className={`pb-2 text-[10px] font-bold uppercase tracking-widest transition-all relative ${view === 'overview' ? 'text-[#0a84ff]' : 'text-[#424245] hover:text-[#86868b]'}`}
                >
                    Node Info
                    {view === 'overview' && <div className="absolute bottom-0 left-0 w-full h-0.5 bg-[#0a84ff]" />}
                </button>
            </div>

            <div className="flex-1 overflow-y-auto custom-scrollbar p-5 space-y-6">
                {selectedNodeId ? (
                    <>
                        {selectedNode?.data?.pendingQuestions && selectedNode.data.pendingQuestions.length > 0 && (
                            <div className="space-y-3 mb-6">
                                {selectedNode.data.pendingQuestions.map(q => (
                                    <AgentQuestionCard
                                        key={q.id}
                                        question={q}
                                        onAnswer={(id: string, ans: string) => console.log('Answered', id, ans)}
                                        onDismiss={(id: string) => console.log('Dismissed', id)}
                                    />
                                ))}
                            </div>
                        )}

                        {view === 'plan' && <AgentPlanPanel plan={planData} />}
                        {view === 'quality' && <QualityAlertPanel quality={qualityData} />}
                        {view === 'delegation' && <SubAgentCluster agentId={selectedNodeId} />}
                        {view === 'chat' && <div className="h-[400px]"><AgentChat agentId={selectedNodeId} /></div>}
                        {view === 'overview' && (
                            <div className="space-y-4">
                                <div className="p-4 rounded-xl bg-[#141414] border border-[#1c1c1e]">
                                    <div className="text-[10px] text-[#86868b] font-bold uppercase tracking-widest mb-2">Properties</div>
                                    <div className="space-y-2">
                                        <div className="flex justify-between items-center text-xs">
                                            <span className="text-[#86868b]">Type</span>
                                            <span className="text-[#f5f5f7] font-mono">{selectedNode?.type}</span>
                                        </div>
                                        <div className="flex justify-between items-center text-xs">
                                            <span className="text-[#86868b]">Status</span>
                                            <span className="text-[#32d74b] font-mono">{selectedNode?.data?.status || 'active'}</span>
                                        </div>
                                        {selectedNode?.data?.path && (
                                            <div className="pt-2 border-t border-[#1c1c1e] mt-2">
                                                <div className="text-[10px] text-[#86868b] font-bold uppercase tracking-widest mb-1">Source Path</div>
                                                <div className="text-[10px] text-[#0a84ff] font-mono truncate">{selectedNode?.data?.path}</div>
                                            </div>
                                        )}
                                    </div>
                                </div>

                                {(selectedNode?.type === 'orchestrator' || selectedNode?.type === 'bridge') && (
                                    <div className="p-4 rounded-xl bg-[#141414] border border-[#1c1c1e] space-y-3">
                                        <div className="text-[10px] text-[#86868b] font-bold uppercase tracking-widest">Delegation Trust</div>
                                        <div className="grid grid-cols-3 gap-2">
                                            {(['autonomous', 'supervised', 'restricted'] as TrustLevel[]).map(level => (
                                                <button
                                                    key={level}
                                                    onClick={() => console.log('Update trust', level)}
                                                    className={`
                                                        flex flex-col items-center gap-1.5 p-2 rounded-lg border transition-all
                                                        ${selectedNode.data.trustLevel === level
                                                            ? 'bg-[#0a84ff]/10 border-[#0a84ff]/30 text-[#0a84ff]'
                                                            : 'bg-[#000000]/20 border-transparent text-[#424245] hover:text-[#86868b]'}
                                                    `}
                                                >
                                                    <TrustBadge level={level} size={10} />
                                                    <span className="text-[8px] font-bold truncate capitalize">{level}</span>
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                    </>
                ) : (
                    <div className="flex flex-col items-center justify-center py-20 text-[#86868b] text-center px-6">
                        <Activity size={32} className="mb-4 opacity-10" />
                        <p className="text-sm font-medium">No node selected</p>
                        <p className="text-[10px] mt-1">Select an agent or component to inspect its live state</p>
                    </div>
                )}
            </div>
        </aside>
    );
};
