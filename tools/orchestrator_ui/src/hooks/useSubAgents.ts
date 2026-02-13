import { useState, useEffect, useCallback } from 'react';
import { SubAgent, API_BASE } from '../types';
import { useSocketSubscription } from './useRealtimeChannel';

export function useSubAgents(agentId: string) {
    const [subAgents, setSubAgents] = useState<SubAgent[]>([]);
    const [loading, setLoading] = useState(false);

    const fetchSubAgents = useCallback(async () => {
        try {
            const res = await fetch(`${API_BASE}/ui/agent/${agentId}/sub_agents`);
            if (res.ok) {
                const data = await res.json();
                setSubAgents(data);
            }
        } catch (e) {
            console.error(e);
        }
    }, [agentId]);

    useEffect(() => {
        setLoading(true);
        fetchSubAgents().finally(() => setLoading(false));
    }, [fetchSubAgents]);

    // Real-time updates
    useSocketSubscription('sub_agent_update', (updatedAgent: SubAgent) => {
        setSubAgents(prev => {
            const idx = prev.findIndex(a => a.id === updatedAgent.id);
            if (idx !== -1) {
                const newAgents = [...prev];
                newAgents[idx] = updatedAgent;
                return newAgents;
            } else if (updatedAgent.parentId === agentId) {
                return [...prev, updatedAgent];
            }
            return prev;
        });
    }, [agentId]);

    const delegateTask = async (description: string, model: string = "llama3") => {
        await fetch(`${API_BASE}/ui/agent/${agentId}/delegate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                subTaskDescription: description,
                modelPreference: model
            })
        });
        // fetchSubAgents(); // Socket should handle it
    };

    const terminateSubAgent = async (subId: string) => {
        await fetch(`${API_BASE}/ui/sub_agent/${subId}/terminate`, { method: 'POST' });
    };

    const delegateBatch = async (tasks: { description: string; model?: string }[]) => {
        await fetch(`${API_BASE}/ui/agent/${agentId}/delegate_batch`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                tasks: tasks.map(t => ({
                    subTaskDescription: t.description,
                    modelPreference: t.model ?? 'llama3'
                }))
            })
        });
    };

    return { subAgents, loading, delegateTask, delegateBatch, terminateSubAgent };
}
