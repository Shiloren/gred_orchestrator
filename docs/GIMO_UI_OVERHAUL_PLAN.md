# GIMO UI Overhaul -- Implementation Plan

> **DEPRECATED 2026-02-23** — Superseded by `docs/UI_IMPROVEMENT_PLAN_2026-02-23.md`
> This document reflects the original UI overhaul from Phase 1. Most items here were implemented.
> For current UI improvements, refer to the new plan.

> **GIMO** = Gred In Multi-Agent Orchestrator
> **Status:** DEPRECATED
> **Target:** `tools/orchestrator_ui/src/`
> **Prerequisite:** None (this is Phase 1 of GIMO_ROADMAP.md)

---

## Objective

Transform the current basic 2-column UI into a professional 3-panel architecture (Sidebar + Graph Canvas + Inspect Panel) matching SOTA multi-agent orchestration platforms (LangGraph Studio, Dify.ai, n8n). The UI must be structured to support future fractal orchestration features.

## Target Layout

```
+------+-------------------------------+------------------+
| SIDE |         HEADER BAR (h-12)     |                  |
| BAR  +-------------------------------+   INSPECT PANEL  |
| 56px |                               |   380px wide     |
|      |      GRAPH CANVAS             |   collapsible    |
|      |      (ReactFlow, full-bleed)  |                  |
|      |      + MiniMap                |   Content by tab:|
|      |      + animated edges         |   - Maintenance  |
|      |      + improved nodes         |   - Logs         |
|      |                               |   - Node details |
+------+-------------------------------+------------------+
|              STATUS BAR / FOOTER (h-8)                  |
+---------------------------------------------------------+
```

## Current Issues to Fix

1. **Missing `API_BASE` export** in `src/types.ts` -- all 4 hooks import it but it doesn't exist
2. **App.tsx diverges from tests** -- tests expect semantic HTML, `bg-[#000000]`, "Repo Orchestrator", "Gred In Labs", "v1.0.0", and MaintenanceIsland rendered
3. **MaintenanceIsland not rendered** -- exists with 34 tests but never shown in App
4. **No MiniMap** on graph despite ReactFlow supporting it
5. **Basic node designs** -- no status indicators, no selected state, no hover effects

---

## Implementation Phases

### Phase 1: Foundation (no visual changes, no breakage)

#### 1.1 Fix `src/types.ts`

Add at the top of the file, before the interfaces:

```typescript
export const API_BASE = '';
```

This works because Vite proxies `/ui/*` in dev, and production serves from same origin. All hooks already construct URLs as `` `${API_BASE}/ui/...` ``.

#### 1.2 Update `src/index.css`

Add these blocks after the existing content:

```css
/* ---- Surface hierarchy variables ---- */
:root {
    --surface-0: #000000;
    --surface-1: #0a0a0a;
    --surface-2: #141414;
    --surface-3: #1c1c1e;
    --border-primary: #2c2c2e;
    --border-subtle: #1c1c1e;
    --accent-blue: #0a84ff;
    --accent-green: #32d74b;
    --accent-purple: #5e5ce6;
    --accent-amber: #ff9f0a;
    --text-primary: #f5f5f7;
    --text-secondary: #86868b;
    --text-tertiary: #424245;
}

/* ---- Animated edge flow ---- */
@keyframes edgeFlow {
    from { stroke-dashoffset: 24; }
    to { stroke-dashoffset: 0; }
}

.react-flow__edge-path {
    stroke-dasharray: 5 5;
    animation: edgeFlow 1s linear infinite;
}

/* ---- Glow utilities ---- */
.glow-green {
    box-shadow: 0 0 20px rgba(50, 215, 75, 0.2);
}

.glow-purple {
    box-shadow: 0 0 20px rgba(94, 92, 230, 0.2);
}

/* ---- Skeleton loading ---- */
@keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}

.skeleton {
    background: linear-gradient(90deg, #1c1c1e 25%, #2c2c2e 50%, #1c1c1e 75%);
    background-size: 200% 100%;
    animation: shimmer 1.5s ease-in-out infinite;
    border-radius: 8px;
}

/* ---- ReactFlow overrides ---- */
.react-flow__minimap {
    border-radius: 12px !important;
    overflow: hidden;
}

.react-flow__controls {
    border-radius: 12px !important;
    overflow: hidden;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.5) !important;
}

.react-flow__controls-button {
    background: #141414 !important;
    border-color: #2c2c2e !important;
    fill: #86868b !important;
}

.react-flow__controls-button:hover {
    background: #1c1c1e !important;
    fill: #f5f5f7 !important;
}

.react-flow__node.selected > div {
    outline: none;
}

/* ---- Toast animation ---- */
@keyframes slideInRight {
    from { transform: translateX(100%); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}

.toast-enter {
    animation: slideInRight 0.3s ease-out;
}

/* ---- Status pulse ---- */
@keyframes statusPulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

.status-dot-active {
    animation: statusPulse 2s ease-in-out infinite;
}
```

