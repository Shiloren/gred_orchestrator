import { useState, useCallback } from 'react';
import { Plan, PlanCreateRequest, API_BASE } from '../types';

export function usePlanEngine() {
    const [currentPlan, setCurrentPlan] = useState<Plan | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const createPlan = useCallback(async (req: PlanCreateRequest) => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`${API_BASE}/ui/plan/create`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(req),
            });
            if (!response.ok) throw new Error('Failed to create plan');
            const plan: Plan = await response.json();
            setCurrentPlan(plan);
            return plan;
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
            return null;
        } finally {
            setLoading(false);
        }
    }, []);

    const fetchPlan = useCallback(async (planId: string) => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`${API_BASE}/ui/plan/${planId}`);
            if (!response.ok) throw new Error('Failed to fetch plan');
            const plan: Plan = await response.json();
            setCurrentPlan(plan);
            return plan;
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
            return null;
        } finally {
            setLoading(false);
        }
    }, []);

    const approvePlan = useCallback(async (planId: string) => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`${API_BASE}/ui/plan/${planId}/approve`, {
                method: 'POST',
            });
            if (!response.ok) throw new Error('Failed to approve plan');
            if (currentPlan?.id === planId) {
                setCurrentPlan({ ...currentPlan, status: 'approved' });
            }
            return true;
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
            return false;
        } finally {
            setLoading(false);
        }
    }, [currentPlan]);

    const updatePlan = useCallback(async (planId: string, updates: Partial<Plan>) => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`${API_BASE}/ui/plan/${planId}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updates),
            });
            if (!response.ok) throw new Error('Failed to update plan');
            const plan: Plan = await response.json();
            setCurrentPlan(plan);
            return plan;
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
            return null;
        } finally {
            setLoading(false);
        }
    }, []);

    return {
        currentPlan,
        loading,
        error,
        createPlan,
        fetchPlan,
        approvePlan,
        updatePlan,
        setCurrentPlan,
    };
}
