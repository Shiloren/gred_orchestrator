import React, { useState, useEffect } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Select } from './ui/select';
import { useProviders } from '../hooks/useProviders';
import { useToast } from './Toast';
import { Server, Cloud, Cpu, Trash2, Activity, Play } from 'lucide-react';

export const ProviderSettings: React.FC = () => {
    const { providers, nodes, loadProviders, addProvider, removeProvider, testProvider } = useProviders();
    const { addToast } = useToast();

    const [newType, setNewType] = useState('groq');
    const [newKey, setNewKey] = useState('');
    const [newId, setNewId] = useState('groq-default');

    useEffect(() => {
        loadProviders();
    }, []);

    const handleAdd = async () => {
        if (!newKey && newType !== 'ollama') {
            showToast('API Key required for cloud providers', 'error');
            return;
        }

        // Config template based on type
        const config: any = { type: newType, id: newId };
        if (newKey) config.api_key = newKey;
        if (newType === 'ollama') config.base_url = "http://localhost:11434"; // Default

        try {
            await addProvider(config);
            showToast('Provider added successfully', 'success');
            setNewKey('');
        } catch (e) {
            showToast('Failed to add provider', 'error');
        }
    };

    return (
        <div className="space-y-6 text-slate-100 p-4">
            <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold flex items-center gap-2">
                    <Server className="w-5 h-5 text-indigo-400" />
                    Hybrid AI Providers
                </h2>
            </div>

            {/* Add New Provider */}
            <Card className="bg-slate-800/50 border-slate-700 p-4">
                <h3 className="text-sm font-semibold mb-3 text-slate-400 uppercase tracking-wider">Connect New Provider</h3>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
                    <div>
                        <label className="block text-xs text-slate-500 mb-1">Provider Type</label>
                        <select
                            value={newType}
                            onChange={(e) => { setNewType(e.target.value); setNewId(`${e.target.value}-1`); }}
                            className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm"
                        >
                            <option value="groq">Groq (Free Cloud)</option>
                            <option value="ollama">Ollama (Local NPU)</option>
                            <option value="codex">OpenAI / Codex</option>
                            <option value="openrouter">OpenRouter</option>
                        </select>
                    </div>
                    <div>
                        <label className="block text-xs text-slate-500 mb-1">ID (Name)</label>
                        <Input value={newId} onChange={(e) => setNewId(e.target.value)} className="bg-slate-900 border-slate-700" />
                    </div>
                    <div className="md:col-span-1">
                        <label className="block text-xs text-slate-500 mb-1">API Key {newType === 'ollama' && '(Optional)'}</label>
                        <Input
                            type="password"
                            value={newKey}
                            onChange={(e) => setNewKey(e.target.value)}
                            placeholder={newType === 'ollama' ? 'n/a' : 'sk-...'}
                            disabled={newType === 'ollama'}
                            className="bg-slate-900 border-slate-700"
                        />
                    </div>
                    <Button onClick={handleAdd} className="bg-indigo-600 hover:bg-indigo-500 text-white">
                        Connect
                    </Button>
                </div>
            </Card>

            {/* Node Status */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(nodes).map(([id, node]: [string, any]) => (
                    <Card key={id} className="bg-slate-800/30 border-slate-700 p-3">
                        <div className="flex items-center justify-between mb-2">
                            <span className="font-semibold text-sm flex items-center gap-2">
                                {id === 'ally_x' ? <Cpu className="w-4 h-4 text-emerald-400" /> : <Server className="w-4 h-4 text-blue-400" />}
                                {node.name}
                            </span>
                            <span className="text-xs text-slate-500">{node.type}</span>
                        </div>
                        <div className="w-full bg-slate-900 h-2 rounded-full overflow-hidden">
                            <div
                                className={`h-full transition-all duration-500 ${node.current_load >= node.max_concurrency ? 'bg-red-500' : 'bg-emerald-500'}`}
                                style={{ width: `${(node.current_load / node.max_concurrency) * 100}%` }}
                            />
                        </div>
                        <div className="flex justify-between mt-1 text-xs text-slate-400">
                            <span>Load: {node.current_load} / {node.max_concurrency} agents</span>
                            <span>{node.current_load >= node.max_concurrency ? 'FULL' : 'AVAILABLE'}</span>
                        </div>
                    </Card>
                ))}
            </div>

            {/* Active Providers List */}
            <div className="space-y-3">
                <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Active Providers</h3>
                {providers.length === 0 && (
                    <div className="text-slate-500 text-center py-6 bg-slate-950/30 rounded border border-dashed border-slate-800">
                        No providers configured. Gred will perform limited local mocking.
                    </div>
                )}
                {providers.map((p) => (
                    <Card key={p.id} className="bg-slate-900/50 border-slate-700 p-4 flex items-center justify-between group hover:border-slate-600 transition-colors">
                        <div className="flex items-center gap-3">
                            <div className={`p-2 rounded-lg ${p.is_local ? 'bg-emerald-500/10 text-emerald-400' : 'bg-blue-500/10 text-blue-400'}`}>
                                {p.is_local ? <Cpu className="w-5 h-5" /> : <Cloud className="w-5 h-5" />}
                            </div>
                            <div>
                                <div className="font-medium text-slate-200">{p.id}</div>
                                <div className="text-xs text-slate-500 uppercase">{p.type} • {p.is_local ? 'Local' : 'Cloud'}</div>
                            </div>
                        </div>

                        <div className="flex items-center gap-2">
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => testProvider(p.id)}
                                className="text-slate-400 hover:text-white"
                            >
                                <Activity className="w-4 h-4 mr-1" />
                                Test
                            </Button>
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => removeProvider(p.id)}
                                className="text-red-400 hover:text-red-300 hover:bg-red-900/20"
                            >
                                <Trash2 className="w-4 h-4" />
                            </Button>
                        </div>
                    </Card>
                ))}
            </div>
        </div>
    );
};
