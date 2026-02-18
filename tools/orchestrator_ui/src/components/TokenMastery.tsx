import { useEffect, useState } from 'react';
import {
    TrendingUp, Leaf, PiggyBank,
    Shield, Activity, Zap, DollarSign, Target, BarChart2,
    CheckCircle
} from 'lucide-react';
import {
    AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    BarChart, Bar, Cell
} from 'recharts';
import { useMasteryService } from '../hooks/useMasteryService';
import {
    UserEconomyConfig, MasteryStatus, CostAnalytics, BudgetForecast
} from '../types';

// Colors
const COLORS = {
    primary: '#af52de',
    success: '#32d74b',
    warning: '#ff9f0a',
    danger: '#ff453a',
    bg: '#1c1c1e',
    card: '#2c2c2e',
    text: '#f5f5f7',
    muted: '#86868b'
};

export function TokenMastery() {
    const { fetchConfig, saveConfig, fetchStatus, fetchAnalytics, fetchForecast } = useMasteryService();

    // State
    const [config, setConfig] = useState<UserEconomyConfig | null>(null);
    const [status, setStatus] = useState<MasteryStatus | null>(null);
    const [analytics, setAnalytics] = useState<CostAnalytics | null>(null);
    const [forecast, setForecast] = useState<BudgetForecast[]>([]);
    const [activeTab, setActiveTab] = useState<'dashboard' | 'settings'>('dashboard');

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [cfg, sts, ana, fct] = await Promise.all([
                fetchConfig(),
                fetchStatus(),
                fetchAnalytics(30),
                fetchForecast()
            ]);
            setConfig(cfg);
            setStatus(sts);
            setAnalytics(ana);
            setForecast(fct);
        } catch (err) {
            console.error(err);
        }
    };

    const handleConfigChange = async (update: Partial<UserEconomyConfig>) => {
        if (!config) return;
        const newConfig = { ...config, ...update };
        setConfig(newConfig);
        await saveConfig(newConfig); // Optimistic UI, verify error handling in production
        loadData(); // Refresh derived data
    };

    const handleEcoToggle = () => {
        if (!config) return;
        const modes: ('off' | 'binary' | 'smart')[] = ['off', 'smart', 'binary'];
        const currentIdx = modes.indexOf(config.eco_mode.mode);
        const nextMode = modes[(currentIdx + 1) % modes.length];

        handleConfigChange({
            eco_mode: { ...config.eco_mode, mode: nextMode }
        });
    };

    if (!config || !status || !analytics) {
        return <div className="p-8 text-center text-[#86868b]">Loading Token Mastery...</div>;
    }

    return (
        <div className="flex flex-col gap-6 p-6 animate-in fade-in slide-in-from-bottom-2 duration-500 max-w-7xl mx-auto">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="p-2.5 bg-[#af52de]/10 rounded-xl">
                        <TrendingUp size={22} className="text-[#af52de]" />
                    </div>
                    <div>
                        <h2 className="text-xl font-bold tracking-tight text-white">Token Mastery</h2>
                        <p className="text-xs text-[#86868b]">Economic Control & Intelligence Layer</p>
                    </div>
                </div>

                <div className="flex bg-[#2c2c2e] p-1 rounded-lg">
                    <button
                        onClick={() => setActiveTab('dashboard')}
                        className={`px-4 py-1.5 text-xs font-medium rounded-md transition-all ${activeTab === 'dashboard' ? 'bg-[#3a3a3c] text-white shadow-sm' : 'text-[#86868b] hover:text-white'}`}
                    >
                        Dashboard
                    </button>
                    <button
                        onClick={() => setActiveTab('settings')}
                        className={`px-4 py-1.5 text-xs font-medium rounded-md transition-all ${activeTab === 'settings' ? 'bg-[#3a3a3c] text-white shadow-sm' : 'text-[#86868b] hover:text-white'}`}
                    >
                        Economy Settings
                    </button>
                </div>
            </div>

            {activeTab === 'dashboard' ? (
                <div className="space-y-6">
                    {/* Top Stats Row */}
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <StatusCard
                            title="Total Savings (30d)"
                            value={`$${status.total_savings_usd.toFixed(2)}`}
                            subtitle={`${(status.efficiency_score * 100).toFixed(0)}% Efficiency`}
                            icon={<PiggyBank size={20} className="text-[#32d74b]" />}
                            color="#32d74b"
                        />
                        <StatusCard
                            title="Current Spend (30d)"
                            value={`$${analytics.daily_costs.reduce((acc, d) => acc + d.cost, 0).toFixed(2)}`}
                            subtitle="Total Estimated"
                            icon={<DollarSign size={20} className="text-[#0a84ff]" />}
                            color="#0a84ff"
                        />
                        <StatusCard
                            title="Autonomy Level"
                            value={config.autonomy_level.toUpperCase()}
                            subtitle={config.autonomy_level === 'manual' ? 'No auto-optimizations' : 'Active Optimization'}
                            icon={<Shield size={20} className="text-[#af52de]" />}
                            color="#af52de"
                        />
                        <div
                            role="button"
                            tabIndex={0}
                            className="bg-[#1c1c1e] border border-[#2c2c2e] rounded-xl p-4 flex flex-col justify-between cursor-pointer hover:border-[#32d74b]/50 transition-colors"
                            onClick={handleEcoToggle}
                            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') handleEcoToggle(); }}
                        >
                            <div className="flex justify-between items-start">
                                <div>
                                    <div className="text-[11px] text-[#86868b] font-medium uppercase tracking-wider">Eco-Mode</div>
                                    <div className="text-xl font-bold mt-1 text-white capitalize">{config.eco_mode.mode}</div>
                                </div>
                                <div className={`p-2 rounded-lg ${config.eco_mode.mode === 'off' ? 'bg-[#2c2c2e] text-[#86868b]' : 'bg-[#32d74b]/20 text-[#32d74b]'}`}>
                                    <Leaf size={20} />
                                </div>
                            </div>
                            <div className="mt-3 text-[11px] text-[#86868b]">
                                {config.eco_mode.mode === 'off' ? 'Tap to enable savings' : 'Active cost reduction'}
                            </div>
                        </div>
                    </div>

                    {/* Charts Row */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* Daily Cost Chart */}
                        <div className="bg-[#1c1c1e] border border-[#2c2c2e] rounded-xl p-5 min-h-[300px]">
                            <h3 className="text-sm font-semibold mb-6 flex items-center gap-2">
                                <Activity size={16} className="text-[#0a84ff]" />
                                Daily Cost Trend
                            </h3>
                            <ResponsiveContainer width="100%" height={240}>
                                <AreaChart data={analytics.daily_costs}>
                                    <defs>
                                        <linearGradient id="colorCost" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor={COLORS.primary} stopOpacity={0.3} />
                                            <stop offset="95%" stopColor={COLORS.primary} stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#2c2c2e" vertical={false} />
                                    <XAxis dataKey="date" stroke="#86868b" fontSize={10} tickFormatter={(d) => d.split('-').slice(1).join('/')} />
                                    <YAxis stroke="#86868b" fontSize={10} tickFormatter={(val) => `$${val}`} />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#1c1c1e', borderColor: '#2c2c2e', fontSize: '12px' }}
                                        labelStyle={{ color: '#86868b' }}
                                    />
                                    <Area type="monotone" dataKey="cost" stroke={COLORS.primary} fillOpacity={1} fill="url(#colorCost)" />
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>

                        {/* Spend by Model */}
                        <div className="bg-[#1c1c1e] border border-[#2c2c2e] rounded-xl p-5 min-h-[300px]">
                            <h3 className="text-sm font-semibold mb-6 flex items-center gap-2">
                                <BarChart2 size={16} className="text-[#ff9f0a]" />
                                Spend by Model
                            </h3>
                            <ResponsiveContainer width="100%" height={240}>
                                <BarChart data={analytics.by_model} layout="vertical">
                                    <CartesianGrid strokeDasharray="3 3" stroke="#2c2c2e" horizontal={false} />
                                    <XAxis type="number" stroke="#86868b" fontSize={10} tickFormatter={(val) => `$${val}`} />
                                    <YAxis dataKey="model" type="category" width={100} stroke="#86868b" fontSize={10} />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#1c1c1e', borderColor: '#2c2c2e', fontSize: '12px' }}
                                        cursor={{ fill: '#2c2c2e', opacity: 0.4 }}
                                    />
                                    <Bar dataKey="cost" fill={COLORS.warning} radius={[0, 4, 4, 0]}>
                                        {analytics.by_model.map((entry, index) => (
                                            <Cell key={`model-${entry.model}`} fill={[COLORS.warning, COLORS.primary, COLORS.success, COLORS.danger][index % 4]} />
                                        ))}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    {/* Bottom Row: ROI Leaderboard & Forecast */}
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        {/* ROI Leaderboard */}
                        <div className="lg:col-span-2 bg-[#1c1c1e] border border-[#2c2c2e] rounded-xl p-5">
                            <h3 className="text-sm font-semibold mb-4 flex items-center gap-2">
                                <Zap size={16} className="text-[#ffd60a]" />
                                ROI Leaderboard
                            </h3>
                            <div className="overflow-x-auto">
                                <table className="w-full text-xs text-left">
                                    <thead>
                                        <tr className="border-b border-[#2c2c2e] text-[#86868b]">
                                            <th className="py-2 font-medium">Model</th>
                                            <th className="py-2 font-medium">Task</th>
                                            <th className="py-2 font-medium">ROI Score</th>
                                            <th className="py-2 font-medium">Avg Quality</th>
                                            <th className="py-2 font-medium">Avg Cost</th>
                                            <th className="py-2 font-medium text-right">Samples</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {analytics.roi_leaderboard.slice(0, 5).map((row) => (
                                            <tr key={`${row.model}-${row.task_type}`} className="border-b border-[#2c2c2e]/50 hover:bg-[#2c2c2e]/30">
                                                <td className="py-2.5 font-medium text-white">{row.model}</td>
                                                <td className="py-2.5 text-[#86868b]">{row.task_type}</td>
                                                <td className="py-2.5 font-mono text-[#32d74b]">{row.roi_score.toFixed(1)}</td>
                                                <td className="py-2.5">
                                                    <div className="flex items-center gap-2">
                                                        <div className="w-12 h-1.5 bg-[#2c2c2e] rounded-full overflow-hidden">
                                                            <div className="h-full bg-[#af52de]" style={{ width: `${row.avg_quality}%` }} />
                                                        </div>
                                                        <span className="text-[#86868b]">{Math.round(row.avg_quality)}%</span>
                                                    </div>
                                                </td>
                                                <td className="py-2.5 font-mono text-[#86868b]">${row.avg_cost.toFixed(4)}</td>
                                                <td className="py-2.5 text-right text-[#86868b]">{row.sample_count}</td>
                                            </tr>
                                        ))}
                                        {analytics.roi_leaderboard.length === 0 && (
                                            <tr>
                                                <td colSpan={6} className="py-8 text-center text-[#86868b]">
                                                    No ROI data collected yet. Run workflows to generate stats.
                                                </td>
                                            </tr>
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>

                        {/* Budget Forecast */}
                        <div className="bg-[#1c1c1e] border border-[#2c2c2e] rounded-xl p-5">
                            <h3 className="text-sm font-semibold mb-4 flex items-center gap-2">
                                <Target size={16} className="text-[#ff453a]" />
                                Budget Health
                            </h3>
                            <div className="space-y-4">
                                {forecast.length > 0 ? forecast.map((f) => (
                                    <div key={`forecast-${f.scope}`} className="space-y-2">
                                        <div className="flex justify-between text-xs">
                                            <span className="font-medium text-white capitalize">{f.scope} Budget</span>
                                            <span className="text-[#86868b]">${f.current_spend.toFixed(2)} / ${f.limit?.toFixed(2) ?? '∞'}</span>
                                        </div>
                                        <div className="h-2 bg-[#2c2c2e] rounded-full overflow-hidden">
                                            <div
                                                className={`h-full rounded-full ${f.alert_level === 'critical' ? 'bg-[#ff453a]' : f.alert_level === 'warning' ? 'bg-[#ff9f0a]' : 'bg-[#32d74b]'}`}
                                                style={{ width: `${Math.min(100, 100 - (f.remaining_pct ?? 100))}%` }}
                                            />
                                        </div>
                                        <div className="flex justify-between text-[10px] text-[#86868b]">
                                            <span>{f.remaining_pct?.toFixed(0)}% remaining</span>
                                            <span>{f.hours_to_exhaustion ? `~${f.hours_to_exhaustion}h left` : 'Stable'}</span>
                                        </div>
                                    </div>
                                )) : (
                                    <div className="text-center py-8 text-[#86868b] text-xs">
                                        No active budgets configured.
                                    </div>
                                )}

                                <div className="mt-6 pt-4 border-t border-[#2c2c2e]">
                                    <h4 className="text-xs font-semibold mb-2">Optimization Tips</h4>
                                    <div className="space-y-2">
                                        {status.tips.slice(0, 3).map((tip, idx) => (
                                            <div key={idx} className="bg-[#2c2c2e]/30 border border-[#2c2c2e] rounded p-2 text-[10px] leading-tight text-[#d1d1d6]">
                                                {tip}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            ) : (
                <EconomySettings config={config} onChange={handleConfigChange} />
            )}
        </div>
    );
}

function StatusCard({ title, value, subtitle, icon, color }: any) {
    return (
        <div className="bg-[#1c1c1e] border border-[#2c2c2e] rounded-xl p-4 flex flex-col justify-between hover:border-gray-600 transition-colors">
            <div className="flex justify-between items-start">
                <div>
                    <div className="text-[11px] text-[#86868b] font-medium uppercase tracking-wider">{title}</div>
                    <div className="text-xl font-bold mt-1 text-white" style={{ color: color }}>{value}</div>
                </div>
                <div className="p-2 rounded-lg bg-[#2c2c2e] text-[#86868b]">
                    {icon}
                </div>
            </div>
            <div className="mt-3 text-[11px] text-[#86868b]">
                {subtitle}
            </div>
        </div>
    );
}

function EconomySettings({ config, onChange }: { config: UserEconomyConfig, onChange: (u: Partial<UserEconomyConfig>) => void }) {
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-6">
                {/* Autonomy Level */}
                <div className="bg-[#1c1c1e] border border-[#2c2c2e] rounded-xl p-6">
                    <h3 className="text-sm font-semibold mb-4 text-white">Autonomy Level</h3>
                    <div className="space-y-3">
                        {['manual', 'advisory', 'guided', 'autonomous'].map((level) => (
                            <div
                                key={level}
                                role="button"
                                tabIndex={0}
                                onClick={() => onChange({ autonomy_level: level as any })}
                                onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') onChange({ autonomy_level: level as any }); }}
                                className={`p-3 rounded-lg border cursor-pointer transition-all ${config.autonomy_level === level ? 'bg-[#af52de]/10 border-[#af52de] ring-1 ring-[#af52de]' : 'bg-[#2c2c2e]/50 border-[#2c2c2e] hover:bg-[#2c2c2e]'}`}
                            >
                                <div className="flex items-center justify-between">
                                    <span className="text-sm font-medium text-white capitalize">{level}</span>
                                    {config.autonomy_level === level && <CheckCircle size={16} className="text-[#af52de]" />}
                                </div>
                                <div className="text-xs text-[#86868b] mt-1">
                                    {level === 'manual' && 'GIMO acts only as a recorder. No active changes.'}
                                    {level === 'advisory' && 'GIMO suggests changes but does not apply them.'}
                                    {level === 'guided' && 'Optimization within configured floor/ceiling bounds.'}
                                    {level === 'autonomous' && 'Full cascading and eco-mode enabled within budget.'}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Routing Boundaries */}
                <div className="bg-[#1c1c1e] border border-[#2c2c2e] rounded-xl p-6">
                    <h3 className="text-sm font-semibold mb-4 text-white">Model Boundaries</h3>
                    <div className="space-y-4">
                        <div>
                            <label htmlFor="model-floor" className="text-xs text-[#86868b] block mb-1.5">Model Floor (Min Quality)</label>
                            <select
                                id="model-floor"
                                value={config.model_floor || ''}
                                onChange={(e) => onChange({ model_floor: e.target.value || null })}
                                className="w-full bg-[#2c2c2e] border border-[#3a3a3c] rounded-md px-3 py-2 text-xs text-white focus:outline-none focus:border-[#af52de]"
                            >
                                <option value="">None (Allow Local/Nano)</option>
                                <option value="haiku">Haiku / Mini</option>
                                <option value="sonnet">Sonnet / GPT-4o</option>
                            </select>
                        </div>
                        <div>
                            <label htmlFor="model-ceiling" className="text-xs text-[#86868b] block mb-1.5">Model Ceiling (Max Cost)</label>
                            <select
                                id="model-ceiling"
                                value={config.model_ceiling || ''}
                                onChange={(e) => onChange({ model_ceiling: e.target.value || null })}
                                className="w-full bg-[#2c2c2e] border border-[#3a3a3c] rounded-md px-3 py-2 text-xs text-white focus:outline-none focus:border-[#af52de]"
                            >
                                <option value="">None (Allow Opus/O1)</option>
                                <option value="sonnet">Sonnet / GPT-4o</option>
                                <option value="haiku">Haiku / Mini</option>
                            </select>
                        </div>
                    </div>
                </div>
            </div>

            <div className="space-y-6">
                {/* Feature Toggles */}
                <div className="bg-[#1c1c1e] border border-[#2c2c2e] rounded-xl p-6">
                    <h3 className="text-sm font-semibold mb-4 text-white">Features</h3>
                    <div className="space-y-6">
                        <div className="space-y-3">
                            <Toggle
                                label="Cascade Execution"
                                desc="Establish confidence chain from cheaper to stronger models"
                                enabled={config.cascade.enabled}
                                onToggle={() => onChange({ cascade: { ...config.cascade, enabled: !config.cascade.enabled } })}
                            />
                            {config.cascade.enabled && (
                                <div className="grid grid-cols-2 gap-3 p-3 bg-[#2c2c2e]/30 border border-[#2c2c2e] rounded-lg mt-2 animate-in fade-in zoom-in-95 duration-200">
                                    <div>
                                        <label className="text-[10px] text-[#86868b] block mb-1">Min Tier</label>
                                        <select
                                            value={config.cascade.min_tier}
                                            onChange={(e) => onChange({ cascade: { ...config.cascade, min_tier: e.target.value } })}
                                            className="w-full bg-[#1c1c1e] border border-[#3a3a3c] rounded px-2 py-1 text-[10px] text-white"
                                        >
                                            <option value="local">Local</option>
                                            <option value="haiku">Haiku</option>
                                            <option value="sonnet">Sonnet</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label className="text-[10px] text-[#86868b] block mb-1">Max Tier</label>
                                        <select
                                            value={config.cascade.max_tier}
                                            onChange={(e) => onChange({ cascade: { ...config.cascade, max_tier: e.target.value } })}
                                            className="w-full bg-[#1c1c1e] border border-[#3a3a3c] rounded px-2 py-1 text-[10px] text-white"
                                        >
                                            <option value="haiku">Haiku</option>
                                            <option value="sonnet">Sonnet</option>
                                            <option value="opus">Opus</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label className="text-[10px] text-[#86868b] block mb-1">Quality Threshold (%)</label>
                                        <input
                                            type="number"
                                            value={config.cascade.quality_threshold}
                                            onChange={(e) => onChange({ cascade: { ...config.cascade, quality_threshold: Number(e.target.value) } })}
                                            className="w-full bg-[#1c1c1e] border border-[#3a3a3c] rounded px-2 py-1 text-[10px] text-white"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-[10px] text-[#86868b] block mb-1">Max Escalations</label>
                                        <input
                                            type="number"
                                            value={config.cascade.max_escalations}
                                            onChange={(e) => onChange({ cascade: { ...config.cascade, max_escalations: Number(e.target.value) } })}
                                            className="w-full bg-[#1c1c1e] border border-[#3a3a3c] rounded px-2 py-1 text-[10px] text-white"
                                        />
                                    </div>
                                </div>
                            )}
                        </div>

                        <Toggle
                            label="ROI Routing"
                            desc="Route based on historical quality/cost ratio"
                            enabled={config.allow_roi_routing}
                            onToggle={() => onChange({ allow_roi_routing: !config.allow_roi_routing })}
                        />

                        <div className="space-y-3">
                            <Toggle
                                label="Semantic Cache"
                                desc="Cache identical prompts (normalized) for 24h"
                                enabled={config.cache_enabled}
                                onToggle={() => onChange({ cache_enabled: !config.cache_enabled })}
                            />
                            {config.cache_enabled && (
                                <div className="p-3 bg-[#2c2c2e]/30 border border-[#2c2c2e] rounded-lg mt-2 animate-in fade-in zoom-in-95 duration-200">
                                    <label className="text-[10px] text-[#86868b] block mb-1">TTL (Hours)</label>
                                    <input
                                        type="number"
                                        value={config.cache_ttl_hours}
                                        onChange={(e) => onChange({ cache_ttl_hours: Number(e.target.value) })}
                                        className="w-full bg-[#1c1c1e] border border-[#3a3a3c] rounded px-2 py-1 text-[10px] text-white"
                                    />
                                </div>
                            )}
                        </div>

                        <Toggle
                            label="Cost Predictions"
                            desc="Show estimated cost before workflow execution"
                            enabled={config.show_cost_predictions}
                            onToggle={() => onChange({ show_cost_predictions: !config.show_cost_predictions })}
                        />

                        {config.eco_mode.mode === 'smart' && (
                            <div className="grid grid-cols-2 gap-3 p-3 bg-[#32d74b]/10 border border-[#32d74b]/30 rounded-lg animate-in fade-in zoom-in-95 duration-200">
                                <div className="col-span-2 text-[10px] font-semibold text-[#32d74b] uppercase tracking-wider">Smart Eco-Mode Thresholds</div>
                                <div>
                                    <label className="text-[10px] text-[#86868b] block mb-1">Aggressive (0-1)</label>
                                    <input
                                        type="number"
                                        step="0.05"
                                        value={config.eco_mode.confidence_threshold_aggressive || 0.85}
                                        onChange={(e) => onChange({ eco_mode: { ...config.eco_mode, confidence_threshold_aggressive: Number(e.target.value) } })}
                                        className="w-full bg-[#1c1c1e] border border-[#3a3a3c] rounded px-2 py-1 text-[10px] text-white"
                                    />
                                </div>
                                <div>
                                    <label className="text-[10px] text-[#86868b] block mb-1">Moderate (0-1)</label>
                                    <input
                                        type="number"
                                        step="0.05"
                                        value={config.eco_mode.confidence_threshold_moderate || 0.70}
                                        onChange={(e) => onChange({ eco_mode: { ...config.eco_mode, confidence_threshold_moderate: Number(e.target.value) } })}
                                        className="w-full bg-[#1c1c1e] border border-[#3a3a3c] rounded px-2 py-1 text-[10px] text-white"
                                    />
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* Budget Config */}
                <div className="bg-[#1c1c1e] border border-[#2c2c2e] rounded-xl p-6">
                    <h3 className="text-sm font-semibold mb-4 text-white">Budgets & Alerts</h3>
                    <div className="space-y-6">
                        <div>
                            <label htmlFor="global-budget" className="text-xs text-[#86868b] block mb-1.5">Global Monthly Limit (USD)</label>
                            <input
                                id="global-budget"
                                type="number"
                                value={config.global_budget_usd || ''}
                                placeholder="No Limit"
                                onChange={(e) => onChange({ global_budget_usd: e.target.value ? Number.parseFloat(e.target.value) : null })}
                                className="w-full bg-[#2c2c2e] border border-[#3a3a3c] rounded-md px-3 py-2 text-xs text-white focus:outline-none focus:border-[#af52de]"
                            />
                        </div>

                        <div>
                            <label className="text-xs text-[#86868b] block mb-2">Alert Thresholds (%)</label>
                            <div className="flex gap-2">
                                {config.alert_thresholds.map((t, i) => (
                                    <input
                                        key={i}
                                        type="number"
                                        value={t}
                                        onChange={(e) => {
                                            const newThresholds = [...config.alert_thresholds];
                                            newThresholds[i] = Number(e.target.value);
                                            onChange({ alert_thresholds: newThresholds });
                                        }}
                                        className="w-12 bg-[#2c2c2e] border border-[#3a3a3c] rounded px-2 py-1 text-[10px] text-center text-white"
                                    />
                                ))}
                                <button
                                    onClick={() => onChange({ alert_thresholds: [...config.alert_thresholds, 10] })}
                                    className="px-2 py-1 bg-[#3a3a3c] rounded text-[10px] text-white hover:bg-[#4a4a4c]"
                                >
                                    +
                                </button>
                            </div>
                        </div>

                        <div className="pt-4 border-t border-[#3a3a3c]">
                            <div className="flex justify-between items-center mb-3">
                                <label className="text-xs text-[#86868b] block">Provider Budgets</label>
                                <button
                                    onClick={() => {
                                        const newProviders = [...config.provider_budgets, { provider: 'openai', max_cost_usd: 10, period: 'monthly' }];
                                        onChange({ provider_budgets: newProviders as any });
                                    }}
                                    className="text-[10px] text-[#af52de] font-medium hover:underline"
                                >
                                    + Add Provider
                                </button>
                            </div>
                            <div className="space-y-3">
                                {config.provider_budgets.map((pb, i) => (
                                    <div key={i} className="flex gap-2 items-center p-2 bg-[#2c2c2e]/50 border border-[#2c2c2e] rounded-lg">
                                        <select
                                            value={pb.provider}
                                            onChange={(e) => {
                                                const newProviders = [...config.provider_budgets];
                                                newProviders[i] = { ...pb, provider: e.target.value };
                                                onChange({ provider_budgets: newProviders });
                                            }}
                                            className="bg-transparent border-none text-[10px] text-white focus:outline-none w-20"
                                        >
                                            <option value="openai">OpenAI</option>
                                            <option value="anthropic">Anthropic</option>
                                            <option value="google">Google</option>
                                            <option value="local">Local</option>
                                        </select>
                                        <input
                                            type="number"
                                            value={pb.max_cost_usd || ''}
                                            placeholder="Limit"
                                            onChange={(e) => {
                                                const newProviders = [...config.provider_budgets];
                                                newProviders[i] = { ...pb, max_cost_usd: e.target.value ? Number(e.target.value) : null };
                                                onChange({ provider_budgets: newProviders });
                                            }}
                                            className="bg-transparent border-b border-[#3a3a3c] text-[10px] text-white w-12 text-center focus:outline-none"
                                        />
                                        <select
                                            value={pb.period}
                                            onChange={(e) => {
                                                const newProviders = [...config.provider_budgets];
                                                newProviders[i] = { ...pb, period: e.target.value as any };
                                                onChange({ provider_budgets: newProviders });
                                            }}
                                            className="bg-transparent border-none text-[10px] text-[#86868b] focus:outline-none"
                                        >
                                            <option value="daily">Daily</option>
                                            <option value="weekly">Weekly</option>
                                            <option value="monthly">Monthly</option>
                                            <option value="total">Total</option>
                                        </select>
                                        <button
                                            onClick={() => {
                                                const newProviders = config.provider_budgets.filter((_, idx) => idx !== i);
                                                onChange({ provider_budgets: newProviders });
                                            }}
                                            className="ml-auto text-[#ff453a]"
                                        >
                                            <PiggyBank size={14} /> {/* Using PiggyBank as a generic small icon for remove since X isn't in top level easily */}
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

function Toggle({ label, desc, enabled, onToggle }: any) {
    return (
        <div className="flex items-center justify-between">
            <div>
                <div className="text-xs font-medium text-white">{label}</div>
                <div className="text-[10px] text-[#86868b] w-48">{desc}</div>
            </div>
            <button
                onClick={onToggle}
                className={`w-10 h-6 rounded-full relative transition-colors ${enabled ? 'bg-[#32d74b]' : 'bg-[#424245]'}`}
            >
                <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-all shadow-sm ${enabled ? 'left-5' : 'left-1'}`} />
            </button>
        </div>
    )
}
