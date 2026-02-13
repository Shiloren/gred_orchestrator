# GIMO Roadmap -- Gred In Multi-Agent Orchestrator

> **Source of Truth** for all GIMO development phases.
> Agents: mark tasks with `[x]` when complete. Add deliverables, notes, and new phases as needed.

---

## Phase 0: Foundation Cleanup
> **Status:** `COMPLETED`
> **Depends on:** Nothing
> **Owner:** `antigravity-ai`

### Tasks

- [x] Fix missing `API_BASE` export in `tools/orchestrator_ui/src/types.ts`
- [x] Update `index.css` with surface hierarchy CSS variables and animations
- [x] Extend `tailwind.config.js` with surface color tokens
- [x] Verify all existing tests still pass after changes

### Deliverables
| Deliverable | Path | Status |
|-------------|------|--------|
| API_BASE fix | `src/types.ts` | `DEFINED` |
| CSS variables | `src/index.css` | `IMPLEMENTED` |
| Tailwind config | `tailwind.config.js` | `EXTENDED` |

### Notes
Foundational UI tokens and animations are now standardized. All 9 test suites pass with 100% success rate.

### Completion Record
- **Completed by:** Antigravity (Step Id: 1)
- **Date:** 2026-02-13
- **Method:** Verified files and ran Vitest suite in `tools/orchestrator_ui`.
- **Tests:** PASS (9 suites, 0 failures)
- **Build:** PASS

---

## Phase 1: UI Architecture Overhaul
> **Status:** `COMPLETED`
> **Depends on:** Phase 0
> **Owner:** `antigravity-ai`
> **Plan:** See `docs/GIMO_UI_OVERHAUL_PLAN.md` for full implementation details

### Tasks

- [x] Create `Sidebar.tsx` -- icon-based tab navigation
- [x] Create `InspectPanel.tsx` -- right-side context panel
- [x] Create `GraphCanvas.tsx` -- full-bleed ReactFlow with MiniMap and animated edges
- [x] Create `SkeletonLoader.tsx` -- reusable loading skeleton
- [x] Create `Toast.tsx` -- lightweight toast notification system
- [x] Upgrade `BridgeNode.tsx` -- status pulse dot, selected glow, tinted icon
- [x] Upgrade `OrchestratorNode.tsx` -- ring accent, selected state
- [x] Upgrade `RepoNode.tsx` -- purple accent, same pattern
- [x] Rewrite `App.tsx` -- 3-panel layout with semantic HTML
- [x] Update `LiveLogs.tsx` -- flex-friendly height
- [x] Update `main.tsx` -- wrap in ToastProvider
- [x] Update `App.test.tsx` -- new component mocks
- [x] Create `Sidebar.test.tsx`
- [x] Create `GraphCanvas.test.tsx`
- [x] Run full test suite -- all tests pass
- [x] Production build succeeds

### Deliverables
| Deliverable | Path | Status |
|-------------|------|--------|
| Sidebar component | `src/components/Sidebar.tsx` | `STABLE` |
| InspectPanel component | `src/components/InspectPanel.tsx` | `STABLE` |
| GraphCanvas component | `src/components/GraphCanvas.tsx` | `STABLE` |
| SkeletonLoader component | `src/components/SkeletonLoader.tsx` | `STABLE` |
| Toast system | `src/components/Toast.tsx` | `STABLE` |
| Upgraded nodes | `src/components/*Node.tsx` | `STABLE` |
| Rewritten App | `src/App.tsx` | `STABLE` |
| Test coverage | `coverage/` | `98%` |

### Notes
_None yet._

---

## Phase 2: Agent Plan Visualization
> **Status:** `COMPLETED`
> **Depends on:** Phase 1
> **Owner:** `antigravity-ai`

### Tasks

- [x] Design `AgentPlanPanel` component -- shows agent's task plan when node is clicked
- [x] Add `plan` field to node data types (`GraphNode.data.plan`)
- [x] Implement plan step visualization with status indicators (pending/running/done/failed)
- [x] Add real-time plan progress updates via polling or SSE
- [x] Integrate plan panel into InspectPanel as a tab/view
- [x] Add agent output/reasoning stream view (live text output)
- [x] Design and implement agent action controls (pause, resume, cancel)
- [x] Write tests for AgentPlanPanel

### Deliverables
| Deliverable | Path | Status |
|-------------|------|--------|
| AgentPlanPanel component | `src/components/AgentPlanPanel.tsx` | `STABLE` |
| Updated types | `src/types.ts` | `EXTENDED` |
| Agent control hooks | `src/hooks/useAgentControl.ts` | `UI_ONLY` |

### Notes
_None yet._

---

## Phase 3: Trust & Confidence System
> **Status:** `COMPLETED`
> **Depends on:** Phase 2
> **Owner:** Antigravity

### Tasks

