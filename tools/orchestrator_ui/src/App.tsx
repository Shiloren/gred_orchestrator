import { useState, useEffect } from 'react';
import { WorkflowCanvasWrapper } from './components/Graph/WorkflowCanvas';
import { CommandPalette } from './components/Shell/CommandPalette';
import { useOpsService } from './hooks/useOpsService';
import { Node, Edge } from '@xyflow/react';
import { Activity, Command, GitBranch, Terminal } from 'lucide-react';
import clsx from 'clsx';
import { GenericNodeData } from './components/Graph/GenericNode';

const mockPlan = {
    tasks: [
        { id: 't-1', title: 'Analyze User Request', description: 'Parse intent and identify required changes.', status: 'done', depends: [] },
        { id: 't-2', title: 'Draft Implementation Plan', description: 'Create a step-by-step plan for the requested feature.', status: 'done', depends: ['t-1'] },
        { id: 't-3', title: 'Generate Component Code', description: 'Write the React components for the new UI.', status: 'running', depends: ['t-2'], meta: { duration_ms: 12000 } },
        { id: 't-4', title: 'Dependency Check', description: 'Ensure all imports are valid.', status: 'pending', depends: ['t-3'] },
        { id: 't-5', title: 'Run Verification Tests', description: 'Execute unit tests to confirm stability.', status: 'pending', depends: ['t-4'] }
    ]
};

// Convert Ops Plan/Tasks to Graph Nodes
const transformToGraph = (plan: any, _runs: any[]) => {
    if (!plan) return { nodes: [], edges: [] };

    const nodes: Node<GenericNodeData>[] = plan.tasks.map((task: any) => {
        let status = task.status;
        if (status === 'in_progress') status = 'running';

        return {
            id: task.id,
            type: 'generic',
            position: { x: 0, y: 0 },
            data: {
                label: task.title,
                description: task.description,
                status: status,
                type: 'AGENT_TASK',
                meta: task.meta
            }
        };
    });

    const edges: Edge[] = [];
    plan.tasks.forEach((task: any) => {
        task.depends.forEach((depId: string) => {
            edges.push({
                id: `${depId}->${task.id}`,
                source: depId,
                target: task.id,
                animated: true,
                style: { stroke: '#ffffff20', strokeWidth: 2 }
            });
        });
    });

    return { nodes, edges };
};

export default function App() {
    const token = import.meta.env.VITE_ORCH_TOKEN;
    const { plan, runs, isLoading } = useOpsService(token);
    const [isCmdOpen, setIsCmdOpen] = useState(false);
    const [graphData, setGraphData] = useState<{ nodes: Node<GenericNodeData>[], edges: Edge[] }>({ nodes: [], edges: [] });

    // Keyboard Shortcuts
    useEffect(() => {
        const down = (e: KeyboardEvent) => {
            if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
                e.preventDefault();
                setIsCmdOpen((open) => !open);
            }
        };
        document.addEventListener('keydown', down);
        return () => document.removeEventListener('keydown', down);
    }, []);

    // Sync Data (or Load Mock)
    useEffect(() => {
        if (plan) {
            const data = transformToGraph(plan, runs);
            setGraphData(data);
        } else if (!isLoading) {
            // Load Mock Data if no plan is found (Demo Mode)
            const data = transformToGraph(mockPlan, []);
            setGraphData(data);
        }
    }, [plan, runs, isLoading]);

    return (
        <div className="h-screen w-screen bg-zinc-950 text-zinc-100 overflow-hidden relative flex">

            {/* 1. Sidebar (Mini) */}
            <div className="w-16 h-full border-r border-white/5 bg-zinc-950 flex flex-col items-center py-6 space-y-6 z-20">
                <div className="p-3 bg-blue-600 rounded-xl shadow-lg shadow-blue-900/20">
                    <Activity className="w-5 h-5 text-white" />
                </div>

                <div className="flex-1 w-full flex flex-col items-center space-y-4">
                    <NavIcon icon={<GitBranch className="w-5 h-5" />} label="Plan" active />
                    <NavIcon icon={<Terminal className="w-5 h-5" />} label="Logs" />
                </div>

                <div className="mt-auto">
                    <NavIcon icon={<Command className="w-5 h-5" />} label="Cmd" onClick={() => setIsCmdOpen(true)} />
                </div>
            </div>

            {/* 2. Main Canvas */}
            <div className="flex-1 relative">
                {isLoading && !plan ? (
                    <div className="absolute inset-0 flex items-center justify-center bg-zinc-950 z-10 flex-col space-y-4">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
                        <div className="text-zinc-500 text-xs tracking-widest uppercase">Connecting to GIMO Plexus...</div>
                    </div>
                ) : (
                    <WorkflowCanvasWrapper data={graphData} />
                )}

                {/* Floating Top Bar (Context) */}
                <div className="absolute top-6 left-6 right-6 pointer-events-none flex justify-center z-10">
                    <button
                        onClick={() => setIsCmdOpen(true)}
                        className="pointer-events-auto bg-zinc-900/80 backdrop-blur-md border border-white/10 px-4 py-2 rounded-full shadow-2xl flex items-center space-x-3 text-sm text-zinc-400 hover:border-white/20 hover:text-zinc-200 transition-all group"
                    >
                        <SearchIcon className="w-4 h-4" />
                        <span>Search or run command...</span>
                        <kbd className="hidden sm:inline-flex h-5 items-center gap-1 rounded bg-white/5 px-1.5 font-mono text-[10px] font-medium text-zinc-500 group-hover:text-zinc-400">
                            ⌘K
                        </kbd>
                    </button>
                </div>
            </div>

            {/* 3. Command Palette */}
            <CommandPalette
                isOpen={isCmdOpen}
                onClose={() => setIsCmdOpen(false)}
                onAction={(id) => console.log('Action:', id)}
            />
        </div>
    );
}

const NavIcon = ({ icon, label, active, onClick }: any) => (
    <button
        onClick={onClick}
        className={clsx(
            "p-3 rounded-xl transition-all relative group",
            active ? "text-white bg-white/10" : "text-zinc-500 hover:text-zinc-300 hover:bg-white/5"
        )}
        title={label}
    >
        {icon}
        {active && (
            <div className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-6 bg-blue-500 rounded-r-full" />
        )}
    </button>
);

const SearchIcon = (props: any) => (
    <svg
        {...props}
        xmlns="http://www.w3.org/2000/svg"
        width="24"
        height="24"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
    >
        <circle cx="11" cy="11" r="8" />
        <path d="m21 21-4.3-4.3" />
    </svg>
);