#### 1.3 Extend `tailwind.config.js`

Add to `theme.extend.colors`:

```js
surface: {
    0: '#000000',
    1: '#0a0a0a',
    2: '#141414',
    3: '#1c1c1e',
},
```

Add to `theme.extend.animation`:

```js
'pulse-slow': 'pulse 3s ease-in-out infinite',
'shimmer': 'shimmer 1.5s ease-in-out infinite',
```

Add to `theme.extend.keyframes`:

```js
shimmer: {
    '0%': { backgroundPosition: '-200% 0' },
    '100%': { backgroundPosition: '200% 0' },
},
```

**Verify:** Run `npm run test:coverage` -- all existing tests must pass unchanged.

---

### Phase 2: New Components (additive only)

#### 2.1 Create `src/components/Sidebar.tsx`

```tsx
import React from 'react';
import { Network, Wrench, ScrollText, Settings } from 'lucide-react';

export type SidebarTab = 'graph' | 'maintenance' | 'logs' | 'settings';

interface SidebarProps {
    activeTab: SidebarTab;
    onTabChange: (tab: SidebarTab) => void;
}

const tabs: { id: SidebarTab; icon: typeof Network; label: string }[] = [
    { id: 'graph', icon: Network, label: 'Graph' },
    { id: 'maintenance', icon: Wrench, label: 'Maintenance' },
    { id: 'logs', icon: ScrollText, label: 'Logs' },
    { id: 'settings', icon: Settings, label: 'Settings' },
];

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, onTabChange }) => {
    return (
        <aside className="w-14 bg-[#000000] border-r border-[#2c2c2e] flex flex-col items-center py-3 gap-1 shrink-0">
            {tabs.map(({ id, icon: Icon, label }) => (
                <button
                    key={id}
                    onClick={() => onTabChange(id)}
                    title={label}
                    className={`
                        w-10 h-10 rounded-xl flex items-center justify-center
                        transition-all duration-200 group relative
                        ${activeTab === id
                            ? 'bg-[#0a84ff]/15 text-[#0a84ff]'
                            : 'text-[#86868b] hover:text-[#f5f5f7] hover:bg-[#1c1c1e]'}
                    `}
                >
                    <Icon size={18} />
                    <span className="absolute left-full ml-2 px-2 py-1 rounded-md bg-[#2c2c2e] text-[10px] text-white font-medium opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap z-50">
                        {label}
                    </span>
                </button>
            ))}
        </aside>
    );
};
```

#### 2.2 Create `src/components/InspectPanel.tsx`

