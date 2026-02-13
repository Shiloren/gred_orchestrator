import React, { useState, useRef, useEffect } from 'react';
import { useAgentComms } from '../hooks/useAgentComms';
import { AgentMessage } from '../types';

interface AgentChatProps {
    agentId: string;
}

const AgentChat: React.FC<AgentChatProps> = ({ agentId }) => {
    const { messages, loading, sendMessage } = useAgentComms(agentId);
    const [input, setInput] = useState('');
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    const handleSend = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || loading) return;

        await sendMessage(input.trim(), 'instruction');
        setInput('');
    };

    return (
        <div className="flex flex-col h-full bg-surface-800/50 rounded-lg border border-white/10 overflow-hidden">
            <div className="p-3 border-b border-white/10 bg-white/5">
                <h3 className="text-sm font-semibold text-white/90">Agent Communication</h3>
            </div>

            <div
                ref={scrollRef}
                className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin scrollbar-thumb-white/10"
            >
                {messages.length === 0 ? (
                    <div className="h-full flex items-center justify-center text-white/30 text-sm italic">
                        No messages yet.
                    </div>
                ) : (
                    messages.map((msg: AgentMessage) => (
                        <div
                            key={msg.id}
                            className={`flex flex-col ${msg.from === 'orchestrator' || msg.from === 'user' ? 'items-end' : 'items-start'}`}
                        >
                            <div className="flex items-center space-x-2 mb-1">
                                <span className="text-[10px] uppercase tracking-wider text-white/40">
                                    {msg.from}
                                </span>
                                <span className="text-[10px] text-white/20">
                                    {new Date(msg.timestamp).toLocaleTimeString()}
                                </span>
                            </div>
                            <div
                                className={`max-w-[85%] p-3 rounded-2xl text-sm ${msg.from === 'orchestrator' || msg.from === 'user'
                                        ? 'bg-primary-600 text-white rounded-tr-none'
                                        : 'bg-white/10 text-white/90 rounded-tl-none'
                                    }`}
                            >
                                {msg.content}
                            </div>
                        </div>
                    ))
                )}
            </div>

            <form onSubmit={handleSend} className="p-3 bg-white/5 border-t border-white/10 flex space-x-2">
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Send instruction as orchestrator..."
                    className="flex-1 bg-black/20 border border-white/10 rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-primary-500 placeholder:text-white/20"
                />
                <button
                    type="submit"
                    disabled={!input.trim() || loading}
                    className="px-4 py-2 bg-primary-600 hover:bg-primary-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium rounded-md transition-colors"
                >
                    {loading ? '...' : 'Send'}
                </button>
            </form>
        </div>
    );
};

export default AgentChat;
