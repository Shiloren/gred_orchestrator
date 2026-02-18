import React from 'react';
import { TrustRecord } from '../../hooks/useSecurityService';
import { ShieldAlert } from 'lucide-react';

interface TrustDashboardProps {
    records: TrustRecord[];
}

const getScoreBarColorClass = (score: number) => {
    if (score >= 0.9) return 'bg-[#32d74b]';
    if (score >= 0.7) return 'bg-[#32d74b] opacity-80';
    if (score >= 0.5) return 'bg-[#ff9f0a]';
    return 'bg-[#ff453a]';
};

const getScoreTextColorClass = (score: number) => {
    if (score >= 0.9) return 'text-[#32d74b]';
    if (score >= 0.7) return 'text-[#32d74b]';
    if (score >= 0.5) return 'text-[#ff9f0a]';
    return 'text-[#ff453a]';
};

const getPolicyBadgeClass = (policy: string) => {
    switch (policy) {
        case 'auto_approve': return 'bg-[#32d74b]/10 text-[#32d74b] border border-[#32d74b]/20';
        case 'require_review': return 'bg-[#ff9f0a]/10 text-[#ff9f0a] border border-[#ff9f0a]/20';
        case 'blocked': return 'bg-[#ff453a]/10 text-[#ff453a] border border-[#ff453a]/20';
        default: return 'bg-gray-500/10 text-gray-500 border-gray-500/20';
    }
};

const getPolicyLabel = (policy: string) => {
    return policy.replace('_', ' ').toUpperCase();
};

export const TrustDashboard: React.FC<TrustDashboardProps> = ({ records }) => {
    return (
        <div className="bg-[#141414] rounded-xl border border-[#1c1c1e] overflow-hidden">
            <div className="overflow-x-auto">
                <table className="w-full text-left">
                    <thead>
                        <tr className="border-b border-[#1c1c1e] bg-[#0a0a0a]">
                            <th className="px-4 py-3 text-[10px] uppercase tracking-widest text-[#86868b] font-semibold">Dimension</th>
                            <th className="px-4 py-3 text-[10px] uppercase tracking-widest text-[#86868b] font-semibold">Trust Score</th>
                            <th className="px-4 py-3 text-[10px] uppercase tracking-widest text-[#86868b] font-semibold text-right">Approve</th>
                            <th className="px-4 py-3 text-[10px] uppercase tracking-widest text-[#86868b] font-semibold text-right">Reject</th>
                            <th className="px-4 py-3 text-[10px] uppercase tracking-widest text-[#86868b] font-semibold text-right">Fail</th>
                            <th className="px-4 py-3 text-[10px] uppercase tracking-widest text-[#86868b] font-semibold text-right">Policy</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-[#1c1c1e]">
                        {records.length === 0 ? (
                            <tr>
                                <td colSpan={6} className="px-4 py-8 text-center text-[#86868b] text-xs">
                                    <ShieldAlert size={16} className="mx-auto mb-2 opacity-50" />
                                    No trust records found.
                                </td>
                            </tr>
                        ) : (
                            records.map((record) => (
                                <tr key={record.dimension_key} className="hover:bg-[#1c1c1e]/50 transition-colors">
                                    <td className="px-4 py-3 text-xs font-mono text-[#f5f5f7] max-w-[150px] truncate" title={record.dimension_key}>
                                        {record.dimension_key}
                                    </td>
                                    <td className="px-4 py-3">
                                        <div className="flex items-center gap-2">
                                            <div className="flex-1 h-1.5 bg-[#2c2c2e] rounded-full overflow-hidden min-w-[60px]">
                                                <div
                                                    className={`h-full rounded-full transition-all duration-500 ${getScoreBarColorClass(record.score)}`}
                                                    style={{ width: `${record.score * 100}%` }}
                                                />
                                            </div>
                                            <span className={`text-xs font-mono w-8 text-right ${getScoreTextColorClass(record.score)}`}>
                                                {Math.round(record.score * 100)}%
                                            </span>
                                        </div>
                                    </td>
                                    <td className="px-4 py-3 text-xs text-[#86868b] text-right">{record.approvals}</td>
                                    <td className="px-4 py-3 text-xs text-[#86868b] text-right">{record.rejections}</td>
                                    <td className="px-4 py-3 text-xs text-right">
                                        {record.failures > 0 ? (
                                            <span className="text-[#ff453a] font-medium">{record.failures}</span>
                                        ) : (
                                            <span className="text-[#86868b]">-</span>
                                        )}
                                    </td>
                                    <td className="px-4 py-3 text-right">
                                        <span className={`
                                            inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider
                                            ${getPolicyBadgeClass(record.policy)}
                                        `}>
                                            {getPolicyLabel(record.policy)}
                                        </span>
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
