import { describe, it, expect, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { MenuBar } from '../MenuBar';

describe('MenuBar', () => {
    it('ejecuta MCP Sync desde el menú Tools', () => {
        const onMcpSync = vi.fn();

        render(
            <MenuBar
                onNewPlan={vi.fn()}
                onSelectView={vi.fn()}
                onSelectSettingsView={vi.fn()}
                onRefreshSession={vi.fn()}
                onOpenCommandPalette={vi.fn()}
                onMcpSync={onMcpSync}
            />
        );

        fireEvent.click(screen.getByRole('button', { name: /tools/i }));
        fireEvent.click(screen.getByRole('button', { name: 'MCP Sync' }));

        expect(onMcpSync).toHaveBeenCalledTimes(1);
    });
});
