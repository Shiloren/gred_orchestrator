import React, { useState } from 'react';
import { useSubAgents } from '../hooks/useSubAgents';
import { Bot, Cpu, XCircle, Play } from 'lucide-react';

interface Props {
    agentId: string;
}

export const SubAgentCluster: React.FC<Props> = ({ agentId }) => {
    const { subAgents, delegateTask, terminateSubAgent } = useSubAgents(agentId);
    const [taskDesc, setTaskDesc] = useState('');
    const [model, setModel] = useState('llama3');

    const handleDelegate = () => {
        if (!taskDesc) return;
        delegateTask(taskDesc, model);
        setTaskDesc('');
    };

    return (
        <div className="p-4 rounded-xl bg-[#141414] border border-[#1c1c1e] space-y-4">
            <div className="flex items-center justify-between">
                <h3 className="text-[10px] text-[#86868b] font-bold uppercase tracking-widest flex items-center gap-2">
                    <Cpu size={12} /> Sub-Agent Cluster
                </h3>
                <span className="text-[10px] text-[#424245]">{subAgents.length} active</span>
            </div>

            <div className="space-y-2">
                {subAgents.map(ag => (
                    <div key={ag.id} className="flex items-center justify-between p-3 bg-[#000000]/40 rounded-lg border border-[#1c1c1e]">
                        <div className="flex items-center gap-3">
                            <div className={`p-1.5 rounded-md ${ag.status === 'working' ? 'bg-blue-500/10 text-blue-500' : 'bg-[#1c1c1e] text-[#86868b]'}`}>
                                <Bot size={14} className={ag.status === 'working' ? 'animate-pulse' : ''} />
                            </div>
                            <div>
                                <div className="text-xs font-medium text-[#f5f5f7]">{ag.name}</div>
                                <div className="text-[10px] text-[#424245] uppercase flex items-center gap-1.5">
                                    <span>{ag.model}</span>
                                    <span>•</span>
                                    <span className={ag.status === 'working' ? 'text-blue-500' : ''}>{ag.status}</span>
                                </div>
                            </div>
                        </div>
                        {ag.status !== 'terminated' && (
                            <button
                                onClick={() => terminateSubAgent(ag.id)}
                                className="text-[#424245] hover:text-red-500 transition-colors p-1"
                                title="Terminate Sub-Agent"
                            >
                                <XCircle size={14} />
                            </button>
                        )}
                    </div>
                ))}
                {subAgents.length === 0 && (
                    <div className="text-xs text-[#424245] italic text-center py-4 border border-dashed border-[#1c1c1e] rounded-lg">
                        No active sub-agents
                    </div>
                )}
            </div>

            <div className="pt-2 border-t border-[#1c1c1e] space-y-2">
                <div className="flex gap-2">
                    <select
                        value={model}
                        onChange={(e) => setModel(e.target.value)}
                        className="bg-[#000000]/20 border border-[#1c1c1e] rounded px-2 py-1 text-[10px] text-[#86868b] focus:outline-none focus:border-[#424245]"
                    >
                        <option value="llama3">Llama 3</option>
                        <option value="codellama">CodeLlama</option>
                        <option value="mistral">Mistral</option>
                        <option value="gemma">Gemma</option>
                    </select>
                </div>
                <div className="flex gap-2">
                    <input
                        className="flex-1 bg-[#000000]/20 border border-[#1c1c1e] rounded px-3 py-1.5 text-xs text-[#f5f5f7] placeholder-[#424245] focus:outline-none focus:border-[#0a84ff]/50"
                        placeholder="Delegate sub-task..."
                        value={taskDesc}
                        onChange={(e) => setTaskDesc(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleDelegate()}
                    />
                    <button
                        onClick={handleDelegate}
                        disabled={!taskDesc}
                        className="bg-[#1c1c1e] hover:bg-[#2c2c2e] text-[#f5f5f7] px-3 py-1.5 rounded-lg text-xs disabled:opacity-50 transition-all flex items-center gap-2"
                    >
                        <Play size={10} className="fill-current" />
                        <span>Run</span>
                    </button>
                </div>
            </div>
        </div>
    );
};
