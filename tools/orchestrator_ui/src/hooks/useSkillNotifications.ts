import { useEffect } from 'react';
import { API_BASE, SkillNotificationPayload } from '../types';
import { useAppStore } from '../stores/appStore';

/**
 * Global hook to listen for background skill execution notifications via SSE.
 */
export function useSkillNotifications() {
    const updateSkillRun = useAppStore(s => s.updateSkillRun);
    const authenticated = useAppStore(s => s.authenticated);

    useEffect(() => {
        if (!authenticated) return;

        let eventSource: EventSource | null = null;
        let reconnectTimeout: ReturnType<typeof setTimeout>;
        let backoffMs = 1000;

        const connect = () => {
            console.log('[SkillNotifications] Connecting to SSE stream...');
            eventSource = new EventSource(`${API_BASE}/ops/notifications/stream`, {
                withCredentials: true
            });

            eventSource.onopen = () => {
                console.log('[SkillNotifications] SSE Connected');
                backoffMs = 1000; // Reset backoff on success
            };

            eventSource.onmessage = (event) => {
                try {
                    const { event: type, data } = JSON.parse(event.data);

                    if (type === 'skill_execution_started' ||
                        type === 'skill_execution_progress' ||
                        type === 'skill_execution_finished') {

                        const payload = data as SkillNotificationPayload;
                        console.log(`[SkillNotifications] Event: ${type}`, payload);

                        updateSkillRun({
                            id: payload.skill_run_id,
                            skill_id: payload.skill_id,
                            command: payload.command,
                            status: payload.status,
                            progress: payload.progress,
                            message: payload.message,
                            started_at: payload.started_at,
                            finished_at: payload.finished_at
                        });
                    }
                } catch (err) {
                    console.error('[SkillNotifications] Error parsing SSE message:', err);
                }
            };

            eventSource.onerror = (err) => {
                console.error('[SkillNotifications] SSE Connection Error:', err);
                eventSource?.close();

                // Exponential backoff reconnection
                console.log(`[SkillNotifications] Reconnecting in ${backoffMs}ms...`);
                reconnectTimeout = setTimeout(connect, backoffMs);
                backoffMs = Math.min(backoffMs * 2, 30000); // Cap at 30s
            };
        };

        connect();

        return () => {
            console.log('[SkillNotifications] Cleaning up SSE...');
            eventSource?.close();
            clearTimeout(reconnectTimeout);
        };
    }, [authenticated, updateSkillRun]);
}
