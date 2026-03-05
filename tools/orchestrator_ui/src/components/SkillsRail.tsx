import React, { useCallback, useEffect, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { X } from 'lucide-react';
import { useAppStore } from '../stores/appStore';
import { SkillsContent } from './SkillsContent';

/**
 * SkillsRail — A small "SKILLS" button that lives on the edges of the screen.
 * The user can drag it along any edge (like WoW addon buttons).
 * Clicking it opens a dropdown popup with the skills list.
 */

interface ButtonPos {
    edge: 'top' | 'bottom' | 'left' | 'right';
    offset: number; // % along the edge (0-100)
}

const BUTTON_SIZE = { w: 72, h: 28 };
const POPUP_W = 360;
const POPUP_H = 420;

function loadPosition(): ButtonPos {
    try {
        const saved = localStorage.getItem('gimo_skills_btn_pos');
        if (saved) {
            const parsed = JSON.parse(saved);
            if (parsed && parsed.edge && typeof parsed.offset === 'number') return parsed;
        }
    } catch { /* ignore */ }
    return { edge: 'top', offset: 70 }; // default: top edge, 70% along
}

function savePosition(pos: ButtonPos) {
    localStorage.setItem('gimo_skills_btn_pos', JSON.stringify(pos));
}

function getAbsolutePos(pos: ButtonPos): { x: number; y: number } {
    const vw = globalThis.innerWidth;
    const vh = globalThis.innerHeight;

    switch (pos.edge) {
        case 'top':
            return { x: (pos.offset / 100) * (vw - BUTTON_SIZE.w), y: 0 };
        case 'bottom':
            return { x: (pos.offset / 100) * (vw - BUTTON_SIZE.w), y: vh - BUTTON_SIZE.h };
        case 'left':
            return { x: 0, y: (pos.offset / 100) * (vh - BUTTON_SIZE.h) };
        case 'right':
            return { x: vw - BUTTON_SIZE.w, y: (pos.offset / 100) * (vh - BUTTON_SIZE.h) };
    }
}

function screenToEdgePos(clientX: number, clientY: number): ButtonPos {
    const vw = globalThis.innerWidth;
    const vh = globalThis.innerHeight;

    // Find which edge is closest
    const distTop = clientY;
    const distBottom = vh - clientY;
    const distLeft = clientX;
    const distRight = vw - clientX;
    const min = Math.min(distTop, distBottom, distLeft, distRight);

    if (min === distTop) {
        return { edge: 'top', offset: Math.max(0, Math.min(100, (clientX / (vw - BUTTON_SIZE.w)) * 100)) };
    }
    if (min === distBottom) {
        return { edge: 'bottom', offset: Math.max(0, Math.min(100, (clientX / (vw - BUTTON_SIZE.w)) * 100)) };
    }
    if (min === distLeft) {
        return { edge: 'left', offset: Math.max(0, Math.min(100, (clientY / (vh - BUTTON_SIZE.h)) * 100)) };
    }
    return { edge: 'right', offset: Math.max(0, Math.min(100, (clientY / (vh - BUTTON_SIZE.h)) * 100)) };
}

export const SkillsRail: React.FC = () => {
    const isOpen = useAppStore((s) => s.isSkillsDropdownOpen);
    const toggleOpen = useAppStore((s) => s.toggleSkillsDropdown);
    const skillRuns = useAppStore((s) => s.skillRuns);

    const [pos, setPos] = useState<ButtonPos>(loadPosition);
    const [isDragging, setIsDragging] = useState(false);
    const [dragPreview, setDragPreview] = useState<{ x: number; y: number } | null>(null);
    const didDragRef = useRef(false);
    const startRef = useRef<{ x: number; y: number; t: number } | null>(null);

    const hasActiveRuns = skillRuns && Object.keys(skillRuns).length > 0;

    // Recalculate position on resize
    useEffect(() => {
        const handle = () => setPos((p) => ({ ...p })); // force re-render
        globalThis.addEventListener('resize', handle);
        return () => globalThis.removeEventListener('resize', handle);
    }, []);

    /* ── Drag logic ── */
    const handlePointerDown = useCallback((e: React.PointerEvent) => {
        e.preventDefault();
        (e.target as HTMLElement).setPointerCapture(e.pointerId);
        startRef.current = { x: e.clientX, y: e.clientY, t: Date.now() };
        didDragRef.current = false;
        setIsDragging(true);
    }, []);

    useEffect(() => {
        if (!isDragging) return;

        const onMove = (e: PointerEvent) => {
            if (startRef.current) {
                const dx = e.clientX - startRef.current.x;
                const dy = e.clientY - startRef.current.y;
                if (Math.abs(dx) > 4 || Math.abs(dy) > 4) {
                    didDragRef.current = true;
                }
            }
            setDragPreview({ x: e.clientX, y: e.clientY });
        };

        const onUp = (e: PointerEvent) => {
            setIsDragging(false);
            setDragPreview(null);

            if (didDragRef.current) {
                const newPos = screenToEdgePos(e.clientX, e.clientY);
                setPos(newPos);
                savePosition(newPos);
            }
            startRef.current = null;
        };

        globalThis.addEventListener('pointermove', onMove);
        globalThis.addEventListener('pointerup', onUp);
        return () => {
            globalThis.removeEventListener('pointermove', onMove);
            globalThis.removeEventListener('pointerup', onUp);
        };
    }, [isDragging]);

    const handleClick = useCallback(() => {
        if (!didDragRef.current) {
            toggleOpen();
        }
    }, [toggleOpen]);

    const absPos = dragPreview
        ? screenToEdgePos(dragPreview.x, dragPreview.y)
        : pos;
    const { x, y } = dragPreview
        ? { x: dragPreview.x - BUTTON_SIZE.w / 2, y: dragPreview.y - BUTTON_SIZE.h / 2 }
        : getAbsolutePos(absPos);

    const isVertical = pos.edge === 'left' || pos.edge === 'right';

    /* ── Popup position (opens away from edge) ── */
    const getPopupStyle = (): React.CSSProperties => {
        const btnAbs = getAbsolutePos(pos);
        const vw = globalThis.innerWidth;
        const vh = globalThis.innerHeight;

        let px = btnAbs.x;
        let py = btnAbs.y;

        switch (pos.edge) {
            case 'top':
                py = BUTTON_SIZE.h + 6;
                px = Math.min(Math.max(8, btnAbs.x), vw - POPUP_W - 8);
                break;
            case 'bottom':
                py = vh - BUTTON_SIZE.h - POPUP_H - 6;
                px = Math.min(Math.max(8, btnAbs.x), vw - POPUP_W - 8);
                break;
            case 'left':
                px = BUTTON_SIZE.w + 6;
                py = Math.min(Math.max(8, btnAbs.y), vh - POPUP_H - 8);
                break;
            case 'right':
                px = vw - BUTTON_SIZE.w - POPUP_W - 6;
                py = Math.min(Math.max(8, btnAbs.y), vh - POPUP_H - 8);
                break;
        }

        return { left: px, top: py, width: POPUP_W, height: POPUP_H };
    };

    return (
        <>
            {/* ── The draggable SKILLS button ── */}
            <div
                className="fixed z-[160]"
                style={{
                    left: x,
                    top: y,
                    width: BUTTON_SIZE.w,
                    height: BUTTON_SIZE.h,
                    transition: isDragging ? 'none' : 'left 0.25s ease, top 0.25s ease',
                }}
            >
                <button
                    onPointerDown={handlePointerDown}
                    onClick={handleClick}
                    className={`
                        w-full h-full rounded-lg border text-[10px] font-black uppercase tracking-widest
                        select-none touch-none transition-all duration-200
                        ${isOpen
                            ? 'bg-violet-500/25 border-violet-400/50 text-violet-300 shadow-lg shadow-violet-500/20'
                            : 'bg-surface-1/90 border-white/10 text-text-secondary hover:text-text-primary hover:border-white/20 hover:bg-surface-2/90'
                        }
                        ${isDragging ? 'cursor-grabbing scale-110 opacity-80' : 'cursor-grab'}
                        ${isVertical ? 'writing-mode-vertical' : ''}
                    `}
                    aria-label="Abrir Skills"
                >
                    SKILLS
                    {hasActiveRuns && (
                        <span className="absolute top-0.5 right-0.5 w-2 h-2 rounded-full bg-violet-500 border border-surface-0 animate-pulse" />
                    )}
                </button>
            </div>

            {/* ── The dropdown popup ── */}
            <AnimatePresence>
                {isOpen && !isDragging && (
                    <>
                        {/* Backdrop (click to close) */}
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            transition={{ duration: 0.15 }}
                            className="fixed inset-0 z-[159]"
                            onClick={() => toggleOpen(false)}
                        />

                        {/* Popup */}
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.95 }}
                            transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                            className="fixed z-[161] flex flex-col bg-surface-1/95 backdrop-blur-xl border border-white/10 rounded-2xl overflow-hidden shadow-2xl shadow-black/50"
                            style={getPopupStyle()}
                        >
                            {/* Popup header */}
                            <div className="flex items-center justify-between px-4 py-2.5 bg-white/[0.03] border-b border-white/[0.06]">
                                <span className="text-[11px] font-bold text-text-primary uppercase tracking-wider">
                                    GIMO Skills
                                </span>
                                <button
                                    onClick={() => toggleOpen(false)}
                                    className="p-1 rounded-md text-text-tertiary hover:text-text-primary hover:bg-white/[0.06] transition-colors"
                                >
                                    <X size={14} />
                                </button>
                            </div>

                            {/* Skills content */}
                            <div className="flex-1 overflow-hidden flex flex-col p-3 min-h-0">
                                <SkillsContent compact={true} />
                            </div>
                        </motion.div>
                    </>
                )}
            </AnimatePresence>
        </>
    );
};
