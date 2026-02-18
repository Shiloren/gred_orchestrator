import React, { useMemo, useState, useEffect } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { useProviders } from '../hooks/useProviders';
import { useToast } from './Toast';
import { Server, Cloud, Cpu, Trash2, Activity, Download, CheckCircle2, AlertTriangle } from 'lucide-react';

export const ProviderSettings: React.FC = () => {
    const {
        providers,
        providerCapabilities,
        effectiveState,
        catalogs,
        catalogLoading,
        nodes,
        loadProviders,
        loadCatalog,
        installModel,
        getInstallJob,
        validateProvider,
        saveActiveProvider,
        removeProvider,
        testProvider,
    } = useProviders();
    const { addToast } = useToast();

    const [providerType, setProviderType] = useState('openai');
    const [providerId, setProviderId] = useState('openai-main');
    const [modelId, setModelId] = useState('');
    const [authMode, setAuthMode] = useState('api_key');
    const [apiKey, setApiKey] = useState('');
    const [account, setAccount] = useState('');
    const [baseUrl, setBaseUrl] = useState('');
    const [org, setOrg] = useState('');
    const [validateResult, setValidateResult] = useState<any>(null);
    const [installState, setInstallState] = useState<{ status: string; message: string; progress?: number; job_id?: string } | null>(null);

    const providerTypes = Object.keys(providerCapabilities);
    const catalog = catalogs[providerType];
    const isLoadingCatalog = Boolean(catalogLoading[providerType]);
    const authModes = catalog?.auth_modes_supported || providerCapabilities[providerType]?.auth_modes_supported || [];
    const supportsInstall = Boolean(catalog?.can_install);
    const accountModeAvailable = authModes.includes('account');
    const accountModeRelevantProvider = providerType === 'openai' || providerType === 'codex';
    const effectiveHealth = validateResult?.health || effectiveState?.health || 'unknown';
    const effectiveActionableError = validateResult?.error_actionable || effectiveState?.last_error_actionable || 'sin errores recientes';
    const roleLabel = useMemo(() => {
        const active = providers.find((p) => p.id === effectiveState?.active);
        if (!active) return 'unknown';
        return active.is_local ? 'local' : 'remote';
    }, [providers, effectiveState]);

    const modelGroups = useMemo(() => {
        const installed = catalog?.installed_models || [];
        const available = catalog?.available_models || [];
        const recommended = catalog?.recommended_models || [];
        return { installed, available, recommended };
    }, [catalog]);

    useEffect(() => {
        loadProviders();
    }, []);

    useEffect(() => {
        if (providerTypes.length > 0 && !providerTypes.includes(providerType)) {
            setProviderType(providerTypes[0]);
        }
    }, [providerTypes, providerType]);

    useEffect(() => {
        if (!providerType) return;
        loadCatalog(providerType).catch(() => addToast('No se pudo cargar el catálogo de modelos', 'error'));
        if (!providerId) setProviderId(`${providerType}-main`);
    }, [providerType]);

    useEffect(() => {
        if (!catalog) return;
        if (!modelId) {
            const first = catalog.installed_models[0]?.id || catalog.recommended_models[0]?.id || catalog.available_models[0]?.id || '';
            setModelId(first);
        }
        if (!authModes.includes(authMode)) {
            setAuthMode(authModes[0] || 'none');
        }
    }, [catalog]);

    const selectedModelInstalled = modelGroups.installed.some((m) => m.id === modelId);

    const handleInstallAndUse = async () => {
        if (!modelId) {
            addToast('Selecciona un modelo para instalar', 'error');
            return;
        }
        try {
            const res = await installModel(providerType, modelId);
            setInstallState(res);
            addToast(res?.message || 'Instalación lanzada', 'info');
        } catch {
            addToast('Error instalando el modelo', 'error');
        }
    };

    useEffect(() => {
        if (!installState?.job_id) return;
        if (!['queued', 'running'].includes(installState.status)) return;
        let cancelled = false;
        const timer = setInterval(async () => {
            try {
                const next = await getInstallJob(providerType, installState.job_id!);
                if (cancelled) return;
                setInstallState(next);
                if (next.status === 'done') {
                    addToast('Modelo instalado correctamente', 'success');
                    clearInterval(timer);
                }
                if (next.status === 'error') {
                    addToast(next.message || 'Error instalando modelo', 'error');
                    clearInterval(timer);
                }
            } catch {
                if (!cancelled) {
                    clearInterval(timer);
                }
            }
        }, 1200);
        return () => {
            cancelled = true;
            clearInterval(timer);
        };
    }, [installState?.job_id, installState?.status, providerType]);

    const handleTestConnection = async () => {
        try {
            const payload: any = {
                base_url: baseUrl || undefined,
                org: org || undefined,
            };
            if (authMode === 'api_key') payload.api_key = apiKey;
            if (authMode === 'account') payload.account = account;
            const result = await validateProvider(providerType, payload);
            setValidateResult(result);
            if (result.valid) {
                addToast('Conexión válida', 'success');
                if (result.effective_model) setModelId(result.effective_model);
            } else {
                addToast(result.error_actionable || 'Validación fallida', 'error');
            }
        } catch {
            addToast('No se pudo validar la conexión', 'error');
        }
    };

    const handleSaveAsActive = async () => {
        if (!providerId.trim() || !modelId.trim()) {
            addToast('Provider ID y modelo son obligatorios', 'error');
            return;
        }
        try {
            await saveActiveProvider({
                providerId: providerId.trim(),
                providerType: providerType,
                modelId: modelId.trim(),
                authMode,
                apiKey: authMode === 'api_key' ? apiKey : undefined,
                account: authMode === 'account' ? account : undefined,
                baseUrl: baseUrl || undefined,
                org: org || undefined,
            });
            addToast('Provider activo guardado', 'success');
        } catch {
            addToast('No se pudo guardar provider activo', 'error');
        }
    };

    return (
        <div className="space-y-6 text-[#f5f5f7] p-4">
            <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold flex items-center gap-2">
                    <Server className="w-5 h-5 text-indigo-400" />
                    Provider Settings
                </h2>
            </div>

            <Card className="bg-[#1c1c1e] border-[#2c2c2e] p-4">
                <h3 className="text-sm font-semibold mb-3 text-[#86868b] uppercase tracking-wider">Estado efectivo actual</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
                    <div><span className="text-[#86868b]">Provider activo:</span> <span className="font-semibold">{effectiveState?.active || 'n/a'}</span></div>
                    <div><span className="text-[#86868b]">Modelo efectivo:</span> <span className="font-semibold">{effectiveState?.model_id || 'n/a'}</span></div>
                    <div><span className="text-[#86868b]">Role:</span> <span className="font-semibold">{roleLabel}</span></div>
                    <div><span className="text-[#86868b]">Health:</span> <span className="font-semibold">{effectiveHealth}</span></div>
                    <div className="md:col-span-2"><span className="text-[#86868b]">Error accionable:</span> <span className="font-semibold text-[#ff9f0a]">{effectiveActionableError}</span></div>
                </div>
            </Card>

            <Card className="bg-[#1c1c1e] border-[#2c2c2e] p-4">
                <h3 className="text-sm font-semibold mb-3 text-[#86868b] uppercase tracking-wider">Configurar provider</h3>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
                    <div>
                        <label className="block text-xs text-[#86868b] mb-1">Provider Type</label>
                        <select
                            value={providerType}
                            onChange={(e) => {
                                setProviderType(e.target.value);
                                setProviderId(`${e.target.value}-main`);
                                setModelId('');
                                setValidateResult(null);
                            }}
                            className="w-full bg-[#0a0a0a] border border-[#2c2c2e] rounded p-2 text-sm text-[#f5f5f7]"
                        >
                            {(providerTypes.length > 0 ? providerTypes : ['openai', 'codex', 'ollama_local', 'groq', 'openrouter', 'custom_openai_compatible']).map((canonical) => (
                                <option key={canonical} value={canonical}>{canonical}</option>
                            ))}
                        </select>
                    </div>
                    <div>
                        <label className="block text-xs text-[#86868b] mb-1">ID (Name)</label>
                        <Input value={providerId} onChange={(e) => setProviderId(e.target.value)} className="bg-[#0a0a0a] border-[#2c2c2e] text-[#f5f5f7]" />
                    </div>

                    <div>
                        <label className="block text-xs text-[#86868b] mb-1">ID/Name (modelo)</label>
                        <select
                            value={modelId}
                            onChange={(e) => setModelId(e.target.value)}
                            className="w-full bg-[#0a0a0a] border border-[#2c2c2e] rounded p-2 text-sm text-[#f5f5f7]"
                        >
                            <option value="">{isLoadingCatalog ? 'Cargando catálogo...' : 'Selecciona modelo'}</option>
                            {modelGroups.installed.length > 0 && (
                                <optgroup label="Installed">
                                    {modelGroups.installed.map((m) => <option key={`i-${m.id}`} value={m.id}>{m.label}</option>)}
                                </optgroup>
                            )}
                            {modelGroups.available.length > 0 && (
                                <optgroup label="Available to download">
                                    {modelGroups.available.map((m) => <option key={`a-${m.id}`} value={m.id}>{m.label}</option>)}
                                </optgroup>
                            )}
                            {modelGroups.recommended.length > 0 && (
                                <optgroup label="Recommended">
                                    {modelGroups.recommended.map((m) => <option key={`r-${m.id}`} value={m.id}>{m.label}</option>)}
                                </optgroup>
                            )}
                        </select>
                    </div>

                    <div>
                        <label className="block text-xs text-[#86868b] mb-1">Auth mode</label>
                        <select
                            value={authMode}
                            onChange={(e) => setAuthMode(e.target.value)}
                            className="w-full bg-[#0a0a0a] border border-[#2c2c2e] rounded p-2 text-sm text-[#f5f5f7]"
                        >
                            {authModes.map((mode) => <option key={mode} value={mode}>{mode}</option>)}
                            {authModes.length === 0 && <option value="none">none</option>}
                        </select>
                    </div>

                    <div>
                        <label className="block text-xs text-[#86868b] mb-1">Base URL (opcional)</label>
                        <Input value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)} placeholder="https://.../v1" className="bg-[#0a0a0a] border-[#2c2c2e] text-[#f5f5f7]" />
                    </div>

                    <div>
                        <label className="block text-xs text-[#86868b] mb-1">Organization (opcional)</label>
                        <Input value={org} onChange={(e) => setOrg(e.target.value)} className="bg-[#0a0a0a] border-[#2c2c2e] text-[#f5f5f7]" />
                    </div>

                    {authMode === 'api_key' && (
                        <div>
                            <label className="block text-xs text-[#86868b] mb-1">API Key</label>
                            <Input type="password" value={apiKey} onChange={(e) => setApiKey(e.target.value)} placeholder="sk-..." className="bg-[#0a0a0a] border-[#2c2c2e] text-[#f5f5f7]" />
                        </div>
                    )}
                    {authMode === 'account' && (
                        <div>
                            <label className="block text-xs text-[#86868b] mb-1">Account</label>
                            <Input value={account} onChange={(e) => setAccount(e.target.value)} placeholder="account/session token" className="bg-[#0a0a0a] border-[#2c2c2e] text-[#f5f5f7]" />
                        </div>
                    )}

                    <Button onClick={handleTestConnection} className="bg-[#2c2c2e] hover:bg-[#3a3a3c] text-white">
                        Test connection
                    </Button>
                    <Button onClick={handleSaveAsActive} className="bg-indigo-600 hover:bg-indigo-500 text-white">
                        Save as active provider
                    </Button>
                </div>

                {catalog?.warnings?.length ? (
                    <div className="mt-3 text-xs text-[#ff9f0a] space-y-1">
                        {catalog.warnings.map((w, idx) => <div key={`${w}-${idx}`}>⚠ {w}</div>)}
                    </div>
                ) : null}

                {accountModeAvailable || !accountModeRelevantProvider ? null : (
                    <div className="mt-3 text-xs text-[#ff9f0a]">Modo cuenta no disponible en este entorno; usa API key.</div>
                )}

                {!selectedModelInstalled && supportsInstall && modelId ? (
                    <div className="mt-4 p-3 rounded border border-[#2c2c2e] bg-[#0a0a0a] flex items-center justify-between gap-3">
                        <div className="text-xs text-[#f5f5f7]">Modelo no instalado. ¿Quieres descargarlo ahora?</div>
                        <Button onClick={handleInstallAndUse} className="bg-[#0a84ff] hover:bg-[#409cff] text-white text-xs px-3 py-2">
                            <Download className="w-3.5 h-3.5 mr-1" />
                            Download & Use
                        </Button>
                    </div>
                ) : null}

                {installState ? (
                    <div className="mt-3 p-3 rounded border border-[#2c2c2e] bg-[#0a0a0a]">
                        <div className="text-xs text-[#f5f5f7]">Instalación: {installState.status}</div>
                        <div className="text-xs text-[#86868b]">{installState.message}</div>
                        {typeof installState.progress === 'number' ? (
                            <div className="text-xs text-[#86868b]">Progreso: {Math.round(installState.progress * 100)}%</div>
                        ) : null}
                    </div>
                ) : null}

                {validateResult ? (
                    <div className={`mt-4 p-3 rounded border ${validateResult.valid ? 'border-[#32d74b]/40 bg-[#32d74b]/10' : 'border-[#ff3b30]/40 bg-[#ff3b30]/10'}`}>
                        <div className="flex items-center gap-2 text-sm">
                            {validateResult.valid ? <CheckCircle2 className="w-4 h-4 text-[#32d74b]" /> : <AlertTriangle className="w-4 h-4 text-[#ff3b30]" />}
                            <span>{validateResult.valid ? 'Conexión válida' : 'Conexión no válida'}</span>
                            <span className="text-xs text-[#86868b]">health: {validateResult.health}</span>
                        </div>
                        {validateResult.error_actionable ? <div className="mt-2 text-xs">Acción sugerida: {validateResult.error_actionable}</div> : null}
                    </div>
                ) : null}
            </Card>

            {/* Node Status */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(nodes).map(([id, node]: [string, any]) => (
                    <Card key={id} className="bg-[#1c1c1e]/70 border-[#2c2c2e] p-3">
                        <div className="flex items-center justify-between mb-2">
                            <span className="font-semibold text-sm flex items-center gap-2">
                                {id === 'ally_x' ? <Cpu className="w-4 h-4 text-emerald-400" /> : <Server className="w-4 h-4 text-blue-400" />}
                                {node.name}
                            </span>
                            <span className="text-xs text-[#86868b]">{node.type}</span>
                        </div>
                        <div className="w-full bg-[#0a0a0a] h-2 rounded-full overflow-hidden">
                            <div
                                className={`h-full transition-all duration-500 ${node.current_load >= node.max_concurrency ? 'bg-red-500' : 'bg-emerald-500'}`}
                                style={{ width: `${(node.current_load / node.max_concurrency) * 100}%` }}
                            />
                        </div>
                        <div className="flex justify-between mt-1 text-xs text-[#86868b]">
                            <span>Load: {node.current_load} / {node.max_concurrency} agents</span>
                            <span>{node.current_load >= node.max_concurrency ? 'FULL' : 'AVAILABLE'}</span>
                        </div>
                    </Card>
                ))}
            </div>

            <div className="space-y-3">
                <h3 className="text-sm font-semibold text-[#86868b] uppercase tracking-wider">Active Providers</h3>
                {providers.length === 0 && (
                    <div className="text-[#86868b] text-center py-6 bg-[#0a0a0a]/60 rounded border border-dashed border-[#2c2c2e]">
                        No providers configured. Gred will perform limited local mocking.
                    </div>
                )}
                {providers.map((p) => (
                    <Card key={p.id} className="bg-[#1c1c1e] border-[#2c2c2e] p-4 flex items-center justify-between group hover:border-[#3a3a3c] transition-colors">
                        <div className="flex items-center gap-3">
                            <div className={`p-2 rounded-lg ${p.is_local ? 'bg-emerald-500/10 text-emerald-400' : 'bg-blue-500/10 text-blue-400'}`}>
                                {p.is_local ? <Cpu className="w-5 h-5" /> : <Cloud className="w-5 h-5" />}
                            </div>
                            <div>
                                <div className="font-medium text-[#f5f5f7]">{p.id}</div>
                                <div className="text-xs text-[#86868b] uppercase">{p.type} • {p.is_local ? 'Local' : 'Cloud'}</div>
                                {p.capabilities && (
                                    <div className="text-[10px] text-[#6e6e73] mt-1">
                                        auth: {(p.capabilities.auth_modes_supported || []).join(', ') || 'n/a'}
                                    </div>
                                )}
                                <div className="text-[10px] text-[#6e6e73]">model: {p.model || p.config?.model || 'n/a'}</div>
                            </div>
                        </div>

                        <div className="flex items-center gap-2">
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => testProvider(p.id)}
                                className="text-[#86868b] hover:text-[#f5f5f7]"
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
