import { useState, useCallback } from 'react';
import { Settings } from 'lucide-react';
import { TrustLevel, API_BASE } from '../types';
import { TrustBadge } from './TrustBadge';

interface AgentTrustEntry {
    agentId: string;
    label: string;
    trustLevel: TrustLevel;
}

interface TrustSettingsProps {
    agents?: AgentTrustEntry[];
}

const TRUST_LEVELS: { level: TrustLevel; label: string; description: string }[] = [
    { level: 'autonomous', label: 'Autonomous', description: 'Full control, no approval needed' },
    { level: 'supervised', label: 'Supervised', description: 'Actions require approval before execution' },
    { level: 'restricted', label: 'Restricted', description: 'Read-only, cannot perform actions' },
];

const DEFAULT_AGENTS: AgentTrustEntry[] = [
    { agentId: 'api', label: 'API Orchestrator', trustLevel: 'autonomous' },
    { agentId: 'tunnel', label: 'Cloudflare Tunnel', trustLevel: 'supervised' },
];

export const TrustSettings: React.FC<TrustSettingsProps> = ({ agents: initialAgents }) => {
    const [agents, setAgents] = useState<AgentTrustEntry[]>(initialAgents ?? DEFAULT_AGENTS);
    const [saving, setSaving] = useState<string | null>(null);

    const updateTrust = useCallback(async (agentId: string, newLevel: TrustLevel) => {
        setSaving(agentId);
        try {
            const params = new URLSearchParams({ trust_level: newLevel });
            await fetch(`${API_BASE}/ui/agent/${agentId}/trust?${params.toString()}`, {
                method: 'POST',
            });
            setAgents(prev =>
                prev.map(a => a.agentId === agentId ? { ...a, trustLevel: newLevel } : a)
            );
        } catch (err) {
            console.error('Failed to update trust level:', err);
        } finally {
            setSaving(null);
        }
    }, []);

    return (
        <div className="space-y-6 animate-fade-in">
            <div className="flex items-center gap-2 text-[#86868b] mb-4">
                <Settings size={14} />
                <span className="text-[10px] font-bold uppercase tracking-widest">Trust Configuration</span>
            </div>

            <div className="space-y-3">
                {agents.map(agent => (
                    <div
                        key={agent.agentId}
                        className="p-4 rounded-xl bg-[#141414] border border-[#1c1c1e] space-y-3"
                    >
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <span className="text-sm font-medium text-[#f5f5f7]">{agent.label}</span>
                                <TrustBadge level={agent.trustLevel} showLabel />
                            </div>
                            <span className="text-[10px] font-mono text-[#86868b]">{agent.agentId}</span>
                        </div>

                        <div className="flex gap-2">
                            {TRUST_LEVELS.map(({ level, label, description }) => (
                                <button
                                    key={level}
                                    onClick={() => updateTrust(agent.agentId, level)}
                                    disabled={saving === agent.agentId || agent.trustLevel === level}
                                    title={description}
                                    className={`
                                        flex-1 py-2 px-3 rounded-lg text-[10px] font-semibold uppercase tracking-wider
                                        border transition-all duration-200
                                        ${agent.trustLevel === level
                                            ? level === 'autonomous'
                                                ? 'bg-[#32d74b]/10 border-[#32d74b]/30 text-[#32d74b]'
                                                : level === 'supervised'
                                                    ? 'bg-[#ff9f0a]/10 border-[#ff9f0a]/30 text-[#ff9f0a]'
                                                    : 'bg-[#ff453a]/10 border-[#ff453a]/30 text-[#ff453a]'
                                            : 'bg-[#0a0a0a] border-[#2c2c2e] text-[#86868b] hover:bg-[#1c1c1e]'
                                        }
                                        disabled:opacity-50 disabled:cursor-not-allowed
                                    `}
                                >
                                    {label}
                                </button>
                            ))}
                        </div>
                    </div>
                ))}
            </div>

            <div className="p-3 rounded-lg bg-[#0a0a0a] border border-[#1c1c1e]">
                <p className="text-[10px] text-[#86868b] leading-relaxed">
                    Trust levels control how much autonomy each agent has.
                    <strong className="text-[#f5f5f7]"> Autonomous</strong> agents execute without approval.
                    <strong className="text-[#f5f5f7]"> Supervised</strong> agents request approval.
                    <strong className="text-[#f5f5f7]"> Restricted</strong> agents are read-only.
                </p>
            </div>
        </div>
    );
};
