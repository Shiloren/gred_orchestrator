import { useCallback, useEffect } from 'react';
import {
    ReactFlow,
    Background,
    Controls,
    useNodesState,
    useEdgesState,
    addEdge,
    Connection,
    Edge,
    Node,
    BackgroundVariant,
    ReactFlowProvider,
    useReactFlow,
    NodeTypes
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import dagre from 'dagre';
import { GenericNode, GenericNodeType } from './GenericNode';

const nodeTypes: NodeTypes = {
    generic: GenericNode,
    agent_task: GenericNode,
    human_review: GenericNode,
    contract_check: GenericNode,
};

const getLayoutedElements = (nodes: GenericNodeType[], edges: Edge[], direction = 'LR') => {
    const dagreGraph = new dagre.graphlib.Graph();
    dagreGraph.setDefaultEdgeLabel(() => ({}));

    const isHorizontal = direction === 'LR';
    dagreGraph.setGraph({ rankdir: direction });

    nodes.forEach((node) => {
        dagreGraph.setNode(node.id, { width: 220, height: 100 });
    });

    edges.forEach((edge) => {
        dagreGraph.setEdge(edge.source, edge.target);
    });

    dagre.layout(dagreGraph);

    const layoutedNodes = nodes.map((node) => {
        const nodeWithPosition = dagreGraph.node(node.id);
        return {
            ...node,
            targetPosition: isHorizontal ? 'left' : 'top',
            sourcePosition: isHorizontal ? 'right' : 'bottom',
            position: {
                x: nodeWithPosition.x - 110, // center anchor
                y: nodeWithPosition.y - 50,
            },
        };
    });

    return { nodes: layoutedNodes, edges };
};

interface WorkflowCanvasProps {
    data: {
        nodes: GenericNodeType[];
        edges: Edge[];
    };
    onNodeClick?: (event: React.MouseEvent, node: Node) => void;
}

const LayoutHandler = ({ nodes, edges, setNodes, setEdges }: any) => {
    const { fitView } = useReactFlow();

    useEffect(() => {
        if (nodes.length > 0) {
            const layouted = getLayoutedElements(nodes, edges);
            setNodes([...layouted.nodes]);
            setEdges([...layouted.edges]);
            window.requestAnimationFrame(() => fitView({ padding: 0.2 }));
        }
    }, [nodes.length, edges.length, fitView, setNodes, setEdges]);

    return null;
};

export const WorkflowCanvas = ({ data, onNodeClick }: WorkflowCanvasProps) => {
    const [nodes, setNodes, onNodesChange] = useNodesState<GenericNodeType>(data.nodes);
    const [edges, setEdges, onEdgesChange] = useEdgesState(data.edges);

    useEffect(() => {
        setNodes(data.nodes);
        setEdges(data.edges);
    }, [data, setNodes, setEdges]);

    const onConnect = useCallback(
        (params: Connection) => setEdges((eds) => addEdge(params, eds)),
        [setEdges],
    );

    return (
        <div className="w-full h-full bg-zinc-950">
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onConnect={onConnect}
                onNodeClick={onNodeClick}
                nodeTypes={nodeTypes}
                proOptions={{ hideAttribution: true }}
                colorMode="dark"
                defaultEdgeOptions={{
                    animated: true,
                    style: { stroke: '#3b82f6', strokeWidth: 2 },
                    type: 'smoothstep'
                }}
            >
                <Background
                    variant={BackgroundVariant.Dots}
                    gap={20}
                    size={1}
                    color="#27272a"
                />
                <Controls className="!bg-zinc-900 !border-white/10 !fill-zinc-400" />
                <LayoutHandler
                    nodes={nodes}
                    edges={edges}
                    setNodes={setNodes}
                    setEdges={setEdges}
                />
            </ReactFlow>
        </div>
    );
};

export const WorkflowCanvasWrapper = (props: WorkflowCanvasProps) => (
    <ReactFlowProvider>
        <WorkflowCanvas {...props} />
    </ReactFlowProvider>
);
