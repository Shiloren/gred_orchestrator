import { useState, useCallback, useEffect, useRef } from 'react';
import { AgentMessage, API_BASE, MessageType } from '../types';

export function useAgentComms(agentId: string | null) {
    const [messages, setMessages] = useState<AgentMessage[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const pollIntervalRef = useRef<any>(null);

    const fetchMessages = useCallback(async () => {
        if (!agentId) return;
        try {
            const response = await fetch(`${API_BASE}/ui/agent/${agentId}/messages`);
            if (!response.ok) throw new Error('Failed to fetch messages');
            const data: AgentMessage[] = await response.json();
            setMessages(data);
        } catch (err) {
            console.error('Error fetching agent messages:', err);
        }
    }, [agentId]);

    const sendMessage = useCallback(async (content: string, type: MessageType = 'instruction') => {
        if (!agentId) return null;
        setLoading(true);
        setError(null);
        try {
            const params = new URLSearchParams({ content, type });
            const response = await fetch(`${API_BASE}/ui/agent/${agentId}/message?${params.toString()}`, {
                method: 'POST',
            });
            if (!response.ok) throw new Error('Failed to send message');
            const newMessage: AgentMessage = await response.json();
            setMessages(prev => [...prev, newMessage]);
            return newMessage;
        } catch (err) {
            const errMsg = err instanceof Error ? err.message : 'Unknown error';
            setError(errMsg);
            return null;
        } finally {
            setLoading(false);
        }
    }, [agentId]);

    useEffect(() => {
        if (agentId) {
            fetchMessages();
            pollIntervalRef.current = setInterval(fetchMessages, 3000);
        } else {
            setMessages([]);
        }

        return () => {
            if (pollIntervalRef.current) {
                clearInterval(pollIntervalRef.current);
            }
        };
    }, [agentId, fetchMessages]);

    return {
        messages,
        loading,
        error,
        sendMessage,
        refresh: fetchMessages
    };
}
