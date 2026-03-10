import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, beforeEach, it, expect, vi } from 'vitest';
import { ChatTerminalLayout } from '../ChatTerminalLayout';

vi.mock('../OrchestratorChat', () => ({
    OrchestratorChat: ({ onViewInFlow }: any) => (
        <div data-testid="mock-chat">
            <button onClick={() => onViewInFlow?.('agent-1')}>
                view-in-flow
            </button>
        </div>
    ),
}));

vi.mock('../OpsTerminal', () => ({
    OpsTerminal: () => <div data-testid="mock-terminal">terminal-content</div>,
}));

vi.mock('../OpsFlow', () => ({
    OpsFlow: ({ agentId }: any) => <div data-testid="mock-flow">flow:{agentId ?? 'none'}</div>,
}));

// Mock fetch for ops config
beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ ui_show_ids_events: true }),
    }));
});

describe('ChatTerminalLayout', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('muestra tabs por defecto y renderiza chat inicialmente', () => {
        render(<ChatTerminalLayout />);

        expect(screen.getByText('Chat')).toBeTruthy();
        expect(screen.getByText('Terminal')).toBeTruthy();
        expect(screen.getByTestId('mock-chat')).toBeTruthy();
    });

    it('cambia a terminal con click', () => {
        render(<ChatTerminalLayout />);

        fireEvent.click(screen.getByText('Terminal'));

        expect(screen.getByTestId('mock-terminal')).toBeTruthy();
    });

    it('abre vista dividida con botón split', async () => {
        render(<ChatTerminalLayout />);

        const splitBtn = screen.getByTitle(/Vista dividida/i);
        fireEvent.click(splitBtn);

        await waitFor(() => {
            expect(screen.getAllByTestId('mock-chat').length).toBeGreaterThan(0);
            expect(screen.getAllByTestId('mock-terminal').length).toBeGreaterThan(0);
        });
    });

    it('cambia tab activo al hacer click en Terminal y luego Chat', () => {
        render(<ChatTerminalLayout />);

        fireEvent.click(screen.getByText('Terminal'));
        expect(screen.getByTestId('mock-terminal')).toBeTruthy();

        fireEvent.click(screen.getByText('Chat'));
        expect(screen.getByTestId('mock-chat')).toBeTruthy();
    });

    it('muestra secondary tab opuesto en split mode', async () => {
        render(<ChatTerminalLayout />);

        // Active tab is chat, so split shows terminal
        const splitBtn = screen.getByTitle(/Vista dividida/i);
        fireEvent.click(splitBtn);

        await waitFor(() => {
            expect(screen.getByText('Terminal (Vista Dividida)')).toBeTruthy();
        });
    });
});
