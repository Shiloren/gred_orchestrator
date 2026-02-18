import { useState, useCallback, useEffect } from 'react';
import { API_BASE } from '../types';

export interface RepoInfo {
    name: string;
    path: string;
}

export const useRepoService = (_token?: string) => {
    const [repos, setRepos] = useState<RepoInfo[]>([]);
    const [activeRepo, setActiveRepo] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchRepos = useCallback(async () => {
        try {
            const headers: HeadersInit = {};

            const res = await fetch(`${API_BASE}/ui/repos`, { headers, credentials: 'include' });
            if (!res.ok) throw new Error('Failed to fetch repositories');
            const data = await res.json();
            setRepos(data.repos || []);
            setActiveRepo(data.active_repo);
            setError(null);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        }
    }, []);

    const bootstrap = useCallback(async (path: string) => {
        setIsLoading(true);
        try {
            const headers: HeadersInit = {};

            const MODERN_BOOTSTRAP_ENDPOINT = `${API_BASE}/ui/repos/bootstrap?path=${encodeURIComponent(path)}`;
            const res = await fetch(MODERN_BOOTSTRAP_ENDPOINT, {
                method: 'POST',
                headers,
                credentials: 'include',
            });

            if (!res.ok) throw new Error('Failed to bootstrap repository');

            await fetchRepos();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setIsLoading(false);
        }
    }, [fetchRepos]);

    const selectRepo = useCallback(async (path: string) => {
        setIsLoading(true);
        try {
            const headers: HeadersInit = {};

            const res = await fetch(`${API_BASE}/ui/repos/select?path=${encodeURIComponent(path)}`, {
                method: 'POST',
                headers,
                credentials: 'include',
            });
            if (!res.ok) throw new Error('Failed to select repository');

            await fetchRepos();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setIsLoading(false);
        }
    }, [fetchRepos]);

    useEffect(() => {
        fetchRepos();
    }, [fetchRepos]);

    return {
        repos,
        activeRepo,
        isLoading,
        error,
        bootstrap,
        selectRepo,
        refresh: fetchRepos
    };
};
