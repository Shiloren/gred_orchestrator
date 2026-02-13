# Sub-Delegation Protocol (Fractal Orchestration)

## Overview
This protocol defines how a primary Agent can delegate sub-tasks to one or more Sub-Agents (Mini-Agents).

## Terminology
- **Primary Agent**: The high-level agent (e.g., Claude/GPT-4) managing the overall task.
- **Sub-Agent**: A specialized, ephemeral agent (e.g., Ollama/CodeLlama) executing a specific sub-task.
- **Cluster**: A logical grouping of a Primary Agent and its active Sub-Agents.

## Interaction Flow

### 1. Delegation Request
When a Primary Agent identifies a decomposable task, it sends a request to the Orchestrator.

**Channel:** `POST /api/agent/{agentId}/delegate`
**Payload:**
```json
{
  "subTaskDescription": "Generate unit tests for auth_service.py",
  "modelPreference": "llama3:8b",
  "constraints": {
    "timeout": 60,
    "maxTokens": 2048
  }
}
```

### 2. Approval & Instantiation
The Orchestrator checks the `TrustLevel` of the Primary Agent.
- **Autonomous**: Automatically approved.
- **Supervised/Restricted**: Requires user approval (via notification).

Upon approval, the Orchestrator:
1. Provisions a `SubAgent` instance ID.
2. Initializes the requested model backend (e.g., via Ollama).
3. Adds the Sub-Agent to the Graph under the Primary Agent's cluster.

### 3. Execution & Reporting
The Sub-Agent executes the task.
- Streaming output is forwarded to the Primary Agent context.
- UI updates to show the Sub-Agent node "working" (pulsing).

### 4. Completion
**Success:**
The Sub-Agent returns the final artifact (code, text) to the Orchestrator.
The Orchestrator forwards this to the Primary Agent as a "tool result".

**Failure:**
Exceptions are caught and reported to the Primary Agent, which can decide to retry or handle the error.

### 5. Cleanup
Once the result is delivered, the Sub-Agent node is marked as `terminated` (or removed, depending on UI preference for history).

## Data Types

### SubAgent
```typescript
interface SubAgent {
  id: string;
  parentId: string;
  model: string;
  status: 'starting' | 'working' | 'idle' | 'terminated';
  currentTask: string;
}
```

### DelegationEvent
```typescript
interface DelegationEvent {
  id: string;
  parentId: string;
  subAgentId: string;
  type: 'request' | 'approval' | 'result';
  timestamp: string;
}
```
