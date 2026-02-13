import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import AgentChat from '../AgentChat';
import { useAgentComms } from '../../hooks/useAgentComms';

// Mock the hook
vi.mock('../../hooks/useAgentComms');

describe('AgentChat', () => {
    const mockSendMessage = vi.fn();
    const mockRefresh = vi.fn();

    beforeEach(() => {
        vi.clearAllMocks();
        (useAgentComms as any).mockReturnValue({
            messages: [],
            loading: false,
            error: null,
            sendMessage: mockSendMessage,
            refresh: mockRefresh,
        });
    });

    it('renders empty state initially', () => {
        render(<AgentChat agentId="test-agent" />);
        expect(screen.getByText('Agent Communication')).toBeInTheDocument();
        expect(screen.getByText('No messages yet.')).toBeInTheDocument();
    });

    it('displays messages', () => {
        (useAgentComms as any).mockReturnValue({
            messages: [
                { id: '1', from: 'agent', content: 'Hello user', timestamp: new Date().toISOString() },
                { id: '2', from: 'orchestrator', content: 'Hello agent', timestamp: new Date().toISOString() },
            ],
            loading: false,
            error: null,
            sendMessage: mockSendMessage,
            refresh: mockRefresh,
        });

        render(<AgentChat agentId="test-agent" />);
        expect(screen.getByText('Hello user')).toBeInTheDocument();
        expect(screen.getByText('Hello agent')).toBeInTheDocument();
    });

    it('handles sending a message', async () => {
        render(<AgentChat agentId="test-agent" />);

        const input = screen.getByPlaceholderText('Send instruction as orchestrator...');
        fireEvent.change(input, { target: { value: 'New instruction' } });

        const button = screen.getByText('Send');
        fireEvent.click(button);

        await waitFor(() => {
            expect(mockSendMessage).toHaveBeenCalledWith('New instruction', 'instruction');
        });
    });

    it('disables send button when input is empty or loading', () => {
        (useAgentComms as any).mockReturnValue({
            messages: [],
            loading: true,
            error: null,
            sendMessage: mockSendMessage,
            refresh: mockRefresh,
        });

        render(<AgentChat agentId="test-agent" />);
        const button = screen.getByText('...');
        expect(button).toBeDisabled();
    });
});
