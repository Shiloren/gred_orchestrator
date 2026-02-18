import { ShieldCheck, ShieldAlert, Shield } from 'lucide-react';

interface ConfidenceScore {
    score: number;
    percentage?: string;
    level?: string;
    reason?: string;
    analysis?: string;
    questions?: string[];
    risk_level?: string;
    type?: string;
}

interface ConfidenceMeterProps {
    readonly data: ConfidenceScore | null;
}

const GetIcon = ({ score }: { readonly score: number }) => {
    if (score >= 0.8) return <ShieldCheck size={12} />;
    if (score <= 0.3) return <ShieldAlert size={12} />;
    return <Shield size={12} />;
};

const RiskBadge = ({ risk }: { risk: string }) => {
    let style = 'text-[#86868b] border-[#2c2c2e]';
    if (risk === 'high') style = 'text-[#ff453a] border-[#ff453a]/30 bg-[#ff453a]/10';
    if (risk === 'medium') style = 'text-[#ffd60a] border-[#ffd60a]/30 bg-[#ffd60a]/10';

    return (
        <div className={`text-[9px] px-1.5 py-0.5 rounded border ${style}`}>
            RIESGO {risk.toUpperCase()}
        </div>
    );
};

export function ConfidenceMeter({ data }: ConfidenceMeterProps) {
    if (!data) return null;

    const getLevel = (score: number) => {
        if (score >= 0.9) return 'High';
        if (score >= 0.7) return 'Strong';
        if (score >= 0.5) return 'Moderate';
        if (score >= 0.3) return 'Low';
        return 'Critical';
    };

    const level = data.level ?? getLevel(data.score);
    const percentage = data.percentage ?? `${Math.round(data.score * 100)}%`;
    const reason = data.reason ?? data.analysis ?? 'Sin análisis disponible';
    const isProactive = data.type === 'proactive';

    const getColor = (lvl: string) => {
        switch (lvl) {
            case 'High': return 'text-[#32d74b] bg-[#32d74b]/10 border-[#32d74b]/20';
            case 'Strong': return 'text-[#0a84ff] bg-[#0a84ff]/10 border-[#0a84ff]/20';
            case 'Moderate': return 'text-[#ffd60a] bg-[#ffd60a]/10 border-[#ffd60a]/20';
            case 'Low': return 'text-[#ff9f0a] bg-[#ff9f0a]/10 border-[#ff9f0a]/20';
            case 'Critical': return 'text-[#ff453a] bg-[#ff453a]/10 border-[#ff453a]/20';
            default: return 'text-[#86868b] bg-[#1c1c1e] border-[#2c2c2e]';
        }
    };

    return (
        <div className={`flex items-center gap-2 px-2 py-1 rounded-full border text-[10px] font-medium ${getColor(level)} group relative cursor-help w-fit animate-in zoom-in-50 duration-300`}>
            <GetIcon score={data.score} />
            <span>{percentage} {isProactive ? 'Proyectado' : 'Confianza'}</span>

            {/* Tooltip */}
            <div className="absolute bottom-full left-0 mb-2 w-64 bg-[#1c1c1e]/95 backdrop-blur-xl border border-[#2c2c2e] p-3 rounded-xl shadow-2xl opacity-0 group-hover:opacity-100 transition-all duration-200 pointer-events-none z-[100] translate-y-1 group-hover:translate-y-0">
                <div className="flex items-center justify-between mb-2">
                    <div className="text-[10px] text-[#86868b] uppercase tracking-wider font-semibold">
                        {isProactive ? 'Autoevaluación Proactiva' : 'Análisis Histórico'}
                    </div>
                    {data.risk_level && (
                        <RiskBadge risk={data.risk_level} />
                    )}
                </div>

                <div className="text-[11px] leading-relaxed text-[#f5f5f7] mb-2">{reason}</div>

                {data.questions && data.questions.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-[#2c2c2e] space-y-1">
                        <div className="text-[9px] text-[#86868b] uppercase font-bold">Dudas del Agente:</div>
                        {data.questions.map((q) => (
                            <div key={q} className="text-[10px] text-[#0a84ff] flex gap-1.5">
                                <span className="opacity-50">•</span>
                                <span>{q}</span>
                            </div>
                        ))}
                    </div>
                )}

                <div className="mt-2.5 pt-2 border-t border-[#2c2c2e] flex justify-between items-center">
                    <span className="text-[9px] text-[#86868b] uppercase font-bold tracking-tight">Status</span>
                    <span className="text-[10px] font-mono">{level} ({percentage})</span>
                </div>
            </div>
        </div>
    );
}