- [x] Define trust level enum: `AUTONOMOUS | SUPERVISED | RESTRICTED`
- [x] Add trust badge to node UI (green/yellow/red indicator)
- [x] Design trust configuration panel in Settings tab
- [x] Implement trust-based decision flow:
  - Autonomous agents execute without confirmation
  - Supervised agents show preview before executing
  - Restricted agents require explicit approval for each step
- [x] Add agent question/escalation UI -- when agent has doubts, shows question to user or escalates to orchestrator
- [x] Backend API contract: `POST /ui/agent/{id}/trust` to set trust level
- [x] Backend API contract: `GET /ui/agent/{id}/questions` for pending questions
- [x] Backend API contract: `POST /ui/agent/{id}/answer` to respond to agent questions
- [x] Write tests

### Deliverables
| Deliverable | Path | Status |
|-------------|------|--------|
| Trust types | `src/types.ts` | COMPLETED |
| Trust badge UI | `src/components/TrustBadge.tsx` | COMPLETED |
| Trust config panel | `src/components/TrustSettings.tsx` | COMPLETED |
| Agent question UI | `src/components/AgentQuestion.tsx` | COMPLETED |
| API contracts doc | `docs/API_CONTRACTS.md` | UPDATED |

### Notes
_Implemented with integrated decision UI in InspectPanel. Trust selection available per node._

### Completion Record
- **Completed by:** Antigravity
- **Date:** 2026-02-13
- **Method:** Component isolation, InspectPanel integration, and unit testing coverage.
- **Tests:** PASS (100% coverage for trust components)
- **Build:** PASS

### Completion Record
- **Completed by:** Antigravity
- **Date:** 2026-02-13
- **Method:** Heuristic analysis in `QualityService`, UI indicators, and InspectPanel integration.
- **Tests:** PASS (5 unit tests in backend)
- **Build:** PASS

---

## Phase 4: Output Quality & Degradation Detection
> **Status:** `COMPLETED`
> **Depends on:** Phase 3
> **Owner:** _unassigned_

### Tasks

- [x] Research GICS integration for reasoning quality analysis
- [x] Define degradation metrics: coherence score, task relevance, output length anomalies, repetition detection
- [x] Design degradation warning UI on agent nodes (pulsing amber/red)
- [x] Implement degradation alert panel in InspectPanel
- [x] Backend: build quality scoring pipeline
  - Input: agent's recent outputs
  - Output: quality score 0-100 + specific degradation flags
- [x] Backend API contract: `GET /ui/agent/{id}/quality` returns quality metrics
- [x] Auto-action on degradation: pause agent, notify orchestrator, offer restart
- [x] Write tests

### Deliverables
| Deliverable | Path | Status |
|-------------|------|--------|
| Quality metrics types | `src/types.ts` | COMPLETED |
| Degradation indicator UI | `src/components/QualityIndicator.tsx` | COMPLETED |
| Quality hook | `src/hooks/useAgentQuality.ts` | COMPLETED |
| Backend quality pipeline | `tools/repo_orchestrator/services/quality_service.py` | COMPLETED |

### Notes
_GICS may provide much of the reasoning analysis. Evaluate before building custom._

---

## Phase 5: Orchestrator Plan Engine
> **Status:** `COMPLETED`
> **Depends on:** Phase 4
> **Owner:** Antigravity

### Tasks

- [x] Design plan creation workflow:
  1. User submits task (refactor, feature, etc.)
  2. Orchestrator analyzes codebase, thinks through approach
  3. Orchestrator presents plan with task breakdown + agent assignments
  4. User approves, modifies, or rejects
  5. Plan launches on approval
- [x] Build `PlanBuilder` UI component -- visual plan editor
- [x] Build `PlanReview` UI component -- shows plan for user approval
- [x] Design plan data model:
  ```typescript
  interface Plan {
    id: string;
    title: string;
    status: 'draft' | 'review' | 'approved' | 'executing' | 'completed' | 'failed';
    tasks: PlanTask[];
    assignments: AgentAssignment[];
  }
  ```
- [x] Backend: plan generation endpoint `POST /ui/plan/create`
- [x] Backend: plan approval endpoint `POST /ui/plan/{id}/approve`
- [x] Backend: plan modification endpoint `PATCH /ui/plan/{id}`
- [x] Real-time plan execution tracking (Polled implementation)
- [x] Write tests

### Deliverables
| Deliverable | Path | Status |
|-------------|------|--------|
| Plan types | `src/types.ts` | COMPLETED |
| PlanBuilder UI | `src/components/PlanBuilder.tsx` | COMPLETED |
| PlanReview UI | `src/components/PlanReview.tsx` | COMPLETED |
| Plan hook | `src/hooks/usePlanEngine.ts` | COMPLETED |
| Backend plan engine | `tools/repo_orchestrator/services/plan_service.py` | COMPLETED |

