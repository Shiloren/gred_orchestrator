import { Component, type ErrorInfo, type ReactNode } from 'react';

interface Props {
    children: ReactNode;
}

interface State {
    hasError: boolean;
    error: Error | null;
    errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
    state: State = { hasError: false, error: null, errorInfo: null };

    static getDerivedStateFromError(error: Error): Partial<State> {
        return { hasError: true, error };
    }

    componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        this.setState({ errorInfo });
        console.error('[ErrorBoundary]', error, errorInfo);
    }

    handleReload = () => window.location.reload();

    handleDismiss = () => this.setState({ hasError: false, error: null, errorInfo: null });

    render() {
        if (!this.state.hasError) return this.props.children;

        return (
            <div className="min-h-screen bg-[#1c1c1e] flex items-center justify-center p-6">
                <div className="max-w-xl w-full bg-[#2c2c2e] rounded-2xl border border-[#3a3a3c] p-8 space-y-4">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-red-500/20 flex items-center justify-center">
                            <span className="text-red-400 text-xl">!</span>
                        </div>
                        <h1 className="text-xl font-semibold text-white">Error en la aplicacion</h1>
                    </div>

                    <p className="text-[#86868b] text-sm">
                        Se ha producido un error inesperado. Puedes intentar recargar la pagina o descartar el error.
                    </p>

                    {this.state.error && (
                        <div className="bg-[#1c1c1e] rounded-lg p-4 border border-[#3a3a3c]">
                            <p className="text-red-400 text-sm font-mono break-all">
                                {this.state.error.message}
                            </p>
                        </div>
                    )}

                    {this.state.errorInfo && (
                        <details className="text-xs text-[#636366]">
                            <summary className="cursor-pointer hover:text-[#86868b] transition-colors">
                                Stack trace
                            </summary>
                            <pre className="mt-2 bg-[#1c1c1e] rounded-lg p-3 border border-[#3a3a3c] overflow-auto max-h-48 font-mono text-[10px]">
                                {this.state.errorInfo.componentStack}
                            </pre>
                        </details>
                    )}

                    <div className="flex gap-3 pt-2">
                        <button
                            onClick={this.handleReload}
                            className="px-4 py-2 bg-[#0a84ff] text-white text-sm rounded-lg hover:bg-[#0a84ff]/80 transition-colors"
                        >
                            Recargar
                        </button>
                        <button
                            onClick={this.handleDismiss}
                            className="px-4 py-2 bg-[#3a3a3c] text-white text-sm rounded-lg hover:bg-[#48484a] transition-colors"
                        >
                            Descartar
                        </button>
                    </div>
                </div>
            </div>
        );
    }
}
