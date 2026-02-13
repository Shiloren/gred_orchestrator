import React, { useState, useEffect, useRef } from 'react';
import { Terminal, Activity } from 'lucide-react';

export const LiveLogs = () => {
    const [logs, setLogs] = useState<string[]>([]);
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const fetchLogs = async () => {
            try {
                const response = await fetch('/ui/audit?limit=50', {
                    headers: { 'Authorization': 'demo-token' }
                });
                const data = await response.json();
                if (data.lines) {
                    setLogs(data.lines);
                }
            } catch (error) {
                console.error('Error fetching logs:', error);
            }
        };

        fetchLogs();
        const interval = setInterval(fetchLogs, 3000);
        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [logs]);

    return (
        <div className="bg-[#000000] border border-[#38383a] rounded-xl overflow-hidden flex flex-col h-[300px] shadow-inner">
            <div className="bg-[#1c1c1e] px-4 py-2 border-b border-[#38383a] flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Terminal size={14} className="text-[#86868b]" />
                    <span className="text-xs font-mono text-[#86868b] uppercase tracking-wider">Audit Stream</span>
                </div>
                <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-[#32d74b] animate-pulse"></div>
                    <span className="text-[10px] text-[#32d74b]">LIVE</span>
                </div>
            </div>
            <div
                ref={scrollRef}
                className="p-4 font-mono text-xs overflow-y-auto flex-1 space-y-1"
            >
                {logs.map((log, i) => (
                    <div key={i} className="text-[#32d74b] opacity-80 border-l-2 border-[#32d74b] border-opacity-20 pl-2">
                        <span className="text-[#86868b] mr-2">[{new Date().toLocaleTimeString()}]</span>
                        {log}
                    </div>
                ))}
                {logs.length === 0 && (
                    <div className="text-[#86868b] italic">No active audit logs...</div>
                )}
            </div>
        </div>
    );
};
