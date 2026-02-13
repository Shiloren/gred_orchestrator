import { useState, useEffect } from 'react';
import { Sidebar, SidebarTab } from './components/Sidebar';
import { GraphCanvas } from './components/GraphCanvas';
import { InspectPanel } from './components/InspectPanel';
import { MaintenanceIsland } from './islands/system/MaintenanceIsland';
import { Zap } from 'lucide-react';
import { UiStatusResponse, PlanCreateRequest } from './types';
import { usePlanEngine } from './hooks/usePlanEngine';
import { PlanBuilder } from './components/PlanBuilder';
import { PlanReview } from './components/PlanReview';
import { ReactFlowProvider } from 'reactflow';

export default function App() {
    const [status, setStatus] = useState<UiStatusResponse | null>(null);
    const [activeTab, setActiveTab] = useState<SidebarTab>('graph');
    const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
    const [inspectOpen, setInspectOpen] = useState(true);

    const { currentPlan, loading, createPlan, approvePlan } = usePlanEngine();

    useEffect(() => {
        const fetchStatus = async () => {
            try {
                const response = await fetch('/ui/status', {
                    headers: { 'Authorization': 'Bearer demo-token' }
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

    const handleNodeSelect = (nodeId: string | null) => {
        setSelectedNodeId(nodeId);
        if (nodeId) {
            setActiveTab('graph');
            setInspectOpen(true);
        }
    };

    const handleCreatePlan = async (req: PlanCreateRequest) => {
        await createPlan(req);
    };

    const handleApprovePlan = async () => {
        if (currentPlan) {
            await approvePlan(currentPlan.id);
        }
    };

    return (
        <div className="min-h-screen bg-[#000000] text-[#f5f5f7] font-sans selection:bg-[#0a84ff] selection:text-white flex flex-col">
            <header role="banner" className="h-12 border-b border-[#2c2c2e] bg-[#000000]/80 backdrop-blur-xl flex items-center justify-between px-4 z-50 shrink-0">
                <div className="flex items-center gap-3">
                    <div className="w-7 h-7 bg-[#0a84ff] rounded-lg flex items-center justify-center glow-blue">
                        <Zap size={14} className="text-white" />
                    </div>
                    <span className="font-semibold tracking-tight text-sm">Repo Orchestrator</span>
                    <span className="text-[10px] text-[#86868b] font-mono bg-[#1c1c1e] px-2 py-0.5 rounded-full ml-1">Gred In Labs</span>
                </div>
                <div className="flex items-center gap-4 text-xs text-[#86868b]">
                    <div className="flex items-center gap-1.5">
                        <div className="w-1.5 h-1.5 rounded-full bg-[#32d74b] animate-pulse" />
                        <span>{status?.service_status || 'Connecting...'}</span>
                    </div>
                </div>
            </header>

            <div className="flex flex-1 overflow-hidden">
                <ReactFlowProvider>
                    <Sidebar
                        activeTab={activeTab}
                        onTabChange={(tab) => {
                            setActiveTab(tab);
                            setInspectOpen(true);
                        }}
                    />

                    <main role="main" className="flex-1 relative overflow-hidden">
                        <GraphCanvas
                            onNodeSelect={handleNodeSelect}
                            selectedNodeId={selectedNodeId}
                        />
                    </main>

                    {inspectOpen && (
                        <InspectPanel
                            activeTab={activeTab}
                            selectedNodeId={selectedNodeId}
                            onClose={() => setInspectOpen(false)}
                        >
                            {activeTab === 'plans' && (
                                currentPlan ? (
                                    <PlanReview
                                        plan={currentPlan}
                                        onApprove={handleApprovePlan}
                                        onModify={() => console.log('Modify')}
                                        loading={loading}
                                    />
                                ) : (
                                    <PlanBuilder onCreate={handleCreatePlan} loading={loading} />
                                )
                            )}
                            {activeTab === 'maintenance' && <MaintenanceIsland />}
                        </InspectPanel>
                    )}
                </ReactFlowProvider>
            </div>

            <footer role="contentinfo" className="h-8 border-t border-[#2c2c2e] bg-[#0a0a0a] flex items-center justify-between px-4 text-[10px] text-[#424245] uppercase tracking-widest shrink-0">
                <div className="flex items-center gap-4">
                    <span>Gred In Labs</span>
                    <span className="text-[#1c1c1e]">|</span>
                    <span>v{status?.version || '1.0.0'}</span>
                </div>
                <div className="font-mono lowercase italic opacity-50">
                    multi-agent orchestration engine
                </div>
            </footer>
        </div>
    );
}
