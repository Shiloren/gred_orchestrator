import { useCallback, useEffect } from 'react';

export type AgentControlAction = 'pause' | 'resume' | 'cancel';

interface UseAgentControlReturn {
    paused: boolean;
    loading: boolean;
    error: string | null;
    pauseAgent: () => Promise<void>;
    resumeAgent: () => Promise<void>;
    cancelPlan: (planId: string) => Promise<void>;
}

export function useAgentControl(_agentId: string | null): UseAgentControlReturn {
    useEffect(() => {
        console.warn('useAgentControl: backend endpoints not implemented yet');
    }, []);

    const nop = useCallback(async () => { }, []);

    // Return mocked state to prevent 404s
    return {
        paused: false,
        loading: false,
        error: null,
        pauseAgent: nop,
        resumeAgent: nop,
        cancelPlan: nop
    };
}
