import { useState, useEffect, useCallback } from 'react';
import { QualityMetrics, API_BASE } from '../types';

export const useAgentQuality = (agentId: string | null) => {
    const [quality, setQuality] = useState<QualityMetrics | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchQuality = useCallback(async () => {
        if (!agentId) return;

        setLoading(true);
        try {
            const response = await fetch(`${API_BASE}/ui/agent/${agentId}/quality`, {
                headers: { 'Authorization': 'demo-token' }
            });
            if (!response.ok) throw new Error('Failed to fetch quality metrics');
            const data = await response.json();
            setQuality(data);
            setError(null);
        } catch (err) {
            console.error('Error fetching quality:', err);
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setLoading(false);
        }
    }, [agentId]);

    useEffect(() => {
        fetchQuality();
        const interval = setInterval(fetchQuality, 10000); // Poll every 10s
        return () => clearInterval(interval);
    }, [fetchQuality]);

    return { quality, loading, error, refetch: fetchQuality };
};
