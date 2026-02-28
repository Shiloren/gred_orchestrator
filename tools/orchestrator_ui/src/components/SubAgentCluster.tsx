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
        <div className="p-4 rounded-xl bg-surface-1 border border-surface-2 space-y-4">
            <div className="flex items-center justify-between">
                <h3 className="text-[10px] text-text-secondary font-bold uppercase tracking-widest flex items-center gap-2">
                    <Cpu size={12} /> Sub-Agent Cluster
                </h3>
                <span className="text-[10px] text-text-tertiary">{subAgents.length} active</span>
            </div>

            <div className="space-y-2">
                {subAgents.map(ag => (
                    <div key={ag.id} className="flex items-center justify-between p-3 bg-surface-0/40 rounded-lg border border-surface-2">
                        <div className="flex items-center gap-3">
                            <div className={`p-1.5 rounded-md ${ag.status === 'working' ? 'bg-blue-500/10 text-blue-500' : 'bg-surface-2 text-text-secondary'}`}>
                                <Bot size={14} className={ag.status === 'working' ? 'animate-pulse' : ''} />
                            </div>
                            <div>
                                <div className="text-xs font-medium text-text-primary">{ag.name}</div>
                                <div className="text-[10px] text-text-tertiary uppercase flex items-center gap-1.5">
                                    <span>{ag.model}</span>
                                    <span>•</span>
                                    <span className={ag.status === 'working' ? 'text-blue-500' : ''}>{ag.status}</span>
                                </div>
                                {ag.result && (
                                    <div className="mt-2 p-2 rounded bg-surface-0/60 border border-surface-2 text-[10px] font-mono text-text-secondary whitespace-pre-wrap max-h-32 overflow-y-auto custom-scrollbar">
                                        {ag.result}
                                    </div>
                                )}
                            </div>
                        </div>
                        {ag.status !== 'terminated' && (
                            <button
                                onClick={() => terminateSubAgent(ag.id)}
                                className="text-text-tertiary hover:text-red-500 transition-colors p-1"
                                title="Terminate Sub-Agent"
                            >
                                <XCircle size={14} />
                            </button>
                        )}
                    </div>
                ))}
                {subAgents.length === 0 && (
                    <div className="text-xs text-text-tertiary italic text-center py-4 border border-dashed border-surface-2 rounded-lg">
                        No active sub-agents
                    </div>
                )}
            </div>

            <div className="flex gap-2 items-center">
                <div className="relative flex-1">
                    <select
                        value={model}
                        onChange={(e) => setModel(e.target.value)}
                        className="w-full bg-surface-0/20 border border-surface-2 rounded px-2 py-1 text-[10px] text-text-secondary focus:outline-none focus:border-text-tertiary appearance-none"
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
                        ? 'bg-accent-purple/10 text-accent-purple border border-accent-purple/20'
                        : 'text-text-tertiary hover:text-text-secondary'
                        }`}
                >
                    <Layers size={10} />
                    Batch
                </button>
            </div>

            {/* Impact Indicator */}
            {!batchMode && model !== 'llama3' && (
                <div className="px-2 py-1 bg-surface-2/40 rounded text-[9px] flex items-center justify-between border border-surface-2">
                    <span className="text-text-secondary">Impacto vs Sonnet:</span>
                    <span className={model === 'haiku' ? 'text-emerald-500 font-bold' : 'text-text-secondary'}>
                        {model === 'haiku' ? '73.3% Ahorro' : model === 'sonnet' ? 'Baseline' : 'Variable'}
                    </span>
                </div>
            )}

            {batchMode ? (
                <div className="space-y-2">
                    {batchTasks.map((task, idx) => (
                        <div key={idx} className="flex items-center gap-2 p-2 bg-surface-0/30 rounded border border-surface-2">
                            <span className="text-[10px] font-mono text-accent-purple shrink-0">{idx + 1}.</span>
                            <span className="text-xs text-text-primary flex-1 truncate">{task.description}</span>
                            <span className="text-[9px] text-text-tertiary uppercase">{task.model}</span>
                            <button onClick={() => removeBatchTask(idx)} className="text-text-tertiary hover:text-red-500">
                                <XCircle size={12} />
                            </button>
                        </div>
                    ))}
                    <div className="flex gap-2">
                        <input
                            className="flex-1 bg-surface-0/20 border border-surface-2 rounded px-3 py-1.5 text-xs text-text-primary placeholder-text-tertiary focus:outline-none focus:border-accent-purple/50"
                            placeholder="Add task to batch..."
                            value={batchInput}
                            onChange={(e) => setBatchInput(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && addBatchTask()}
                        />
                        <button
                            onClick={addBatchTask}
                            disabled={!batchInput}
                            className="bg-surface-2 hover:bg-surface-3 text-text-primary px-3 py-1.5 rounded-lg text-xs disabled:opacity-50 transition-all"
                        >
                            Add
                        </button>
                    </div>
                    <button
                        onClick={executeBatch}
                        disabled={batchTasks.length === 0}
                        className="w-full bg-accent-purple/10 hover:bg-accent-purple/20 border border-accent-purple/20 text-accent-purple px-3 py-2 rounded-lg text-xs font-semibold disabled:opacity-50 transition-all flex items-center justify-center gap-2"
                    >
                        <Layers size={12} />
                        Launch {batchTasks.length} Tasks in Parallel
                    </button>
                </div>
            ) : (
                <div className="flex gap-2">
                    <input
                        className="flex-1 bg-surface-0/20 border border-surface-2 rounded px-3 py-1.5 text-xs text-text-primary placeholder-text-tertiary focus:outline-none focus:border-accent-primary/50"
                        placeholder="Delegate sub-task..."
                        value={taskDesc}
                        onChange={(e) => setTaskDesc(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleDelegate()}
                    />
                    <button
                        onClick={handleDelegate}
                        disabled={!taskDesc}
                        className="bg-surface-2 hover:bg-surface-3 text-text-primary px-3 py-1.5 rounded-lg text-xs disabled:opacity-50 transition-all flex items-center gap-2"
                    >
                        <Play size={10} className="fill-current" />
                        <span>Run</span>
                    </button>
                </div>
            )}
        </div>
    );
};
