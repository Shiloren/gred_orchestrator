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

const nodeTypes = {
    bridge: BridgeNode,
    orchestrator: OrchestratorNode,
    repo: RepoNode,
    cluster: ClusterNode,
};

interface GraphCanvasProps {
    onNodeSelect: (nodeId: string | null) => void;
    selectedNodeId: string | null;
    onNodeCountChange?: (count: number) => void;
}

export const GraphCanvas: React.FC<GraphCanvasProps> = ({ onNodeSelect, selectedNodeId, onNodeCountChange }) => {
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);

    const fetchGraphData = useCallback(async () => {
        try {
            const response = await fetch('/ui/graph', {
                credentials: 'include'
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

            const nodesWithLiveState = data.nodes.map((n: any) => {
                return {
                    ...n,
                    data: {
                        ...n.data,
                        // Backend now provides these fields dynamically
                        status: n.data.status || 'pending',
                        confidence: n.data.confidence,
                        pendingQuestions: n.data.pendingQuestions,
                        plan: n.data.plan,
                        quality: n.data.quality,
                        trustLevel: n.data.trustLevel || 'autonomous'
                    }
                };
            });

            onNodeCountChange?.(nodesWithLiveState.length);

            setNodes(nodesWithLiveState);
            setEdges(formattedEdges);
        } catch (error) {
            console.error('Error fetching graph data:', error);
            onNodeCountChange?.(0);
        }
    }, [setNodes, setEdges, onNodeCountChange]);

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
