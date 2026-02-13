import { useState, useCallback } from 'react';
import { API_BASE } from '../types';

export type AgentControlAction = 'pause' | 'resume' | 'cancel';

interface UseAgentControlReturn {
    paused: boolean;
    loading: boolean;
    error: string | null;
    pauseAgent: () => Promise<void>;
    resumeAgent: () => Promise<void>;
    cancelPlan: (planId: string) => Promise<void>;
}

export function useAgentControl(agentId: string | null): UseAgentControlReturn {
    const [paused, setPaused] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const sendAction = useCallback(async (action: AgentControlAction, planId?: string) => {
        if (!agentId) return;
        setLoading(true);
        setError(null);
        try {
            const params = new URLSearchParams({ action });
            if (planId) params.set('plan_id', planId);

            const response = await fetch(
                `${API_BASE}/ui/agent/${agentId}/control?${params.toString()}`,
                { method: 'POST' }
            );
            if (!response.ok) {
                throw new Error(`Agent control failed: ${response.statusText}`);
            }
        } catch (err) {
            const msg = err instanceof Error ? err.message : 'Unknown error';
            setError(msg);
        } finally {
            setLoading(false);
        }
    }, [agentId]);

    const pauseAgent = useCallback(async () => {
        await sendAction('pause');
        setPaused(true);
    }, [sendAction]);

    const resumeAgent = useCallback(async () => {
        await sendAction('resume');
        setPaused(false);
    }, [sendAction]);

    const cancelPlan = useCallback(async (planId: string) => {
        await sendAction('cancel', planId);
    }, [sendAction]);

    return { paused, loading, error, pauseAgent, resumeAgent, cancelPlan };
}
