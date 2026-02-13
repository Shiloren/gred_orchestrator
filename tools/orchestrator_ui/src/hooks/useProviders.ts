import { useState, useCallback } from 'react';
import { API_BASE } from '../types';

export interface ProviderInfo {
    id: string;
    type: string;
    is_local: boolean;
    config: any;
}

export const useProviders = () => {
    const [providers, setProviders] = useState<ProviderInfo[]>([]);
    const [nodes, setNodes] = useState<any>({});
    const [loading, setLoading] = useState(false);

    const loadProviders = useCallback(async () => {
        setLoading(true);
        try {
            const res = await fetch(`${API_BASE}/ui/providers`, {
                headers: { 'Authorization': 'Bearer demo-token' }
            });
            if (res.ok) {
                const data = await res.json();
                setProviders(data);
            }

            const nodeRes = await fetch(`${API_BASE}/ui/nodes`, {
                headers: { 'Authorization': 'Bearer demo-token' }
            });
            if (nodeRes.ok) {
                const nodeData = await nodeRes.json();
                setNodes(nodeData);
            }
        } catch (error) {
            console.error("Failed to load providers", error);
        } finally {
            setLoading(false);
        }
    }, []);

    const addProvider = async (config: any) => {
        const res = await fetch(`${API_BASE}/ui/providers`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer demo-token"
            },
            body: JSON.stringify(config)
        });
        if (!res.ok) throw new Error("Failed to add");
        await loadProviders();
    };

    const removeProvider = async (id: string) => {
        await fetch(`${API_BASE}/ui/providers/${id}`, {
            method: "DELETE",
            headers: { 'Authorization': 'Bearer demo-token' }
        });
        await loadProviders();
    };

    const testProvider = async (id: string) => {
        try {
            const res = await fetch(`${API_BASE}/ui/providers/${id}/test`, {
                method: "POST",
                headers: { 'Authorization': 'Bearer demo-token' }
            });
            const data = await res.json();
            alert(`Test Result: ${data.status}\nMessage: ${data.message}`);
        } catch (e) {
            alert("Test failed check console");
        }
    };

    return {
        providers,
        nodes,
        loading,
        loadProviders,
        addProvider,
        removeProvider,
        testProvider
    };
};