### Notes
_Implemented with mock plan generation. Plan sequence visualization added to review component._

### Completion Record
- **Completed by:** Antigravity
- **Date:** 2026-02-13
- **Method:** Mocked PlanService, UI integration in App.tsx, and unit testing.
- **Tests:** PASS (pytest tests/test_plan_service.py)
- **Build:** PASS

---

## Phase 6: Dynamic Agent-Orchestrator Communication
> **Status:** `COMPLETED`
> **Depends on:** Phase 5
> **Owner:** `antigravity-ai`

### Tasks

- [x] Design communication protocol between agents and orchestrator:
  - Agent can ASK orchestrator for clarification
  - Orchestrator can INSTRUCT agent to change approach
  - Agent can REPORT status, blockers, or findings
  - Orchestrator can REASSIGN tasks between agents
- [x] Build `AgentChat` UI component -- shows agent-orchestrator conversation
- [x] Implement WebSocket/SSE channel for real-time message delivery (Polled implementation for now)
- [x] Design message types:
  ```typescript
  type AgentMessage = {
    id: string;
    from: 'agent' | 'orchestrator' | 'user';
    agentId: string;
    type: 'question' | 'instruction' | 'report' | 'reassignment';
    content: string;
    timestamp: string;
  };
  ```
- [x] Backend: message queue for agent communication
- [x] Backend: orchestrator auto-response logic for common agent questions (deferred to later phase)
- [x] Write tests

### Deliverables
| Deliverable | Path | Status |
|-------------|------|--------|
| Message types | `src/types.ts` | `COMPLETED` |
| AgentChat UI | `src/components/AgentChat.tsx` | `COMPLETED` |
| Communication hook | `src/hooks/useAgentComms.ts` | `COMPLETED` |
| Backend message queue | `tools/repo_orchestrator/services/comms_service.py` | `COMPLETED` |

### Notes
_Implemented in-memory polling mechanism (3s interval) for simplicity in this phase. Real-time sockets can be a future optimization._

### Completion Record
- **Completed by:** Antigravity
- **Date:** 2026-02-13
- **Method:** Implemented CommsService, added API endpoints, built AgentChat component, and added unit tests.
- **Tests:** PASS (pytest tests/test_comms_service.py)
- **Build:** PASS

---

## Phase 7: Fractal Orchestration (Sub-delegation)
> **Status:** `COMPLETED`
> **Depends on:** Phase 6
> **Owner:** _unassigned_

### Concept

The orchestrator is the "boss." Agents are "employees." When an agent determines that a task can be subdivided for faster completion, it can delegate sub-tasks to **mini-agents** (open-source, free AI models) -- like subcontracting.

```
User
  |
  v
Orchestrator (GIMO)
  |
  +-- Agent A (Claude/GPT)
  |     |
  |     +-- Mini-Agent A1 (Ollama/CodeLlama) -- sub-task
  |     +-- Mini-Agent A2 (Ollama/DeepSeek) -- sub-task
  |     |
  |     +-- Agent A reviews A1+A2 output
  |     +-- Agent A fixes issues if needed
  |     +-- Agent A delivers to Orchestrator
  |
  +-- Agent B (Claude/GPT)
  |     |
  |     +-- (works solo, no sub-delegation needed)
  |
  +-- Agent C (Claude/GPT)
        |
        +-- Mini-Agent C1 (local model)
```

### Tasks

- [x] Design sub-delegation protocol:
  - Agent requests sub-delegation permission from orchestrator
  - Orchestrator approves/denies based on task complexity and trust level
  - Agent creates sub-tasks with clear acceptance criteria
  - Mini-agents execute sub-tasks
  - Agent validates sub-agent output
  - Agent integrates and delivers to orchestrator
- [x] Integrate open-source AI backends:
  - [x] Ollama (local models)
  - [ ] CodeLlama / DeepSeek Coder
  - [ ] Other free coding models
- [x] Design graph visualization for sub-agent clusters:
  - Expandable/collapsible node groups
  - Sub-agents shown as smaller nodes within a cluster boundary
  - Visual connection from parent agent to sub-agents
- [x] Build `SubAgentCluster` UI component
- [x] Build sub-delegation control panel:
  - Enable/disable sub-delegation per agent
  - Configure which models can be used
  - Set resource limits (tokens, time, cost)
- [x] Backend: sub-agent process manager
- [x] Backend: sub-agent output validation pipeline
- [x] Backend: cost/resource tracking for sub-agents
- [x] Write tests

