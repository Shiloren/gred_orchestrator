import React, { useState } from 'react';
import { Send, ClipboardList } from 'lucide-react';
import { PlanCreateRequest } from '../types';

interface PlanBuilderProps {
    onCreate: (req: PlanCreateRequest) => Promise<void>;
    loading: boolean;
}

export const PlanBuilder: React.FC<PlanBuilderProps> = ({ onCreate, loading }) => {
    const [title, setTitle] = useState('');
    const [description, setDescription] = useState('');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!title || !description) return;
        onCreate({ title, task_description: description });
    };

    return (
        <div className="flex flex-col h-full bg-[#0a0a0a]">
            <div className="p-6 space-y-6">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-[#0a84ff]/10 flex items-center justify-center text-[#0a84ff]">
                        <ClipboardList size={20} />
                    </div>
                    <div>
                        <h2 className="text-lg font-semibold text-[#f5f5f7]">New Orchestrated Plan</h2>
                        <p className="text-xs text-[#86868b]">Define a task for the orchestrator to solve</p>
                    </div>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="space-y-1.5">
                        <label htmlFor="plan-title" className="text-[10px] uppercase tracking-widest font-bold text-[#86868b] pl-1">
                            Plan Title
                        </label>
                        <input
                            id="plan-title"
                            type="text"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            placeholder="e.g., Refactor Auth Module"
                            className="w-full bg-[#1c1c1e] border border-[#2c2c2e] rounded-xl px-4 py-2.5 text-sm text-[#f5f5f7] focus:outline-none focus:border-[#0a84ff] transition-all placeholder:text-[#424245]"
                            required
                        />
                    </div>

                    <div className="space-y-1.5">
                        <label htmlFor="plan-desc" className="text-[10px] uppercase tracking-widest font-bold text-[#86868b] pl-1">
                            Task Description
                        </label>
                        <textarea
                            id="plan-desc"
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            placeholder="Describe what you want GIMO to do..."
                            rows={6}
                            className="w-full bg-[#1c1c1e] border border-[#2c2c2e] rounded-xl px-4 py-3 text-sm text-[#f5f5f7] focus:outline-none focus:border-[#0a84ff] transition-all placeholder:text-[#424245] resize-none"
                            required
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={loading || !title || !description}
                        className={`
                            w-full flex items-center justify-center gap-2 py-3 rounded-xl font-bold text-xs uppercase tracking-widest transition-all
                            ${loading || !title || !description
                                ? 'bg-[#1c1c1e] text-[#424245] cursor-not-allowed'
                                : 'bg-[#0a84ff] text-white hover:bg-[#0071e3] shadow-lg shadow-[#0a84ff]/20 active:scale-[0.98]'}
                        `}
                    >
                        {loading ? (
                            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        ) : (
                            <>
                                <Send size={14} />
                                Generate Plan
                            </>
                        )}
                    </button>
                </form>
            </div>

            <div className="mt-auto p-6 border-t border-[#1c1c1e] bg-[#000000]/30 mr-2 rounded-tr-3xl">
                <h3 className="text-[10px] uppercase tracking-widest font-bold text-[#424245] mb-2 text-center">How it works</h3>
                <div className="grid grid-cols-2 gap-4">
                    <div className="text-[10px] text-[#86868b] leading-relaxed">
                        <span className="text-[#f5f5f7] font-semibold block mb-0.5">1. Analysis</span> GIMO will scan the codebase and evaluate current state.
                    </div>
                    <div className="text-[10px] text-[#86868b] leading-relaxed">
                        <span className="text-[#f5f5f7] font-semibold block mb-0.5">2. Delegation</span> It will break tasks down and assign them to specialized agents.
                    </div>
                </div>
            </div>
        </div>
    );
};
