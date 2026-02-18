import React from 'react';
import { TrustRecord } from '../../hooks/useSecurityService';
import { Activity, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';

interface CircuitBreakerPanelProps {
    records: TrustRecord[];
    onInspect: (dimensionKey: string) => void;
}

export const CircuitBreakerPanel: React.FC<CircuitBreakerPanelProps> = ({ records, onInspect }) => {
    const activeBreakers = records.filter(r => r.circuit_state !== 'closed' || r.failures > 0);

    const getStatusColor = (state: string, failures: number) => {
        if (state === 'open') return 'text-red-500';
        if (state === 'half_open') return 'text-yellow-500';
        if (failures > 0) return 'text-orange-400';
        return 'text-green-500';
    };

    return (
        <div className="bg-[#141414] rounded-xl border border-[#1c1c1e] overflow-hidden">
            <div className="overflow-x-auto">
                <table className="w-full text-left">
                    <thead>
                        <tr className="border-b border-[#1c1c1e] bg-[#0a0a0a]">
                            <th className="px-4 py-3 text-[10px] uppercase tracking-widest text-[#86868b] font-semibold">Dimension</th>
                            <th className="px-4 py-3 text-[10px] uppercase tracking-widest text-[#86868b] font-semibold">State</th>
                            <th className="px-4 py-3 text-[10px] uppercase tracking-widest text-[#86868b] font-semibold text-right">Score</th>
                            <th className="px-4 py-3 text-[10px] uppercase tracking-widest text-[#86868b] font-semibold text-right">Failures</th>
                            <th className="px-4 py-3 text-[10px] uppercase tracking-widest text-[#86868b] font-semibold text-right">Action</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-[#1c1c1e]">
                        {activeBreakers.length === 0 ? (
                            <tr>
                                <td colSpan={5} className="px-4 py-8 text-center text-[#86868b] text-xs">
                                    <CheckCircle size={16} className="mx-auto mb-2 text-[#32d74b] opacity-50" />
                                    All circuits nominal. No active failures detected.
                                </td>
                            </tr>
                        ) : (
                            activeBreakers.map((record) => (
                                <tr key={record.dimension_key} className="hover:bg-[#1c1c1e]/50 transition-colors">
                                    <td className="px-4 py-3 text-xs font-mono text-[#f5f5f7]">
                                        {record.dimension_key}
                                    </td>
                                    <td className="px-4 py-3 text-xs">
                                        <div className={`flex items-center gap-1.5 font-medium ${getStatusColor(record.circuit_state, record.failures)}`}>
                                            {record.circuit_state === 'open' ? <XCircle size={12} /> :
                                                record.circuit_state === 'half_open' ? <AlertTriangle size={12} /> : // Note: original code used 'half_open', new code uses 'half-open'
                                                    <Activity size={12} />}
                                            <span className="capitalize">{record.circuit_state}</span>
                                        </div>
                                    </td>
                                    <td className="px-4 py-3 text-xs text-[#f5f5f7] text-right">
                                        {(record.score * 100).toFixed(1)}%
                                    </td>
                                    <td className="px-4 py-3 text-xs text-[#f5f5f7] text-right">
                                        {record.failures}
                                    </td>
                                    <td className="px-4 py-3 text-right">
                                        <button
                                            onClick={() => onInspect(record.dimension_key)}
                                            className="text-[#0a84ff] hover:text-[#32d74b] text-xs font-medium transition-colors"
                                        >
                                            Inspect
                                        </button>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};
