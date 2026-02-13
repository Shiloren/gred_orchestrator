import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from '../App';

// Mock Sidebar
vi.mock('../components/Sidebar', () => ({
    Sidebar: () => <div data-testid="sidebar">Sidebar Mock</div>
}));

// Mock GraphCanvas
vi.mock('../components/GraphCanvas', () => ({
    GraphCanvas: () => <div data-testid="graph-canvas">GraphCanvas Mock</div>
}));

// Mock InspectPanel
vi.mock('../components/InspectPanel', () => ({
    InspectPanel: ({ children }: any) => (
        <div data-testid="inspect-panel">{children}</div>
    )
}));

// Mock MaintenanceIsland
vi.mock('../islands/system/MaintenanceIsland', () => ({
    MaintenanceIsland: () => <div data-testid="maintenance-island">MaintenanceIsland Mock</div>
}));

// Mock ResizeObserver
globalThis.ResizeObserver = class ResizeObserver {
    observe() { }
    unobserve() { }
    disconnect() { }
};

describe('App', () => {
    it('renders header with title', () => {
        render(<App />);
        expect(screen.getByText('Repo Orchestrator')).toBeInTheDocument();
    });

    it('renders company name', () => {
        render(<App />);
        expect(screen.getAllByText('Gred In Labs')[0]).toBeInTheDocument();
    });

    it('renders footer with version', () => {
        render(<App />);
        expect(screen.getByText(/v1\.0\.0/)).toBeInTheDocument();
    });

    it('renders MaintenanceIsland component', () => {
        render(<App />);
        expect(screen.getByTestId('maintenance-island')).toBeInTheDocument();
    });

    it('has correct structure with header, main, and footer', () => {
        render(<App />);
        expect(screen.getByRole('banner')).toBeInTheDocument();
        expect(screen.getByRole('main')).toBeInTheDocument();
        expect(screen.getByRole('contentinfo')).toBeInTheDocument();
    });

    it('applies dark mode classes', () => {
        const { container } = render(<App />);
        const rootDiv = container.firstChild as HTMLElement;
        expect(rootDiv).toHaveClass('min-h-screen');
        expect(rootDiv).toHaveClass('bg-[#000000]');
    });
});