```tsx
import React from 'react';
import { X } from 'lucide-react';
import type { SidebarTab } from './Sidebar';
import { LiveLogs } from './LiveLogs';

interface InspectPanelProps {
    activeTab: SidebarTab;
    selectedNodeId: string | null;
    onClose: () => void;
    children?: React.ReactNode;
}

export const InspectPanel: React.FC<InspectPanelProps> = ({
    activeTab,
    selectedNodeId,
    onClose,
    children,
}) => {
    const getPanelTitle = () => {
        if (selectedNodeId && activeTab === 'graph') return `Node: ${selectedNodeId}`;
        switch (activeTab) {
            case 'graph': return 'Graph Overview';
            case 'maintenance': return 'System Maintenance';
            case 'logs': return 'Audit Logs';
            case 'settings': return 'Settings';
        }
    };

    return (
        <aside className="w-[380px] bg-[#0a0a0a] border-l border-[#2c2c2e] flex flex-col shrink-0 overflow-hidden">
            <div className="h-10 px-4 flex items-center justify-between border-b border-[#1c1c1e] shrink-0">
                <span className="text-xs font-semibold text-[#f5f5f7] truncate">
                    {getPanelTitle()}
                </span>
                <button
                    onClick={onClose}
                    className="w-6 h-6 rounded-md flex items-center justify-center text-[#86868b] hover:text-white hover:bg-[#1c1c1e] transition-all"
                >
                    <X size={14} />
                </button>
            </div>

            <div className="flex-1 overflow-y-auto custom-scrollbar p-4 space-y-4">
                {activeTab === 'maintenance' && children}
                {activeTab === 'logs' && <LiveLogs />}
                {activeTab === 'graph' && !selectedNodeId && (
                    <div className="text-xs text-[#86868b] text-center py-12">
                        Click a node on the canvas to inspect it
                    </div>
                )}
                {activeTab === 'settings' && (
                    <div className="text-xs text-[#86868b] text-center py-12">
                        Settings panel -- coming in Phase 3
                    </div>
                )}
            </div>
        </aside>
    );
};
```

#### 2.3 Create `src/components/GraphCanvas.tsx`

```tsx
import React, { useEffect, useCallback } from 'react';
import ReactFlow, {
    Background,
    Controls,
    MiniMap,
    Panel,
    useNodesState,
    useEdgesState,
    MarkerType,
    NodeMouseHandler,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { BridgeNode } from './BridgeNode';
import { OrchestratorNode } from './OrchestratorNode';
import { RepoNode } from './RepoNode';

const nodeTypes = {
    bridge: BridgeNode,
    orchestrator: OrchestratorNode,
    repo: RepoNode,
};

interface GraphCanvasProps {
    onNodeSelect: (nodeId: string | null) => void;
    selectedNodeId: string | null;
}

export const GraphCanvas: React.FC<GraphCanvasProps> = ({ onNodeSelect, selectedNodeId }) => {
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);

    const fetchGraphData = useCallback(async () => {
        try {
            const response = await fetch('/ui/graph', {
                headers: { 'Authorization': 'demo-token' }
            });
            const data = await response.json();

            const formattedEdges = data.edges.map((e: any) => ({
                ...e,
                animated: true,
                style: {
                    stroke: e.source === 'tunnel' ? '#0a84ff' : '#32d74b',
                    strokeWidth: 2,
                },
                markerEnd: {
                    type: MarkerType.ArrowClosed,
                    color: e.source === 'tunnel' ? '#0a84ff' : '#32d74b',
                },
            }));

            setNodes(data.nodes);
            setEdges(formattedEdges);
        } catch (error) {
            console.error('Error fetching graph data:', error);
        }
    }, [setNodes, setEdges]);

    useEffect(() => {
        fetchGraphData();
        const interval = setInterval(fetchGraphData, 5000);
        return () => clearInterval(interval);
    }, [fetchGraphData]);

    const onNodeClick: NodeMouseHandler = useCallback((_event, node) => {
        onNodeSelect(node.id);
    }, [onNodeSelect]);

    const onPaneClick = useCallback(() => {
        onNodeSelect(null);
    }, [onNodeSelect]);

    return (
        <div className="w-full h-full bg-[#0a0a0a]">
            <ReactFlow
                nodes={nodes.map(n => ({ ...n, selected: n.id === selectedNodeId }))}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                nodeTypes={nodeTypes}
                onNodeClick={onNodeClick}
                onPaneClick={onPaneClick}
                fitView
                proOptions={{ hideAttribution: true }}
            >
                <Background color="#1c1c1e" gap={24} size={1} />
                <Controls showInteractive={false} />
                <MiniMap
                    nodeColor={(node) => {
                        if (node.type === 'orchestrator') return '#0a84ff';
                        if (node.type === 'bridge') return '#0a84ff';
                        if (node.type === 'repo') return '#5e5ce6';
                        return '#86868b';
                    }}
                    maskColor="rgba(0, 0, 0, 0.7)"
                    className="!bg-[#0a0a0a] !border-[#2c2c2e] !rounded-xl"
                    style={{ width: 140, height: 90 }}
                />
                <Panel
                    position="top-left"
                    className="bg-[#141414]/90 backdrop-blur-xl px-3 py-1.5 rounded-lg border border-[#2c2c2e] text-[10px] text-[#86868b] font-mono uppercase tracking-wider"
                >
                    Live Orchestration Graph
                </Panel>
            </ReactFlow>
        </div>
    );
};
```

