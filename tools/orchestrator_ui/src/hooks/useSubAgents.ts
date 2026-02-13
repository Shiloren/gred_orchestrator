import { useState, useEffect, useCallback } from 'react';
import { SubAgent, API_BASE } from '../types';

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
        const interval = setInterval(fetchSubAgents, 2000); // Polling for now
        return () => clearInterval(interval);
    }, [fetchSubAgents]);

    const delegateTask = async (description: string, model: string = "llama3") => {
        await fetch(`${API_BASE}/ui/agent/${agentId}/delegate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                subTaskDescription: description,
                modelPreference: model
            })
        });
        fetchSubAgents();
    };

    const terminateSubAgent = async (subId: string) => {
        await fetch(`${API_BASE}/ui/sub_agent/${subId}/terminate`, { method: 'POST' });
        fetchSubAgents();
    };

    return { subAgents, loading, delegateTask, terminateSubAgent };
}
