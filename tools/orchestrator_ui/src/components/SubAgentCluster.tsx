import React, { useState } from 'react';
import { useSubAgents } from '../hooks/useSubAgents';
import { Bot, Cpu, XCircle, Play, Layers } from 'lucide-react';

interface BatchTask {
    description: string;
    model: string;
}

interface Props {
    agentId: string;
}

export const SubAgentCluster: React.FC<Props> = ({ agentId }) => {
    const { subAgents, delegateTask, delegateBatch, terminateSubAgent } = useSubAgents(agentId);
    const [taskDesc, setTaskDesc] = useState('');
    const [model, setModel] = useState('llama3');
    const [batchMode, setBatchMode] = useState(false);
    const [batchTasks, setBatchTasks] = useState<BatchTask[]>([]);
    const [batchInput, setBatchInput] = useState('');

    const handleDelegate = () => {
        if (!taskDesc) return;
        delegateTask(taskDesc, model);
        setTaskDesc('');
    };

    const addBatchTask = () => {
        if (!batchInput) return;
        setBatchTasks(prev => [...prev, { description: batchInput, model }]);
        setBatchInput('');
    };

    const removeBatchTask = (index: number) => {
        setBatchTasks(prev => prev.filter((_, i) => i !== index));
    };

    const executeBatch = () => {
        if (batchTasks.length === 0) return;
        delegateBatch(batchTasks);
        setBatchTasks([]);
        setBatchMode(false);
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
                                {ag.result && (
                                    <div className="mt-2 p-2 rounded bg-[#000000]/60 border border-[#1c1c1e] text-[10px] font-mono text-[#a1a1a6] whitespace-pre-wrap max-h-32 overflow-y-auto custom-scrollbar">
                                        {ag.result}
                                    </div>
                                )}
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

            <div className="flex gap-2 items-center">
                <div className="relative flex-1">
                    <select
                        value={model}
                        onChange={(e) => setModel(e.target.value)}
                        className="w-full bg-[#000000]/20 border border-[#1c1c1e] rounded px-2 py-1 text-[10px] text-[#86868b] focus:outline-none focus:border-[#424245] appearance-none"
                    >
                        <optgroup label="Local (Free)">
                            <option value="llama3">Llama 3 (Local)</option>
                            <option value="mistral">Mistral (Local)</option>
                        </optgroup>
                        <optgroup label="Cloud (Token Mastery)">
                            <option value="sonnet">Claude 3.5 Sonnet</option>
                            <option value="haiku">Claude 3.5 Haiku (Eco)</option>
                            <option value="gpt4o">GPT-4o</option>
                            <option value="mini">GPT-4o Mini (Eco)</option>
                        </optgroup>
                    </select>
                    {model.includes('haiku') || model.includes('mini') ? (
                        <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                            <span className="text-[8px] text-emerald-500 font-bold bg-emerald-500/10 px-1 rounded">ECO</span>
                        </div>
                    ) : null}
                </div>

                <button
                    onClick={() => setBatchMode(!batchMode)}
                    className={`flex items-center gap-1.5 px-2 py-1 rounded text-[10px] font-semibold transition-colors ${batchMode
                        ? 'bg-[#5e5ce6]/10 text-[#5e5ce6] border border-[#5e5ce6]/20'
                        : 'text-[#424245] hover:text-[#86868b]'
                        }`}
                >
                    <Layers size={10} />
                    Batch
                </button>
            </div>

            {/* Impact Indicator */}
            {!batchMode && model !== 'llama3' && (
                <div className="px-2 py-1 bg-[#1c1c1e]/40 rounded text-[9px] flex items-center justify-between border border-[#1c1c1e]">
                    <span className="text-[#86868b]">Impacto vs Sonnet:</span>
                    <span className={model === 'haiku' ? 'text-emerald-500 font-bold' : 'text-[#86868b]'}>
                        {model === 'haiku' ? '73.3% Ahorro' : model === 'sonnet' ? 'Baseline' : 'Variable'}
                    </span>
                </div>
            )}

            {batchMode ? (
                <div className="space-y-2">
                    {batchTasks.map((task, idx) => (
                        <div key={idx} className="flex items-center gap-2 p-2 bg-[#000000]/30 rounded border border-[#1c1c1e]">
                            <span className="text-[10px] font-mono text-[#5e5ce6] shrink-0">{idx + 1}.</span>
                            <span className="text-xs text-[#f5f5f7] flex-1 truncate">{task.description}</span>
                            <span className="text-[9px] text-[#424245] uppercase">{task.model}</span>
                            <button onClick={() => removeBatchTask(idx)} className="text-[#424245] hover:text-red-500">
                                <XCircle size={12} />
                            </button>
                        </div>
                    ))}
                    <div className="flex gap-2">
                        <input
                            className="flex-1 bg-[#000000]/20 border border-[#1c1c1e] rounded px-3 py-1.5 text-xs text-[#f5f5f7] placeholder-[#424245] focus:outline-none focus:border-[#5e5ce6]/50"
                            placeholder="Add task to batch..."
                            value={batchInput}
                            onChange={(e) => setBatchInput(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && addBatchTask()}
                        />
                        <button
                            onClick={addBatchTask}
                            disabled={!batchInput}
                            className="bg-[#1c1c1e] hover:bg-[#2c2c2e] text-[#f5f5f7] px-3 py-1.5 rounded-lg text-xs disabled:opacity-50 transition-all"
                        >
                            Add
                        </button>
                    </div>
                    <button
                        onClick={executeBatch}
                        disabled={batchTasks.length === 0}
                        className="w-full bg-[#5e5ce6]/10 hover:bg-[#5e5ce6]/20 border border-[#5e5ce6]/20 text-[#5e5ce6] px-3 py-2 rounded-lg text-xs font-semibold disabled:opacity-50 transition-all flex items-center justify-center gap-2"
                    >
                        <Layers size={12} />
                        Launch {batchTasks.length} Tasks in Parallel
                    </button>
                </div>
            ) : (
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
            )}
        </div>
    );
};
