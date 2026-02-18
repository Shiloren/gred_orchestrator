import { describe, it, expect, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { CommandPalette } from '../CommandPalette';

describe('CommandPalette', () => {
    it('dispara acción mcp_sync cuando se selecciona comando MCP', () => {
        const onAction = vi.fn();

        render(
            <CommandPalette
                isOpen
                onClose={vi.fn()}
                onAction={onAction}
            />
        );

        fireEvent.click(screen.getByRole('button', { name: /sincronizar mcp tools/i }));

        expect(onAction).toHaveBeenCalledWith('mcp_sync');
    });
});
