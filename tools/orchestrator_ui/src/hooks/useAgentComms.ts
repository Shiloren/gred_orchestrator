import { useState, useCallback, useEffect } from 'react';
import { AgentMessage, MessageType } from '../types';

export function useAgentComms(_agentId: string | null) {
    useEffect(() => {
        console.warn('useAgentComms: backend endpoints not implemented yet');
    }, []);

    const [messages] = useState<AgentMessage[]>([]);

    const sendMessage = useCallback(async (_content: string, _type: MessageType = 'instruction') => null, []);
    const refresh = useCallback(async () => { }, []);

    // Return mocked state to prevent 404s
    return {
        messages,
        loading: false,
        error: null as string | null,
        sendMessage,
        refresh
    };
}
