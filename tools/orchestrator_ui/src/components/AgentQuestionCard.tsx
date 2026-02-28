import React from 'react';
import { HelpCircle, Check, X, MessageSquareQuote } from 'lucide-react';
import { AgentQuestion } from '../types';

interface AgentQuestionCardProps {
    question: AgentQuestion;
    onAnswer: (questionId: string, answer: string) => void;
    onDismiss: (questionId: string) => void;
}

export const AgentQuestionCard: React.FC<AgentQuestionCardProps> = ({
    question,
    onAnswer,
    onDismiss
}) => {
    return (
        <div className="p-4 rounded-xl bg-surface-2 border border-border-primary shadow-lg animate-in fade-in slide-in-from-bottom-2 duration-300">
            <div className="flex items-start gap-3 mb-3">
                <div className="mt-1 p-1.5 rounded-lg bg-accent-primary/10 text-accent-primary">
                    <HelpCircle size={16} />
                </div>
                <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                        <span className="text-[10px] font-bold text-text-secondary uppercase tracking-wider">Agent Question</span>
                        <span className="text-[9px] text-text-tertiary font-mono">{new Date(question.timestamp).toLocaleTimeString()}</span>
                    </div>
                    <p className="text-xs text-text-primary leading-relaxed font-medium">
                        {question.question}
                    </p>
                </div>
            </div>

            {question.context && (
                <div className="mb-4 p-2.5 rounded-lg bg-surface-0/40 border border-border-primary flex gap-2">
                    <MessageSquareQuote size={12} className="text-text-secondary shrink-0 mt-0.5" />
                    <p className="text-[10px] text-text-secondary italic leading-snug">
                        {question.context}
                    </p>
                </div>
            )}

            <div className="flex gap-2">
                <button
                    onClick={() => onAnswer(question.id, 'Approved')}
                    className="flex-1 h-8 rounded-lg bg-accent-trust/10 border border-accent-trust/20 text-accent-trust text-[10px] font-bold hover:bg-accent-trust/20 transition-all flex items-center justify-center gap-1.5"
                >
                    <Check size={12} /> APPROVE
                </button>
                <button
                    onClick={() => onAnswer(question.id, 'Rejected')}
                    className="flex-1 h-8 rounded-lg bg-accent-alert/10 border border-accent-alert/20 text-accent-alert text-[10px] font-bold hover:bg-accent-alert/20 transition-all flex items-center justify-center gap-1.5"
                >
                    <X size={12} /> REJECT
                </button>
            </div>
            <button
                onClick={() => onDismiss(question.id)}
                className="w-full mt-2 h-7 rounded-lg text-text-tertiary hover:text-text-secondary text-[9px] font-bold uppercase tracking-widest transition-all"
            >
                Escalate to Orchestrator
            </button>
        </div>
    );
};