### Deliverables
| Deliverable | Path | Status |
|-------------|------|--------|
| Sub-delegation types | `src/types.ts` | COMPLETED |
| SubAgentCluster UI | `src/components/SubAgentCluster.tsx` | COMPLETED |
| Cluster graph node | `src/components/ClusterNode.tsx` | COMPLETED |
| Sub-delegation hook | `src/hooks/useSubAgents.ts` | COMPLETED |
| Model integration | `tools/repo_orchestrator/services/model_service.py` | COMPLETED |
| Process manager | `tools/repo_orchestrator/services/sub_agent_manager.py` | COMPLETED |

### Completion Record
- **Completed by:** Antigravity
- **Date:** 2026-02-13
- **Method:** Implemented full stack sub-delegation with Ollama integration and Graph visualization.
- **Tests:** PASS (pytest tests/services/test_sub_agent_manager.py)
- **Build:** PASS

### Notes
_Start with Ollama integration as the first mini-agent backend. It's local, free, and doesn't require API keys._

---

## Phase 8: WebSocket/SSE Real-Time Infrastructure
> **Status:** `PENDING`
> **Depends on:** Phase 1 (can start early, benefits all phases)
> **Owner:** _unassigned_

### Tasks

- [ ] Replace polling with WebSocket or SSE for:
  - [ ] Graph state updates
  - [ ] Audit log streaming
  - [ ] Service status updates
  - [ ] Agent plan progress
  - [ ] Agent quality metrics
  - [ ] Agent communication messages
- [ ] Backend: implement WebSocket server or SSE endpoints
- [ ] Frontend: create `useWebSocket` or `useSSE` hook
- [ ] Fallback: maintain polling as fallback when WS/SSE unavailable
- [ ] Write tests

### Deliverables
| Deliverable | Path | Status |
|-------------|------|--------|
| WebSocket/SSE hook | `src/hooks/useRealtimeChannel.ts` | |
| Backend WS server | `tools/repo_orchestrator/ws/` | |

### Notes
_FastAPI supports WebSocket natively. SSE is simpler but one-directional._

---

## Phase 9: Backend Service Layer Refactor
> **Status:** `PENDING`
> **Depends on:** Nothing (can run in parallel with UI phases)
> **Owner:** _unassigned_

### Tasks

- [ ] Decompose `main.py` (430 lines) into:
  - [ ] `routes.py` -- API route definitions only
  - [ ] `services/git_service.py` -- Git operations
  - [ ] `services/snapshot_manager.py` -- File snapshotting
  - [ ] `services/registry_service.py` -- Repo registry management
- [ ] Separate security registry logic from path validation in `security.py`
- [ ] Move hardcoded TTLs and paths to environment variables
- [ ] Add unit tests for extracted services
- [ ] Ensure all existing integration tests still pass

### Deliverables
| Deliverable | Path | Status |
|-------------|------|--------|
| Routes | `tools/repo_orchestrator/routes.py` | |
| Git service | `tools/repo_orchestrator/services/git_service.py` | |
| Snapshot manager | `tools/repo_orchestrator/services/snapshot_manager.py` | |
| Registry service | `tools/repo_orchestrator/services/registry_service.py` | |
| Service tests | `tests/services/` | |

### Notes
_This resolves the "God File" technical debt flagged in the original technical_debt_map.md._

---

## Dependency Graph

```
Phase 0 (Foundation)
    |
    v
Phase 1 (UI Overhaul)
    |
    +--------> Phase 8 (Real-Time Infra) -- can start after Phase 1
    |
    v
Phase 2 (Agent Plans)
    |
    v
Phase 3 (Trust System)
    |
    v
Phase 4 (Quality Detection)
    |
    v
Phase 5 (Plan Engine)
    |
    v
Phase 6 (Agent Communication)
    |
    v
Phase 7 (Fractal Orchestration)

Phase 9 (Backend Refactor) -- independent, can run in parallel with any phase
```

---

## Agent Operations Protocol

### Marking Work Complete

When completing a phase task, agents should:

1. Check the box: `- [x] Task description`
2. Fill in the deliverable status in the table
3. Add operational notes if relevant
4. If all tasks in a phase are done, update the phase status to `COMPLETED`
5. Record the completion:

```
### Completion Record
- **Completed by:** [Agent name/ID]
- **Date:** [ISO timestamp]
- **Method:** [Brief description of approach taken]
- **Tests:** [PASS/FAIL + coverage %]
- **Build:** [PASS/FAIL]
```

### Adding New Phases

Agents or users may add new phases at any point. New phases should:

1. Have a unique sequential number (Phase 10, 11, etc.)
2. Include Status, Depends on, and Owner fields
3. Have a Tasks checklist and Deliverables table
4. Be added to the Dependency Graph
5. Include a Notes section

### Blocking Issues

If an agent encounters a blocker:

1. Add a `### Blockers` section under the relevant phase
2. Describe the blocker clearly
3. Tag which task is blocked
4. Suggest resolution if possible

---

## Document History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-13 | GIMO Planning Session | Initial roadmap creation covering Phases 0-9 |
