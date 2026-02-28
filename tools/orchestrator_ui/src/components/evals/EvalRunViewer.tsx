import React, { useEffect, useState } from 'react';
import { CheckCircle2, XCircle, ChevronLeft, ChevronDown, ChevronRight, Clock } from 'lucide-react';
import { useEvalsService } from '../../hooks/useEvalsService';
import { EvalRunDetail, EvalCaseResult } from '../../types';

interface EvalRunViewerProps {
    runId: number;
    onBack: () => void;
}

export const EvalRunViewer: React.FC<EvalRunViewerProps> = ({ runId, onBack }) => {
    const { getRunDetail } = useEvalsService();
    const [detail, setDetail] = useState<EvalRunDetail | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [expandedCase, setExpandedCase] = useState<number | null>(null);

    useEffect(() => {
        const load = async () => {
            try {
                const data = await getRunDetail(runId);
                setDetail(data);
            } catch (err) {
                setError('Failed to load run details');
            } finally {
                setLoading(false);
            }
        };
        load();
    }, [runId]);

    if (loading) return <div className="p-8 text-center text-text-secondary">Cargando detalles...</div>;
    if (error || !detail) return <div className="p-8 text-center text-red-500">{error || 'Run not found'}</div>;

    const { report } = detail;
    const safeDetails = Array.isArray(report?.details) ? report.details : [];

    const renderStateValue = (state: Record<string, any>) => {
        if (state?.prompt) return state.prompt;
        if (state?.content) return state.content;
        return typeof state === 'string' ? state : JSON.stringify(state, null, 2);
    };

    return (
        <div className="h-full flex flex-col bg-surface-0">
            {/* Header */}
            <div className="flex items-center gap-4 p-4 border-b border-surface-2">
                <button
                    onClick={onBack}
                    className="p-2 hover:bg-surface-2 rounded-lg text-text-secondary transition-colors"
                >
                    <ChevronLeft size={20} />
                </button>
                <div>
                    <h2 className="text-lg font-semibold text-text-primary">Evaluation Run #{runId}</h2>
                    <div className="flex items-center gap-2 text-xs text-text-secondary">
                        <Clock size={12} />
                        <span>{new Date(detail.created_at).toLocaleString()}</span>
                        <span>•</span>
                        <span className="font-mono">{detail.workflow_id}</span>
                    </div>
                </div>
                <div className="ml-auto flex gap-4">
                    <div className="flex flex-col items-end">
                        <span className="text-[10px] uppercase text-text-secondary font-bold">Pass Rate</span>
                        <span className={`font-mono font-bold ${report.pass_rate >= 1.0 ? 'text-accent-trust' : 'text-accent-warning'}`}>
                            {(report.pass_rate * 100).toFixed(1)}%
                        </span>
                    </div>
                    <div className="flex flex-col items-end">
                        <span className="text-[10px] uppercase text-text-secondary font-bold">Gate</span>
                        <span className={`font-bold ${report.gate_passed ? 'text-accent-trust' : 'text-accent-alert'}`}>
                            {report.gate_passed ? 'PASSED' : 'FAILED'}
                        </span>
                    </div>
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto custom-scrollbar p-6">
                <div className="space-y-4">
                    {safeDetails.map((result: EvalCaseResult, idx: number) => {
                        return (
                            <div key={idx} className="bg-surface-1 border border-surface-2 rounded-lg overflow-hidden">
                                <button
                                    onClick={() => setExpandedCase(expandedCase === idx ? null : idx)}
                                    className="w-full flex items-center gap-4 p-4 hover:bg-surface-2 transition-colors text-left"
                                >
                                    {result.passed ? (
                                        <CheckCircle2 className="text-accent-trust shrink-0" size={20} />
                                    ) : (
                                        <XCircle className="text-accent-alert shrink-0" size={20} />
                                    )}
                                    <div className="flex-1 min-w-0">
                                        <div className="text-sm font-medium text-text-primary truncate font-mono">
                                            {/* Display ID or formatted input */}
                                            {result.case_id || renderStateValue(result.input_state || {}).substring(0, 100)}
                                        </div>
                                        <div className="text-xs text-text-secondary mt-1">
                                            Score: {result.score.toFixed(2)}
                                        </div>
                                    </div>
                                    {expandedCase === idx ? <ChevronDown size={16} className="text-text-secondary" /> : <ChevronRight size={16} className="text-text-secondary" />}
                                </button>

                                {expandedCase === idx && (
                                    <div className="border-t border-surface-2 p-4 bg-surface-0/20 space-y-4">
                                        {/* Expected vs Actual Grid */}
                                        <div className="grid grid-cols-2 gap-4">
                                            <div>
                                                <div className="text-[10px] uppercase text-text-secondary font-bold mb-2">Expected State</div>
                                                <pre className="text-xs font-mono text-text-primary bg-surface-0 p-3 rounded border border-surface-2 overflow-x-auto whitespace-pre-wrap h-full">
                                                    {renderStateValue(result.expected_state)}
                                                </pre>
                                            </div>
                                            <div>
                                                <div className="text-[10px] uppercase text-text-secondary font-bold mb-2">Actual State</div>
                                                <pre className="text-xs font-mono text-text-primary bg-surface-2 p-3 rounded border border-border-primary overflow-x-auto whitespace-pre-wrap h-full">
                                                    {renderStateValue(result.actual_state)}
                                                </pre>
                                            </div>
                                        </div>

                                        {/* Reason if failed */}
                                        {!result.passed && result.reason && (
                                            <div className="bg-accent-alert/10 border border-accent-alert/20 p-3 rounded">
                                                <div className="text-[10px] uppercase text-accent-alert font-bold mb-1">Failure Reason</div>
                                                <p className="text-xs text-accent-alert">{result.reason}</p>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        )
                    })}
                    {safeDetails.length === 0 && (
                        <div className="text-text-secondary text-sm p-4 bg-surface-1 border border-surface-2 rounded-lg">
                            This run has no detailed cases to display.
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