#### 2.4 Create `src/components/SkeletonLoader.tsx`

```tsx
import React from 'react';

interface SkeletonProps {
    className?: string;
    lines?: number;
}

export const Skeleton: React.FC<SkeletonProps> = ({ className = '', lines = 1 }) => {
    return (
        <div className="space-y-2">
            {Array.from({ length: lines }).map((_, i) => (
                <div
                    key={i}
                    className={`skeleton h-4 ${i === lines - 1 ? 'w-3/4' : 'w-full'} ${className}`}
                />
            ))}
        </div>
    );
};
```

#### 2.5 Create `src/components/Toast.tsx`

```tsx
import React, { createContext, useContext, useState, useCallback } from 'react';

interface Toast {
    id: string;
    message: string;
    type: 'success' | 'error' | 'info';
}

interface ToastContextValue {
    toasts: Toast[];
    addToast: (message: string, type?: Toast['type']) => void;
    removeToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

export const useToast = () => {
    const ctx = useContext(ToastContext);
    if (!ctx) throw new Error('useToast must be used within ToastProvider');
    return ctx;
};

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [toasts, setToasts] = useState<Toast[]>([]);

    const addToast = useCallback((message: string, type: Toast['type'] = 'info') => {
        const id = Date.now().toString();
        setToasts(prev => [...prev, { id, message, type }]);
        setTimeout(() => {
            setToasts(prev => prev.filter(t => t.id !== id));
        }, 4000);
    }, []);

    const removeToast = useCallback((id: string) => {
        setToasts(prev => prev.filter(t => t.id !== id));
    }, []);

    return (
        <ToastContext.Provider value={{ toasts, addToast, removeToast }}>
            {children}
            <div className="fixed bottom-16 right-4 z-[100] space-y-2">
                {toasts.map(toast => (
                    <div
                        key={toast.id}
                        className={`toast-enter px-4 py-2.5 rounded-xl border text-xs font-medium shadow-2xl backdrop-blur-xl cursor-pointer
                            ${toast.type === 'success'
                                ? 'bg-[#32d74b]/10 border-[#32d74b]/20 text-[#32d74b]'
                                : toast.type === 'error'
                                ? 'bg-[#ff3b30]/10 border-[#ff3b30]/20 text-[#ff3b30]'
                                : 'bg-[#0a84ff]/10 border-[#0a84ff]/20 text-[#0a84ff]'
                            }`}
                        onClick={() => removeToast(toast.id)}
                    >
                        {toast.message}
                    </div>
                ))}
            </div>
        </ToastContext.Provider>
    );
};
```

#### 2.6 Create `src/components/__tests__/Sidebar.test.tsx`

```tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Sidebar } from '../Sidebar';

describe('Sidebar', () => {
    it('renders all tab buttons', () => {
        render(<Sidebar activeTab="graph" onTabChange={vi.fn()} />);
        expect(screen.getByTitle('Graph')).toBeInTheDocument();
        expect(screen.getByTitle('Maintenance')).toBeInTheDocument();
        expect(screen.getByTitle('Logs')).toBeInTheDocument();
        expect(screen.getByTitle('Settings')).toBeInTheDocument();
    });

    it('calls onTabChange when tab clicked', () => {
        const onTabChange = vi.fn();
        render(<Sidebar activeTab="graph" onTabChange={onTabChange} />);
        fireEvent.click(screen.getByTitle('Maintenance'));
        expect(onTabChange).toHaveBeenCalledWith('maintenance');
    });

    it('highlights active tab', () => {
        render(<Sidebar activeTab="logs" onTabChange={vi.fn()} />);
        const logsButton = screen.getByTitle('Logs');
        expect(logsButton.className).toContain('text-[#0a84ff]');
    });
});
```

