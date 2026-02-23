import { useState, useCallback, useEffect } from 'react';
import { QualityMetrics } from '../types';

export const useAgentQuality = (_agentId: string | null) => {
    useEffect(() => {
        console.warn('useAgentQuality: backend endpoints not implemented yet');
    }, []);

    const [quality] = useState<QualityMetrics | null>(null);
    const refetch = useCallback(async () => { }, []);

    // Return mocked state to prevent 404s
    return {
        quality,
        loading: false,
        error: null as string | null,
        refetch
    };
};
