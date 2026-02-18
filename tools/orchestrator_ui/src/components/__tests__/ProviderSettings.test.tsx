import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ProviderSettings } from '../ProviderSettings';

const loadProvidersMock = vi.fn();
const loadCatalogMock = vi.fn().mockResolvedValue({});
const installModelMock = vi.fn().mockResolvedValue({ status: 'queued', message: 'Install queued' });
const getInstallJobMock = vi.fn().mockResolvedValue({ status: 'done', message: 'ok', progress: 1, job_id: 'job-1' });
const validateProviderMock = vi.fn().mockResolvedValue({ valid: true, health: 'ok', warnings: [] });
const saveActiveProviderMock = vi.fn().mockResolvedValue({});
const removeProviderMock = vi.fn();
const testProviderMock = vi.fn();
const addToastMock = vi.fn();

// Mock useProviders hook
vi.mock('../../hooks/useProviders', () => ({
    useProviders: () => ({
        providerCapabilities: {
            openai: { auth_modes_supported: ['api_key'], requires_remote_api: true },
            ollama_local: { auth_modes_supported: ['none'], requires_remote_api: false },
        },
        effectiveState: {
            active: 'p1',
            model_id: 'qwen2.5-coder:7b',
        },
        catalogs: {
            openai: {
                provider_type: 'openai',
                installed_models: [{ id: 'gpt-4o-mini', label: 'gpt-4o-mini', installed: true, downloadable: false }],
                available_models: [{ id: 'gpt-4.1-mini', label: 'gpt-4.1-mini', installed: false, downloadable: false }],
                recommended_models: [{ id: 'gpt-4o-mini', label: 'gpt-4o-mini', installed: true, downloadable: false }],
                can_install: false,
                install_method: 'manual',
                auth_modes_supported: ['api_key'],
                warnings: [],
            },
        },
        catalogLoading: {},
        providers: [
            {
                id: 'p1',
                type: 'ollama_local',
                is_local: true,
                model: 'qwen2.5-coder:7b',
                config: { model: 'qwen2.5-coder:7b' },
                capabilities: { auth_modes_supported: ['none'] },
            },
            {
                id: 'p2',
                type: 'groq',
                is_local: false,
                model: 'llama-3.3-70b-versatile',
                config: { model: 'llama-3.3-70b-versatile' },
                capabilities: { auth_modes_supported: ['api_key'] },
            },
        ],
        nodes: {
            'node-a': {
                id: 'node-a',
                name: 'The Handheld',
                type: 'edge',
                max_concurrency: 2,
                current_load: 1,
            },
        },
        loading: false,
        loadProviders: loadProvidersMock,
        loadCatalog: loadCatalogMock,
        installModel: installModelMock,
        getInstallJob: getInstallJobMock,
        validateProvider: validateProviderMock,
        saveActiveProvider: saveActiveProviderMock,
        removeProvider: removeProviderMock,
        testProvider: testProviderMock,
    }),
}));

vi.mock('../Toast', () => ({
    useToast: () => ({ addToast: addToastMock }),
}));

const renderWithToast = () =>
    render(<ProviderSettings />);

describe('ProviderSettings', () => {
    it('loads providers on mount', () => {
        renderWithToast();
        expect(loadProvidersMock).toHaveBeenCalled();
    });

    it('renders provider list', () => {
        renderWithToast();
        expect(screen.getByText('p1')).toBeInTheDocument();
        expect(screen.getByText('p2')).toBeInTheDocument();
    });

    it('renders provider settings actions', () => {
        renderWithToast();
        expect(screen.getByText('Provider Settings')).toBeInTheDocument();
        expect(screen.getByText('Test connection')).toBeInTheDocument();
        expect(screen.getByText('Save as active provider')).toBeInTheDocument();
    });

    it('shows local/cloud labels in active providers', () => {
        renderWithToast();
        expect(screen.getAllByText(/Local/)[0]).toBeInTheDocument();
        expect(screen.getAllByText(/Cloud/)[0]).toBeInTheDocument();
    });

    it('shows model labels', () => {
        renderWithToast();
        expect(screen.getByText('qwen2.5-coder:7b')).toBeInTheDocument();
        expect(screen.getByText('llama-3.3-70b-versatile')).toBeInTheDocument();
    });

    it('renders compute nodes section', () => {
        renderWithToast();
        expect(screen.getByText('The Handheld')).toBeInTheDocument();
        expect(screen.getByText(/Load: 1 \/ 2 agents/)).toBeInTheDocument();
    });

    it('calls validate on test connection', () => {
        renderWithToast();
        fireEvent.click(screen.getByText('Test connection'));
        expect(validateProviderMock).toHaveBeenCalled();
    });

    it('calls save active provider', () => {
        renderWithToast();
        fireEvent.click(screen.getByText('Save as active provider'));
        expect(saveActiveProviderMock).toHaveBeenCalled();
    });
});
