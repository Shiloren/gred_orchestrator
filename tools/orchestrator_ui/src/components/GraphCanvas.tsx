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
import { ClusterNode } from './ClusterNode';

import { TrustLevel } from '../types';

const nodeTypes = {
    bridge: BridgeNode,
    orchestrator: OrchestratorNode,
    repo: RepoNode,
    cluster: ClusterNode,
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

            const mockPlan = {
                id: 'p1',
                tasks: [
                    { id: 't1', description: 'Analyze repository structure and dependencies', status: 'done', output: 'Found 12 modules, 3 main entry points.' },
                    { id: 't2', description: 'Evaluate GICS reasoning quality for current session', status: 'running' },
                    { id: 't3', description: 'Generate architectural refactoring proposal', status: 'pending' },
                    { id: 't4', description: 'Execute decomposition of God-file main.py', status: 'pending' },
                ],
                reasoning: [
                    { id: 'r1', content: 'Scanning codebase for architectural patterns...' },
                    { id: 'r2', content: 'Detected high coupling in main.py (430 lines).' },
                    { id: 'r3', content: 'Initiating Phase 2 visualization engine...' },
                    { id: 'r4', content: 'Awaiting GICS validation of reasoning pipeline.' }
                ]
            };

            const nodesWithMockPlans = data.nodes.map((n: any) => {
                const isAgent = n.type === 'orchestrator' || n.type === 'bridge';
                let trustLevel: TrustLevel | undefined;
                if (n.type === 'orchestrator') trustLevel = 'autonomous';
                else if (n.type === 'bridge') trustLevel = 'supervised';

                const pendingQuestions = n.type === 'bridge' ? [
                    {
                        id: 'q1',
                        question: 'Should I escalate the reasoning quality analysis to the fractal layer?',
                        context: 'Detected pattern that suggests sub-decomposition might be more token-efficient.',
                        timestamp: new Date().toISOString(),
                        status: 'pending'
                    }
                ] : undefined;

                return {
                    ...n,
                    data: {
                        ...n.data,
                        plan: isAgent ? mockPlan : undefined,
                        trustLevel,
                        pendingQuestions,
                        quality: isAgent ? {
                            score: n.type === 'orchestrator' ? 95 : 65,
                            alerts: n.type === 'bridge' ? ['repetition'] : [],
                            lastCheck: new Date().toISOString()
                        } : undefined
                    }
                };
            });

            setNodes(nodesWithMockPlans);
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
