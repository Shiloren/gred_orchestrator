import React from 'react';
import { AlertTriangle, CheckCircle, Info } from 'lucide-react';
import { QualityMetrics, DegradationFlag } from '../types';

interface QualityAlertPanelProps {
    quality?: QualityMetrics;
}

export const QualityAlertPanel: React.FC<QualityAlertPanelProps> = ({ quality }) => {
    if (!quality) {
        return (
            <div className="p-8 text-center">
                <Info size={32} className="mx-auto text-surface-3 mb-3" />
                <div className="text-sm text-text-secondary">Sin métricas de calidad disponibles para este nodo.</div>
            </div>
        );
    }

    const { score, alerts, lastCheck } = quality;

    const getAlertLabel = (flag: DegradationFlag) => {
        switch (flag) {
            case 'repetition': return 'Repetición detectada';
            case 'coherence': return 'Alerta de coherencia';
            case 'relevance': return 'Irrelevancia de tarea';
            case 'latency': return 'Latencia alta';
            default: return 'Problema desconocido';
        }
    };

    const getAlertSeverityColor = (score: number) => {
        if (score >= 80) return 'text-accent-trust';
        if (score >= 50) return 'text-accent-warning';
        return 'text-accent-alert';
    };

    const getAlertBarColor = (score: number) => {
        if (score >= 80) return 'bg-accent-trust';
        if (score >= 50) return 'bg-accent-warning';
        return 'bg-accent-alert';
    };

    return (
        <div className="p-4 space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <div className="text-[10px] text-text-secondary uppercase tracking-widest font-bold mb-1">Calidad de Razonamiento</div>
                    <div className={`text-3xl font-bold ${getAlertSeverityColor(score)}`}>
                        {score}%
                    </div>
                </div>
                <div className="text-right">
                    <div className="text-[10px] text-text-secondary uppercase tracking-widest font-bold mb-1">Último Análisis</div>
                    <div className="text-xs text-text-primary font-mono">
                        {new Date(lastCheck).toLocaleTimeString()}
                    </div>
                </div>
            </div>

            {/* Quality Progress Bar */}
            <div className="w-full h-1.5 bg-surface-2 rounded-full overflow-hidden">
                <div
                    className={`h-full transition-all duration-1000 ${getAlertBarColor(score)}`}
                    style={{ width: `${score}%` }}
                />
            </div>

            {/* Alerts Section */}
            <div className="space-y-3">
                <div className="text-[10px] text-text-secondary uppercase tracking-widest font-bold">Estado de Salud</div>

                {alerts.length === 0 ? (
                    <div className="flex items-center gap-3 p-3 rounded-lg bg-accent-trust/10 border border-accent-trust/20">
                        <CheckCircle size={16} className="text-accent-trust" />
                        <div className="text-xs text-accent-trust">Todas las métricas dentro del rango nominal.</div>
                    </div>
                ) : (
                    alerts.map((alert) => (
                        <div key={alert} className="flex items-center gap-3 p-3 rounded-lg bg-accent-alert/10 border border-accent-alert/20">
                            <AlertTriangle size={16} className="text-accent-alert" />
                            <div className="text-xs text-accent-alert">
                                <span className="font-bold">{getAlertLabel(alert)}</span>: Automated detection triggered.
                            </div>
                        </div>
                    ))
                )}
            </div>

            {/* System Info */}
            <div className="p-3 rounded-lg bg-surface-2 border border-border-primary">
                <div className="text-[10px] text-text-secondary uppercase tracking-widest font-bold mb-2">GICS Context</div>
                <div className="text-xs text-text-secondary leading-relaxed">
                    Reasoning quality is evaluated using GICS (Gred In-Context Scoring).
                    The model monitors for entropy spikes, semantic repetition, and plan divergence.
                </div>
            </div>
        </div>
    );
};
