// API Configuration
export const API_BASE = import.meta.env.VITE_API_URL || `http://${globalThis.location?.hostname ?? 'localhost'}:9325`;

export type TrustLevel = 'autonomous' | 'supervised' | 'restricted';

export interface GraphNode {
    id: string;
    type: string;
    data: {
        label: string;
        status?: string;
        path?: string;
        plan?: AgentPlan;
        trustLevel?: TrustLevel;
        pendingQuestions?: AgentQuestion[];
        quality?: QualityMetrics;
        subAgents?: SubAgent[];
    };
    position: { x: number; y: number };
}

export type DegradationFlag = 'repetition' | 'coherence' | 'relevance' | 'latency' | 'none';

export interface QualityMetrics {
    score: number; // 0-100
    alerts: DegradationFlag[];
    lastCheck: string;
}

export type TaskStatus = 'pending' | 'running' | 'done' | 'failed';

export interface AgentQuestion {
    id: string;
    question: string;
    context?: string;
    timestamp: string;
    status: 'pending' | 'answered' | 'dismissed';
}

export interface AgentTask {
    id: string;
    description: string;
    status: TaskStatus;
    output?: string;
}

export interface AgentThought {
    id: string;
    content: string;
}

export interface AgentPlan {
    id: string;
    tasks: AgentTask[];
    currentStep?: number;
    reasoning?: AgentThought[];
}

export interface GraphEdge {
    id: string;
    source: string;
    target: string;
    animated?: boolean;
}

export interface GraphResponse {
    nodes: GraphNode[];
    edges: GraphEdge[];
}

export interface UiStatusResponse {
    version: string;
    uptime_seconds: number;
    allowlist_count: number;
    last_audit_line: string | null;
    service_status: string;
}

export type PlanStatus = 'draft' | 'review' | 'approved' | 'executing' | 'completed' | 'failed';

export interface PlanTask {
    id: string;
    title: string;
    description: string;
    status: TaskStatus;
    dependencies: string[]; // IDs of other PlanTasks
}

export interface AgentAssignment {
    agentId: string;
    taskIds: string[];
}

export interface Plan {
    id: string;
    title: string;
    status: PlanStatus;
    tasks: PlanTask[];
    assignments: AgentAssignment[];
}

export interface PlanCreateRequest {
    title: string;
    task_description: string;
}

export type MessageType = 'question' | 'instruction' | 'report' | 'reassignment';

export interface AgentMessage {
    id: string;
    from: 'agent' | 'orchestrator' | 'user';
    agentId: string;
    type: MessageType;
    content: string;
    timestamp: string;
}

export interface SubAgentConfig {
    model: string;
    temperature: number;
    max_tokens: number;
}

export interface SubAgent {
    id: string;
    parentId: string;
    name: string;
    model: string;
    status: 'starting' | 'working' | 'idle' | 'terminated' | 'failed';
    currentTask?: string;
    config: SubAgentConfig;
    result?: string;
}

export interface DelegationRequest {
    subTaskDescription: string;
    modelPreference: string;
    constraints?: Record<string, any>;
}

// --- Phase 11: Hybrid Provider System ---

export type ProviderType = 'ollama' | 'groq' | 'openrouter' | 'codex' | 'custom';

export interface ProviderConfig {
    id: string;
    type: ProviderType;
    name: string;
    enabled: boolean;
    base_url?: string;
    api_key?: string;
    default_model?: string;
    is_local: boolean;
    max_concurrent: number;
    cost_per_1k_tokens: number;
    max_context: number;
    models: string[];
}

export interface ComputeNode {
    id: string;
    name: string;
    role: string;
    max_concurrent_agents: number;
    current_agents: number;
    preferred_models: string[];
    provider_ids: string[];
    constraints: Record<string, any>;
}

export interface ProviderHealth {
    provider_id: string;
    available: boolean;
    latency_ms?: number;
    error?: string;
    last_check: string;
}

export interface ProviderCreateRequest {
    type: ProviderType;
    name: string;
    base_url?: string;
    api_key?: string;
    default_model?: string;
    is_local?: boolean;
    max_concurrent?: number;
    models?: string[];
}

export interface RepoInfo {
    name: string;
    path: string;
}

export interface OpsTask {
    id: string;
    title: string;
    scope: string;
    depends: string[];
    status: 'pending' | 'in_progress' | 'done' | 'blocked';
    description: string;
}

export interface OpsPlan {
    id: string;
    workspace: string;
    created: string;
    title: string;
    objective: string;
    tasks: OpsTask[];
    constraints: string[];
}

export interface OpsDraft {
    id: string;
    prompt: string;
    context?: Record<string, unknown>;
    provider?: string | null;
    content?: string | null;
    status: 'draft' | 'rejected' | 'approved' | 'error';
    error?: string | null;
    created_at: string;
}

export interface OpsApproved {
    id: string;
    draft_id: string;
    prompt: string;
    provider?: string | null;
    content: string;
    approved_at: string;
    approved_by?: string | null;
}

export interface OpsRun {
    id: string;
    approved_id: string;
    status: 'pending' | 'running' | 'done' | 'error' | 'cancelled';
    log: Array<{ ts: string; level: string; msg: string }>;
    started_at?: string | null;
    created_at: string;
}

export interface OpsApproveResponse {
    approved: OpsApproved;
    run: OpsRun | null;
}

export interface OpsConfig {
    default_auto_run: boolean;
    draft_cleanup_ttl_days: number;
    max_concurrent_runs: number;
    operator_can_generate: boolean;
}

export interface ProviderEntry {
    type: 'openai_compat' | 'anthropic' | 'gemini';
    base_url?: string | null;
    api_key?: string | null;
    model: string;
}

export interface RemoteProviderConfig {
    active: string;
    providers: Record<string, ProviderEntry>;
}
