import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ProviderSettings } from '../ProviderSettings';

// Mock useProviders hook
vi.mock('../../hooks/useProviders', () => ({
    useProviders: () => ({
        providers: [
            {
                id: 'p1',
                type: 'ollama',
                name: 'Ollama (Local)',
                enabled: true,
                is_local: true,
                max_concurrent: 4,
                cost_per_1k_tokens: 0,
                max_context: 4096,
                models: ['qwen2.5-coder:7b', 'llama3.2:3b'],
            },
            {
                id: 'p2',
                type: 'groq',
                name: 'Groq Cloud',
                enabled: true,
                is_local: false,
                max_concurrent: 2,
                cost_per_1k_tokens: 0,
                max_context: 32768,
                models: ['llama-3.3-70b-versatile'],
                api_key: 'gsk_****',
            },
        ],
        nodes: [
            {
                id: 'node-a',
                name: 'The Handheld',
                role: 'Mobile Edge Node',
                max_concurrent_agents: 2,
                current_agents: 1,
                preferred_models: [],
                provider_ids: [],
                constraints: {},
            },
        ],
        loading: false,
        error: null,
        addProvider: vi.fn(),
        removeProvider: vi.fn(),
        testProvider: vi.fn(),
        refresh: vi.fn(),
    }),
}));

describe('ProviderSettings', () => {
    it('renders provider list', () => {
        render(<ProviderSettings />);
        expect(screen.getByText('Ollama (Local)')).toBeInTheDocument();
        expect(screen.getByText('Groq Cloud')).toBeInTheDocument();
    });

    it('renders header with connect button', () => {
        render(<ProviderSettings />);
        expect(screen.getByText('AI Providers')).toBeInTheDocument();
        expect(screen.getByText('Connect')).toBeInTheDocument();
    });

    it('shows local/cloud labels', () => {
        render(<ProviderSettings />);
        expect(screen.getAllByText(/Local/)[0]).toBeInTheDocument();
        expect(screen.getAllByText(/Cloud/)[0]).toBeInTheDocument();
    });

    it('shows model tags', () => {
        render(<ProviderSettings />);
        expect(screen.getByText('qwen2.5-coder:7b')).toBeInTheDocument();
        expect(screen.getByText('llama-3.3-70b-versatile')).toBeInTheDocument();
    });

    it('renders compute nodes section', () => {
        render(<ProviderSettings />);
        expect(screen.getByText('Compute Nodes')).toBeInTheDocument();
        expect(screen.getByText('The Handheld')).toBeInTheDocument();
        expect(screen.getByText('1/2')).toBeInTheDocument();
    });

    it('shows add form when connect is clicked', () => {
        render(<ProviderSettings />);
        fireEvent.click(screen.getByText('Connect'));
        expect(screen.getByText('Connect Provider')).toBeInTheDocument();
        expect(screen.getByPlaceholderText('Display name (optional)')).toBeInTheDocument();
    });

    it('shows test button for each provider', () => {
        render(<ProviderSettings />);
        const testButtons = screen.getAllByText('Test');
        expect(testButtons.length).toBe(2);
    });
});