#### 2.7 Create `src/components/__tests__/GraphCanvas.test.tsx`

```tsx
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
```

**Verify:** Run `npm run test:coverage` -- new tests pass, existing tests unchanged.

---

### Phase 3: Node Visual Upgrades

#### 3.1 Replace `src/components/BridgeNode.tsx`

```tsx
import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { Cloud } from 'lucide-react';

export const BridgeNode = memo(({ data, selected }: any) => {
    return (
        <div className={`
            px-4 py-3 rounded-xl bg-[#141414] border-2 transition-all duration-200 min-w-[160px]
            ${selected
                ? 'border-[#0a84ff] shadow-[0_0_20px_rgba(10,132,255,0.3)]'
                : 'border-[#2c2c2e] hover:border-[#38383a]'}
        `}>
            <div className="flex items-center gap-3">
                <div className="relative">
                    <div className="w-9 h-9 rounded-lg bg-[#0a84ff]/15 flex items-center justify-center">
                        <Cloud size={18} className="text-[#0a84ff]" />
                    </div>
                    <div className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-[#32d74b] border-2 border-[#141414] animate-pulse" />
                </div>
                <div>
                    <div className="text-xs font-semibold text-[#f5f5f7]">{data.label}</div>
                    <div className="text-[10px] text-[#86868b] font-mono">{data.status || 'bridge'}</div>
                </div>
            </div>
            <Handle type="source" position={Position.Right} className="!w-2 !h-2 !bg-[#0a84ff] !border-[#141414] !border-2" />
        </div>
    );
});
```

#### 3.2 Replace `src/components/OrchestratorNode.tsx`

```tsx
import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { Cpu } from 'lucide-react';

export const OrchestratorNode = memo(({ data, selected }: any) => {
    return (
        <div className={`
            px-5 py-4 rounded-xl bg-[#141414] border-2 transition-all duration-200 min-w-[180px]
            ${selected
                ? 'border-[#0a84ff] shadow-[0_0_30px_rgba(10,132,255,0.4)]'
                : 'border-[#0a84ff]/40 shadow-[0_0_15px_rgba(10,132,255,0.15)]'}
        `}>
            <div className="flex items-center gap-3">
                <div className="relative">
                    <div className="w-10 h-10 rounded-xl bg-[#0a84ff]/20 flex items-center justify-center ring-1 ring-[#0a84ff]/30">
                        <Cpu size={20} className="text-[#0a84ff]" />
                    </div>
                    <div className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-[#32d74b] border-2 border-[#141414] animate-pulse" />
                </div>
                <div>
                    <div className="text-sm font-semibold text-[#f5f5f7]">{data.label}</div>
                    <div className="text-[10px] text-[#32d74b] uppercase tracking-wider font-bold font-mono">{data.status}</div>
                </div>
            </div>
            <Handle type="target" position={Position.Left} className="!w-2 !h-2 !bg-[#0a84ff] !border-[#141414] !border-2" />
            <Handle type="source" position={Position.Right} className="!w-2 !h-2 !bg-[#32d74b] !border-[#141414] !border-2" />
        </div>
    );
});
```

#### 3.3 Replace `src/components/RepoNode.tsx`

```tsx
import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { FolderGit2 } from 'lucide-react';

export const RepoNode = memo(({ data, selected }: any) => {
    return (
        <div className={`
            px-4 py-3 rounded-xl bg-[#141414] border-2 transition-all duration-200 min-w-[160px]
            ${selected
                ? 'border-[#5e5ce6] shadow-[0_0_20px_rgba(94,92,230,0.3)]'
                : 'border-[#2c2c2e] hover:border-[#5e5ce6]/40'}
        `}>
            <div className="flex items-center gap-3">
                <div className="relative">
                    <div className="w-9 h-9 rounded-lg bg-[#5e5ce6]/15 flex items-center justify-center">
                        <FolderGit2 size={18} className="text-[#5e5ce6]" />
                    </div>
                    <div className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-[#32d74b] border-2 border-[#141414]" />
                </div>
                <div>
                    <div className="text-xs font-semibold text-[#f5f5f7]">{data.label}</div>
                    <div className="text-[10px] text-[#86868b] font-mono truncate max-w-[120px]">{data.path}</div>
                </div>
            </div>
            <Handle type="target" position={Position.Left} className="!w-2 !h-2 !bg-[#5e5ce6] !border-[#141414] !border-2" />
        </div>
    );
});
```

---

### Phase 4: App Rewrite

#### 4.1 Update `src/__tests__/App.test.tsx` FIRST

```tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from '../App';

vi.mock('../components/Sidebar', () => ({
    Sidebar: () => <div data-testid="sidebar">Sidebar Mock</div>
}));

vi.mock('../components/GraphCanvas', () => ({
    GraphCanvas: () => <div data-testid="graph-canvas">GraphCanvas Mock</div>
}));

vi.mock('../components/InspectPanel', () => ({
    InspectPanel: ({ children }: any) => (
        <div data-testid="inspect-panel">{children}</div>
    )
}));

vi.mock('../islands/system/MaintenanceIsland', () => ({
    MaintenanceIsland: () => <div data-testid="maintenance-island">MaintenanceIsland Mock</div>
}));

describe('App', () => {
    it('renders header with title', () => {
        render(<App />);
        expect(screen.getByText('Repo Orchestrator')).toBeInTheDocument();
    });

    it('renders company name', () => {
        render(<App />);
        expect(screen.getByText('Gred In Labs')).toBeInTheDocument();
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
```

#### 4.2 Rewrite `src/App.tsx`

```tsx
import React, { useState, useEffect } from 'react';
import { Sidebar, SidebarTab } from './components/Sidebar';
import { GraphCanvas } from './components/GraphCanvas';
import { InspectPanel } from './components/InspectPanel';
import { MaintenanceIsland } from './islands/system/MaintenanceIsland';
import { Zap } from 'lucide-react';
import { UiStatusResponse } from './types';

export default function App() {
    const [status, setStatus] = useState<UiStatusResponse | null>(null);
    const [activeTab, setActiveTab] = useState<SidebarTab>('graph');
    const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
    const [inspectOpen, setInspectOpen] = useState(true);

    useEffect(() => {
        const fetchStatus = async () => {
            try {
                const response = await fetch('/ui/status', {
                    headers: { 'Authorization': 'demo-token' }
                });
                const data = await response.json();
                setStatus(data);
            } catch (error) {
                console.error('Error fetching status:', error);
            }
        };
        fetchStatus();
        const interval = setInterval(fetchStatus, 5000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="min-h-screen bg-[#000000] text-[#f5f5f7] font-sans selection:bg-[#0a84ff] selection:text-white flex flex-col">
            <header className="h-12 border-b border-[#2c2c2e] bg-[#000000]/80 backdrop-blur-xl flex items-center justify-between px-4 z-50 shrink-0">
                <div className="flex items-center gap-3">
                    <div className="w-7 h-7 bg-[#0a84ff] rounded-lg flex items-center justify-center glow-blue">
                        <Zap size={14} className="text-white" />
                    </div>
                    <span className="font-semibold tracking-tight text-sm">Repo Orchestrator</span>
                    <span className="text-[10px] text-[#86868b] font-mono bg-[#1c1c1e] px-2 py-0.5 rounded-full">Gred In Labs</span>
                </div>
                <div className="flex items-center gap-4 text-xs text-[#86868b]">
                    <div className="flex items-center gap-1.5">
                        <div className="w-1.5 h-1.5 rounded-full bg-[#32d74b] animate-pulse" />
                        <span>{status?.service_status || 'Connecting...'}</span>
                    </div>
                </div>
            </header>

            <div className="flex flex-1 overflow-hidden">
                <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />

                <main className="flex-1 relative overflow-hidden">
                    <GraphCanvas onNodeSelect={setSelectedNodeId} selectedNodeId={selectedNodeId} />
                </main>

                {inspectOpen && (
                    <InspectPanel
                        activeTab={activeTab}
                        selectedNodeId={selectedNodeId}
                        onClose={() => setInspectOpen(false)}
                    >
                        <MaintenanceIsland />
                    </InspectPanel>
                )}
            </div>

            <footer className="h-8 border-t border-[#2c2c2e] bg-[#000000] flex items-center justify-between px-4 text-[10px] text-[#424245] uppercase tracking-widest shrink-0">
                <span>Protected by Gred In Labs</span>
                <div className="flex items-center gap-4">
                    <span className="text-[#86868b]">Uptime: {status ? Math.floor(status.uptime_seconds / 60) : 0}m</span>
                    <span>v{status?.version || '1.0.0'}</span>
                </div>
            </footer>
        </div>
    );
}
```

#### 4.3 Update `src/components/LiveLogs.tsx`

Change the outer div from:
```tsx
<div className="bg-[#000000] border border-[#38383a] rounded-xl overflow-hidden flex flex-col h-[300px] shadow-inner">
```
To:
```tsx
<div className="bg-[#000000] border border-[#38383a] rounded-xl overflow-hidden flex flex-col flex-1 min-h-[200px] shadow-inner">
```

#### 4.4 Update `src/main.tsx`

```tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.tsx';
import { ToastProvider } from './components/Toast.tsx';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
        <ToastProvider>
            <App />
        </ToastProvider>
    </React.StrictMode>,
);
```

---

### Phase 5: Verify

```bash
cd tools/orchestrator_ui
npm run test:coverage   # All tests pass, coverage maintained
npm run build           # Production build succeeds
```

Expected test results:
- 6 App tests pass (updated mocks)
- 34 MaintenanceIsland tests pass (unchanged)
- 3 Sidebar tests pass (new)
- 3 GraphCanvas tests pass (new)
- All hook tests pass (unchanged)
- All Accordion tests pass (unchanged)

---

## Files Summary

| File | Action | Notes |
|------|--------|-------|
| `src/types.ts` | MODIFY | Add `API_BASE` export |
| `src/index.css` | MODIFY | Add CSS variables, animations |
| `tailwind.config.js` | MODIFY | Add surface colors |
| `src/components/Sidebar.tsx` | CREATE | Navigation sidebar |
| `src/components/InspectPanel.tsx` | CREATE | Right panel |
| `src/components/GraphCanvas.tsx` | CREATE | Full-bleed graph |
| `src/components/SkeletonLoader.tsx` | CREATE | Loading skeleton |
| `src/components/Toast.tsx` | CREATE | Toast system |
| `src/components/__tests__/Sidebar.test.tsx` | CREATE | Sidebar tests |
| `src/components/__tests__/GraphCanvas.test.tsx` | CREATE | GraphCanvas tests |
| `src/components/BridgeNode.tsx` | REPLACE | Visual upgrade |
| `src/components/OrchestratorNode.tsx` | REPLACE | Visual upgrade |
| `src/components/RepoNode.tsx` | REPLACE | Visual upgrade |
| `src/App.tsx` | REPLACE | 3-panel layout |
| `src/__tests__/App.test.tsx` | REPLACE | Updated mocks |
| `src/components/LiveLogs.tsx` | MODIFY | Flex height |
| `src/main.tsx` | MODIFY | ToastProvider |
| `src/components/GraphView.tsx` | KEEP | Deprecated, not deleted |
| `src/islands/system/MaintenanceIsland.tsx` | KEEP | No changes |
| `src/components/Accordion.tsx` | KEEP | No changes |
| All hooks | KEEP | No changes |
| All hook tests | KEEP | No changes |
