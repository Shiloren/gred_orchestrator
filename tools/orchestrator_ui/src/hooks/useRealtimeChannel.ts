import { useEffect, useState, useCallback } from 'react';
import { API_BASE } from '../types';

export type SocketStatus = 'CONNECTING' | 'OPEN' | 'CLOSING' | 'CLOSED';

export interface RealtimeMessage {
    type: string;
    payload: any;
    [key: string]: any;
}

type MessageHandler = (message: RealtimeMessage) => void;

// Simple event bus for socket messages
class SocketBus {
    private listeners: Record<string, MessageHandler[]> = {};

    subscribe(type: string, handler: MessageHandler) {
        if (!this.listeners[type]) {
            this.listeners[type] = [];
        }
        this.listeners[type].push(handler);
        return () => {
            this.listeners[type] = this.listeners[type].filter(h => h !== handler);
        };
    }

    emit(message: RealtimeMessage) {
        const type = message.type;
        if (this.listeners[type]) {
            this.listeners[type].forEach(h => h(message));
        }
        if (this.listeners['*']) {
            this.listeners['*'].forEach(h => h(message));
        }
    }
}

const bus = new SocketBus();
let socket: WebSocket | null = null;
let reconnectTimer: any = null; // NodeJS.Timeout or number
let status: SocketStatus = 'CLOSED';
let listeners: ((s: SocketStatus) => void)[] = [];

function notifyStatus(s: SocketStatus) {
    status = s;
    listeners.forEach(l => l(s));
}

function connect() {
    if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
        return;
    }

    let targetUrl = '';
    const protocol = globalThis.location.protocol === 'https:' ? 'wss:' : 'ws:';

    if (!API_BASE) {
        targetUrl = `${protocol}//${globalThis.location.host}/ws`;
    } else if (API_BASE.startsWith('http')) {
        targetUrl = API_BASE.replace(/^http/, 'ws') + '/ws';
    } else {
        targetUrl = `${protocol}//${API_BASE}/ws`;
    }

    // console.log('Connecting to WebSocket:', targetUrl);
    notifyStatus('CONNECTING');

    try {
        socket = new WebSocket(targetUrl);

        socket.onopen = () => {
            notifyStatus('OPEN');
            if (reconnectTimer) {
                clearTimeout(reconnectTimer);
                reconnectTimer = null;
            }
        };

        socket.onclose = () => {
            notifyStatus('CLOSED');
            socket = null;
            // Retry in 3s
            if (!reconnectTimer) {
                reconnectTimer = setTimeout(connect, 3000);
            }
        };

        socket.onerror = (err) => {
            console.error('WebSocket error:', err);
            socket?.close();
        };

        socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                bus.emit(data);
            } catch (e) {
                console.error('Failed to parse WS message:', e);
            }
        };

    } catch (e) {
        console.error('WebSocket connection failed:', e);
        reconnectTimer = setTimeout(connect, 3000);
    }
}

export function useRealtimeChannel() {
    const [socketStatus, setSocketStatus] = useState<SocketStatus>(status);

    useEffect(() => {
        const handler = (s: SocketStatus) => setSocketStatus(s);
        listeners.push(handler);

        // Ensure connection is started
        if (!socket && status === 'CLOSED') {
            connect();
        }

        return () => {
            listeners = listeners.filter(l => l !== handler);
        };
    }, []);

    const subscribe = useCallback((type: string, handler: MessageHandler) => {
        return bus.subscribe(type, handler);
    }, []);

    return { status: socketStatus, subscribe };
}

export function useSocketSubscription<T>(type: string, onMessage: (payload: T) => void, deps: any[] = []) {
    const { subscribe } = useRealtimeChannel();

    useEffect(() => {
        const unsub = subscribe(type, (msg) => {
            onMessage(msg.payload as T);
        });
        return unsub;
    }, [type, subscribe, ...deps]);
}
