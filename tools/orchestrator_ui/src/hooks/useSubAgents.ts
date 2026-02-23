import { useState, useCallback, useEffect } from 'react';
import { SubAgent } from '../types';

export function useSubAgents(_agentId: string) {
    useEffect(() => {
        console.warn('useSubAgents: backend endpoints not implemented yet');
    }, []);

    const [subAgents] = useState<SubAgent[]>([]);

    const delegateTask = useCallback(async (_description: string, _model: string = "llama3") => { }, []);
    const delegateBatch = useCallback(async (_tasks: { description: string; model?: string }[]) => { }, []);
    const terminateSubAgent = useCallback(async (_subId: string) => { }, []);

    // Return mocked state to prevent 404s
    return {
        subAgents,
        loading: false,
        delegateTask,
        delegateBatch,
        terminateSubAgent
    };
}
