import React from 'react';

interface Props extends React.PropsWithChildren {
    visualState?: 'idle' | 'verifying' | 'success' | 'error';
    style?: React.CSSProperties;
}

export const LoginGlassCard: React.FC<Props> = ({ children, visualState = 'idle', style }) => {
    const stateClass =
        visualState === 'verifying'
            ? 'border-accent-primary/60 shadow-[0_24px_80px_var(--glow-primary)]'
            : visualState === 'success'
                ? 'border-accent-trust/60 shadow-[0_24px_80px_var(--glow-trust)]'
                : visualState === 'error'
                    ? 'border-accent-alert/55 shadow-[0_24px_80px_var(--glow-alert)]'
                    : 'border-border-primary shadow-2xl';

    return (
        <div
            style={style}
            className={`relative z-10 w-full max-w-lg rounded-2xl border bg-surface-2/60 backdrop-blur-lg p-6 sm:p-8 transition-all duration-300 ${stateClass}`}
        >
            <div
                className={`pointer-events-none absolute inset-0 rounded-2xl transition-opacity duration-300 ${visualState === 'verifying'
                    ? 'opacity-100 bg-[radial-gradient(circle_at_20%_0%,var(--glow-primary),transparent_45%)]'
                    : visualState === 'success'
                        ? 'opacity-100 bg-[radial-gradient(circle_at_20%_0%,var(--glow-trust),transparent_45%)]'
                        : visualState === 'error'
                            ? 'opacity-100 bg-[radial-gradient(circle_at_20%_0%,var(--glow-alert),transparent_45%)]'
                            : 'opacity-0'
                    }`}
            />
            {children}
        </div>
    );
};
