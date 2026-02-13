import { useState, useCallback, useEffect } from 'react';
import { AgentMessage, API_BASE, MessageType } from '../types';
import { useSocketSubscription } from './useRealtimeChannel';

export function useAgentComms(agentId: string | null) {
    const [messages, setMessages] = useState<AgentMessage[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

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

    // Real-time subscription
    useSocketSubscription('chat_message', (msg: any) => {
        // payload wrapper handled in hook? No, hook returns payload as T if I used it right?
        // Wait, backend sends { type: ..., payload: ... }
        // useSocketSubscription implementation: onMessage(msg.payload as T)
        // So here 'msg' IS the payload (AgentMessage).
        // BUT backend sends: 
        // "type": "chat_message",
        // "agent_id": agent_id,
        // "payload": message.dict()

        // My useSocketSubscription unwrap logic:
        // const unsub = subscribe(type, (msg) => { onMessage(msg.payload as T); });
        // So 'msg' here is indeed message.dict() i.e. AgentMessage.
        // However, I should check agent_id from the wrapper?
        // The wrapper is gone. I need the full message to check agent_id if it's not in payload?
        // AgentMessage has agentId. So it is in payload.

        const message = msg as AgentMessage;
        if (agentId && message.agentId === agentId) {
            setMessages(prev => {
                if (prev.some(m => m.id === message.id)) return prev;
                return [...prev, message];
            });
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
            // Optimistic update or wait for socket? Socket is fast enough usually.
            // But let's keep it to be sure, or dedupe.
            setMessages(prev => {
                if (prev.some(m => m.id === newMessage.id)) return prev;
                return [...prev, newMessage];
            });
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
        } else {
            setMessages([]);
        }
    }, [agentId, fetchMessages]);

    return {
        messages,
        loading,
        error,
        sendMessage,
        refresh: fetchMessages
    };
}
