import React, { useState } from 'react';
import { useSystemService } from '../../hooks/useSystemService';
import { useAuditLog } from '../../hooks/useAuditLog';
import { useSecurityService } from '../../hooks/useSecurityService';
import { useRepoService } from '../../hooks/useRepoService';
import {
    Activity,
    RefreshCcw,
    Square,
    FileText,
    Search,
    Filter,
    ChevronDown,
    Terminal,
    AlertCircle,
    ShieldCheck,
    Download,
    FlaskConical,
    ShieldAlert,
    Database
} from 'lucide-react';
import { Accordion } from '../../components/Accordion';

interface MaintenanceIslandProps {
    token?: string;
}

export const MaintenanceIsland: React.FC<MaintenanceIslandProps> = ({ token }) => {
    const { status, isLoading: isServiceLoading, restart, stop, error: serviceError } = useSystemService(token);
    const {
        logs,
        rawLogs,
        filter,
        setFilter,
        searchTerm,
        setSearchTerm,
        refresh: refreshLogs
    } = useAuditLog(token);
    const { panicMode, events, clearPanic, isLoading: isSecurityLoading } = useSecurityService(token);
    const { repos, activeRepo, vitaminize, selectRepo, isLoading: isRepoLoading } = useRepoService(token);

    const [selectedRepoPath, setSelectedRepoPath] = useState<string>('');

    const getStatusColor = () => {
        if (panicMode) return 'text-red-500 bg-red-500/10 border-red-500/40 animate-pulse';
        switch (status) {
            case 'RUNNING': return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
            case 'STOPPED': return 'text-red-400 bg-red-500/10 border-red-500/20';
            case 'STARTING':
            case 'STOPPING': return 'text-amber-400 bg-amber-500/10 border-amber-500/20 animate-pulse';
            default: return 'text-slate-400 bg-slate-500/10 border-slate-500/20';
        }
    };

    const getLogClass = (log: string): string => {
        if (log.includes('DENIED')) return 'text-red-400 bg-red-400/5 px-2 rounded';
        if (log.includes('READ')) return 'text-blue-400';
        if (log.includes('SYSTEM')) return 'text-amber-400';
        return 'text-slate-400';
    };

    const handleExport = () => {
        if (rawLogs.length === 0) return;
        const blob = new Blob([rawLogs.join('\n')], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `gred_audit_${new Date().toISOString().replaceAll(/[:.]/g, '-')}.log`;
        link.click();
        URL.revokeObjectURL(url);
    };

    return (
        <div className="flex flex-col space-y-4 animate-fade-in">
            {/* Panic Mode Banner */}
            {panicMode && (
                <div className="p-4 rounded-2xl bg-red-600/20 border border-red-500/50 flex flex-col space-y-3 shadow-2xl overflow-hidden relative">
                    <div className="absolute top-0 right-0 p-2 opacity-10">
                        <ShieldAlert className="w-12 h-12" />
                    </div>
                    <div className="flex items-center space-x-3">
                        <ShieldAlert className="w-6 h-6 text-red-500" />
                        <div>
                            <p className="text-xs font-black uppercase tracking-widest text-red-400">Security Lockdown</p>
                            <p className="text-sm font-bold text-white">System in Panic Mode</p>
                        </div>
                    </div>
                    <button
                        onClick={clearPanic}
                        disabled={isSecurityLoading}
                        className="w-full py-3 bg-red-500 hover:bg-red-400 text-white text-xs font-black uppercase tracking-widest rounded-xl transition-all shadow-lg active:scale-95"
                    >
                        {isSecurityLoading ? 'Processing...' : 'Deactivate Lockdown'}
                    </button>
                    {events.length > 0 && (
                        <div className="space-y-1.5 max-h-32 overflow-y-auto custom-scrollbar">
                            {events.map((ev) => (
                                <div key={`event-${ev.timestamp}`} className="text-xs font-mono text-red-300 bg-red-900/20 p-2 rounded-lg border border-red-500/10">
                                    <span className="opacity-60">{ev.timestamp}</span> | {ev.reason}
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}

            {/* Service Status Card */}
            <div className={`p-4 rounded-2xl border ${getStatusColor()} flex items-center justify-between shadow-xl backdrop-blur-md`}>
                <div className="flex items-center space-x-3">
                    <div className="p-2.5 rounded-xl bg-black/20">
                        <Activity className="w-5 h-5" />
                    </div>
                    <div>
                        <p className="text-xs uppercase font-black tracking-widest opacity-60">System Core</p>
                        <p className="text-sm font-bold">{panicMode ? 'LOCKDOWN' : status}</p>
                    </div>
                </div>
                <div className="flex space-x-3">
                    <button
                        onClick={restart}
                        disabled={isServiceLoading || panicMode}
                        className="p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-all group disabled:opacity-30"
                        title="Restart Service"
                    >
                        <RefreshCcw className={`w-4 h-4 ${isServiceLoading ? 'animate-spin' : 'group-hover:rotate-180 transition-transform duration-500'}`} />
                    </button>
                    <button
                        onClick={stop}
                        disabled={isServiceLoading || status === 'STOPPED' || panicMode}
                        className="p-3 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-500 transition-all disabled:opacity-30"
                        title="Stop Service"
                    >
                        <Square className="w-4 h-4 fill-current" />
                    </button>
                </div>
            </div>

            {serviceError && (
                <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center space-x-2 text-xs text-red-400">
                    <AlertCircle className="w-4 h-4" />
                    <span>{serviceError}</span>
                </div>
            )}

            {/* Repository Maintenance Accordion */}
            <Accordion title="Repository Control">
                <div className="space-y-3">
                    <div className="flex flex-col space-y-2">
                        <label htmlFor="repo-select" className="text-xs font-black uppercase tracking-widest text-slate-500">Target Repository</label>
                        <div className="relative group">
                            <select
                                id="repo-select"
                                value={selectedRepoPath}
                                onChange={(e) => setSelectedRepoPath(e.target.value)}
                                className="w-full pl-10 pr-4 py-3 bg-black/40 border border-white/5 rounded-xl text-sm text-slate-300 focus:border-accent-primary/50 outline-none transition-all appearance-none cursor-pointer"
                            >
                                <option value="">Select a repository...</option>
                                {repos.map((repo) => (
                                    <option key={repo.path} value={repo.path}>{repo.name}</option>
                                ))}
                            </select>
                            <Database className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 pointer-events-none" />
                        </div>
                    </div>

                    <div className="flex space-x-3">
                        <button
                            onClick={() => selectRepo(selectedRepoPath)}
                            disabled={!selectedRepoPath || isRepoLoading || selectedRepoPath === activeRepo}
                            className="flex-1 py-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-xs font-black uppercase tracking-widest text-white transition-all disabled:opacity-20"
                        >
                            Activate
                        </button>
                        <button
                            onClick={() => vitaminize(selectedRepoPath)}
                            disabled={!selectedRepoPath || isRepoLoading}
                            className="flex-1 py-3 bg-accent-primary/20 hover:bg-accent-primary/30 border border-accent-primary/30 rounded-xl text-xs font-black uppercase tracking-widest text-accent-primary transition-all disabled:opacity-20 flex items-center justify-center space-x-2"
                        >
                            <FlaskConical className="w-4 h-4" />
                            <span>Vitaminize</span>
                        </button>
                    </div>

                    {activeRepo && (
                        <div className="pt-3 flex items-center justify-between border-t border-white/5">
                            <span className="text-xs font-black text-slate-600 uppercase tracking-widest">Active:</span>
                            <span className="text-xs font-mono text-emerald-400 truncate max-w-[200px]" title={activeRepo}>{activeRepo.split(/[/\\]/).pop()}</span>
                        </div>
                    )}
                </div>
            </Accordion>

            {/* Audit Logs Section */}
            <Accordion title="Audit Logs" defaultOpen={true}>
                <div className="space-y-3">
                    {/* Log Controls */}
                    <div className="flex items-center space-x-3">
                        <div className="relative flex-1">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                            <input
                                type="text"
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                placeholder="Filter logs..."
                                className="w-full pl-10 pr-4 py-3 bg-black/40 border border-white/5 rounded-xl text-sm text-slate-300 focus:border-accent-primary/50 outline-none transition-all placeholder:text-slate-600"
                            />
                        </div>
                        <div className="relative group">
                            <select
                                value={filter}
                                onChange={(e) => setFilter(e.target.value as 'all' | 'read' | 'deny' | 'system')}
                                className="appearance-none pl-10 pr-10 py-3 bg-black/40 border border-white/5 rounded-xl text-sm text-slate-300 focus:border-accent-primary/50 outline-none transition-all cursor-pointer"
                            >
                                <option value="all">All</option>
                                <option value="read">Read</option>
                                <option value="deny">Deny</option>
                                <option value="system">System</option>
                            </select>
                            <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 pointer-events-none" />
                            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 pointer-events-none" />
                        </div>
                    </div>

                    {/* Log Terminal View */}
                    <div className="bg-black/60 rounded-2xl border border-white/5 overflow-hidden shadow-inner">
                        <div className="flex items-center justify-between px-5 py-3 bg-white/5 border-b border-white/5">
                            <div className="flex items-center space-x-2">
                                <Terminal className="w-4 h-4 text-emerald-400" />
                                <span className="text-xs font-black uppercase tracking-widest text-slate-500">Live Audit Stream</span>
                            </div>
                            <div className="flex items-center space-x-3">
                                <button
                                    onClick={handleExport}
                                    className="p-1.5 hover:bg-white/5 rounded-md transition-all group"
                                    title="Export Logs"
                                >
                                    <Download className="w-3.5 h-3.5 text-slate-500 group-hover:text-white transition-colors" />
                                </button>
                                <button
                                    onClick={refreshLogs}
                                    className="p-1.5 hover:bg-white/5 rounded-md transition-all group"
                                    title="Refresh"
                                >
                                    <RefreshCcw className="w-3.5 h-3.5 text-slate-500 group-hover:text-white transition-colors" />
                                </button>
                            </div>
                        </div>
                        <div className="h-64 overflow-y-auto p-5 space-y-2 custom-scrollbar font-mono text-xs">
                            {logs.length === 0 ? (
                                <div className="h-full flex flex-col items-center justify-center opacity-20 py-12">
                                    <FileText className="w-10 h-10 mb-2" />
                                    <p className="text-sm">No matches found</p>
                                </div>
                            ) : (
                                logs.map((log, i) => (
                                    <div key={`log-${logs.length - i}`} className="flex space-x-3 group">
                                        <span className="text-slate-600 shrink-0 select-none">[{logs.length - i}]</span>
                                        <span className={`break-all ${getLogClass(log)}`}>
                                            {log}
                                        </span>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </div>
            </Accordion>

            {/* Quick Security Badge */}
            <div className="pt-4">
                <div className={`p-4 bg-gradient-to-r ${panicMode ? 'from-red-500/20' : 'from-accent-primary/10'} to-transparent rounded-2xl border ${panicMode ? 'border-red-500/20' : 'border-accent-primary/10'} flex items-center justify-between`}>
                    <div className="flex items-center space-x-3">
                        <ShieldCheck className={`w-5 h-5 ${panicMode ? 'text-red-500' : 'text-accent-primary'}`} />
                        <span className="text-xs font-bold text-slate-400">{panicMode ? 'System Locked' : 'Vault Integrity Active'}</span>
                    </div>
                    <span className={`text-xs font-black ${panicMode ? 'text-red-500 bg-red-500/20' : 'text-accent-primary bg-accent-primary/20'} px-3 py-1 rounded-full uppercase tracking-tighter`}>
                        {panicMode ? 'Critical' : 'Hardened'}
                    </span>
                </div>
            </div>
        </div>
    );
};
