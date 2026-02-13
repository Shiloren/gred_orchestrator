import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';

vi.mock('reactflow', () => ({
    default: ({ children }: any) => <div data-testid="react-flow">{children}</div>,
    Background: () => <div data-testid="rf-background" />,
    Controls: () => <div data-testid="rf-controls" />,
    MiniMap: () => <div data-testid="rf-minimap" />,
    Panel: ({ children }: any) => <div data-testid="rf-panel">{children}</div>,
    useNodesState: () => [[], vi.fn(), vi.fn()],
    useEdgesState: () => [[], vi.fn(), vi.fn()],
    MarkerType: { ArrowClosed: 'arrowclosed' },
}));

import { GraphCanvas } from '../GraphCanvas';

describe('GraphCanvas', () => {
    it('renders ReactFlow container', () => {
        render(<GraphCanvas onNodeSelect={vi.fn()} selectedNodeId={null} />);
        expect(screen.getByTestId('react-flow')).toBeInTheDocument();
    });

    it('renders MiniMap', () => {
        render(<GraphCanvas onNodeSelect={vi.fn()} selectedNodeId={null} />);
        expect(screen.getByTestId('rf-minimap')).toBeInTheDocument();
    });

    it('renders panel label', () => {
        render(<GraphCanvas onNodeSelect={vi.fn()} selectedNodeId={null} />);
        expect(screen.getByText('Live Orchestration Graph')).toBeInTheDocument();
    });
});
