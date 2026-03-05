import { render, screen } from '@testing-library/react';
import { act } from 'react';
import { BackgroundRunner } from '../BackgroundRunner';
import { useAppStore } from '../../stores/appStore';
import { describe, it, expect, beforeEach, vi } from 'vitest';

// Mock types since we can't easily import from ../types in this snippet environment
// but the actual execution will have access to them.

describe('BackgroundRunner - Phase 7 QA', () => {
    beforeEach(async () => {
        // Reset store state before each test
        await act(async () => {
            useAppStore.getState().skillRuns = {};
        });
        vi.useFakeTimers();
    });

    it('no muestra nada cuando no hay runs activos', () => {
        const { container } = render(<BackgroundRunner />);
        expect(container.firstChild).toBeNull();
    });

    it('muestra el widget cuando se añade un run al store', async () => {
        await act(async () => {
            useAppStore.getState().updateSkillRun({
                id: 'run_1',
                skill_id: 'skill_1',
                command: '/test',
                status: 'running',
                progress: 0.1,
                message: 'Iniciando...',
                started_at: new Date().toISOString()
            });
        });

        render(<BackgroundRunner />);

        expect(screen.getByText(/Background Skills/i)).toBeTruthy();
        expect(screen.getByText('/test')).toBeTruthy();
        expect(screen.getByText('10%')).toBeTruthy();
        expect(screen.getByText('Iniciando...')).toBeTruthy();
    });

    it('actualiza el progreso en tiempo real', async () => {
        render(<BackgroundRunner />);

        await act(async () => {
            useAppStore.getState().updateSkillRun({
                id: 'run_1',
                skill_id: 'skill_1',
                command: '/test',
                status: 'running',
                progress: 0.1,
                message: 'Iniciando...',
                started_at: new Date().toISOString()
            });
        });

        expect(screen.getByText('10%')).toBeTruthy();

        await act(async () => {
            useAppStore.getState().updateSkillRun({
                id: 'run_1',
                progress: 0.5,
                message: 'Mitad de camino'
            });
        });

        expect(screen.getByText('50%')).toBeTruthy();
        expect(screen.getByText('Mitad de camino')).toBeTruthy();
    });

    it('se auto-elimina después de 5 segundos al completar', async () => {
        render(<BackgroundRunner />);

        await act(async () => {
            useAppStore.getState().updateSkillRun({
                id: 'run_1',
                skill_id: 'skill_1',
                command: '/test',
                status: 'completed',
                progress: 1,
                message: 'Terminado',
                started_at: new Date().toISOString()
            });
        });

        expect(screen.getByText('100%')).toBeTruthy();

        // Advance timers by 5 seconds
        await act(async () => {
            vi.advanceTimersByTime(5000);
        });

        // The run should be gone from the store (and thus the UI)
        expect(Object.keys(useAppStore.getState().skillRuns)).toHaveLength(0);
        expect(screen.queryByText('/test')).toBeNull();
    });

    it('maneja errores visualmente', async () => {
        render(<BackgroundRunner />);

        await act(async () => {
            useAppStore.getState().updateSkillRun({
                id: 'run_fail',
                skill_id: 'skill_1',
                command: '/fail',
                status: 'error',
                progress: 0.4,
                message: 'Algo salió mal',
                started_at: new Date().toISOString()
            });
        });

        expect(screen.getByText('Algo salió mal')).toBeTruthy();
        // Since we don't have CSS matching here, we check if the run is still there 
        // until dismissed (either auto or manual)
        expect(screen.getByText('/fail')).toBeTruthy();
    });
});
