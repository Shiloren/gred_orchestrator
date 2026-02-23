import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Sidebar } from '../Sidebar';

describe('Sidebar', () => {
    it('renders all tab buttons', () => {
        render(<Sidebar activeTab="graph" onTabChange={vi.fn()} />);
        expect(screen.getByTitle('Grafo')).toBeInTheDocument();
        expect(screen.getByTitle('Planes')).toBeInTheDocument();
        expect(screen.getByTitle('Ops')).toBeInTheDocument();
        expect(screen.getByTitle('Ajustes')).toBeInTheDocument();
    });

    it('calls onTabChange when tab clicked', () => {
        const onTabChange = vi.fn();
        render(<Sidebar activeTab="graph" onTabChange={onTabChange} />);
        fireEvent.click(screen.getByTitle('Ops'));
        expect(onTabChange).toHaveBeenCalledWith('operations');
    });

    it('highlights active tab', () => {
        render(<Sidebar activeTab="operations" onTabChange={vi.fn()} />);
        const opsButton = screen.getByTitle('Ops');
        expect(opsButton.className).toContain('text-[#0a84ff]');
    });
});
