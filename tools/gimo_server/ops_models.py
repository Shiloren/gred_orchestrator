from __future__ import annotations

# Compatibility shim: Re-export everything from the new models/ directory
# This ensures existing code importing from tools.gimo_server.ops_models continues to work.

try:
    from tools.gimo_server.models import (
        OpsTask, OpsPlan, OpsDraft, OpsApproved, OpsRunStatus, OpsRun, 
        OpsConfig, ExecutorReport, OpsCreateDraftRequest, OpsUpdateDraftRequest, 
        OpsApproveResponse, OpsCreateRunRequest, RepoEntry, RunEvent, RunLogEntry,
        AgentRole, AgentChannel, AgentProfile, AgentActionEvent, AgentInsight,
        ActionDraft, ProviderType, ProviderEntry, ProviderRoleBinding,
        ProviderRolesConfig, NormalizedModelInfo, ProviderModelsCatalogResponse,
        McpServerConfig, ProviderConfig, PHASE4_INTENT_CLASSES,
        ExecutionDecisionCode, IntentDecisionAudit, RuntimePolicyConfig,
        BaselineManifest, PolicyDecision, PolicyRuleMatch, PolicyRule, PolicyConfig,
        TrustRecord, TrustEvent, StrategyFinalStatus, ModelStrategyAudit, ProviderBudget,
        CascadeConfig, EcoModeConfig, UserEconomyConfig, CostEvent, BudgetForecast,
        NodeEconomyMetrics, PlanEconomySnapshot, CascadeResult, CascadeStatsEntry,
        CacheStats, RoiLeaderboardEntry, CostAnalytics, MasteryStatus, IntentClass,
        DelegationStatus, QaVerdict, RepoSnapshot, RepoContext, ContractExecution,
        StrictContract, Delegation, CommandRun, TestRun, DiffRef, Evidence, Failure,
        QaState, GraphState, WorkflowNode, WorkflowEdge, WorkflowGraph,
        WorkflowCheckpoint, WorkflowState, WorkflowExecuteRequest, ContractCheck,
        WorkflowContract, EvalGoldenCase, EvalDataset, EvalJudgeConfig,
        EvalGateConfig, EvalRunRequest, EvalCaseResult, EvalRunReport,
        EvalRunSummary, EvalRunDetail
    )
except ImportError:
    from .models import (
        OpsTask, OpsPlan, OpsDraft, OpsApproved, OpsRunStatus, OpsRun, 
        OpsConfig, ExecutorReport, OpsCreateDraftRequest, OpsUpdateDraftRequest, 
        OpsApproveResponse, OpsCreateRunRequest, RepoEntry, RunEvent, RunLogEntry,
        AgentRole, AgentChannel, AgentProfile, AgentActionEvent, AgentInsight,
        ActionDraft, ProviderType, ProviderEntry, ProviderRoleBinding,
        ProviderRolesConfig, NormalizedModelInfo, ProviderModelsCatalogResponse,
        McpServerConfig, ProviderConfig, PHASE4_INTENT_CLASSES,
        ExecutionDecisionCode, IntentDecisionAudit, RuntimePolicyConfig,
        BaselineManifest, PolicyDecision, PolicyRuleMatch, PolicyRule, PolicyConfig,
        TrustRecord, TrustEvent, StrategyFinalStatus, ModelStrategyAudit, ProviderBudget,
        CascadeConfig, EcoModeConfig, UserEconomyConfig, CostEvent, BudgetForecast,
        NodeEconomyMetrics, PlanEconomySnapshot, CascadeResult, CascadeStatsEntry,
        CacheStats, RoiLeaderboardEntry, CostAnalytics, MasteryStatus, IntentClass,
        DelegationStatus, QaVerdict, RepoSnapshot, RepoContext, ContractExecution,
        StrictContract, Delegation, CommandRun, TestRun, DiffRef, Evidence, Failure,
        QaState, GraphState, WorkflowNode, WorkflowEdge, WorkflowGraph,
        WorkflowCheckpoint, WorkflowState, WorkflowExecuteRequest, ContractCheck,
        WorkflowContract, EvalGoldenCase, EvalDataset, EvalJudgeConfig,
        EvalGateConfig, EvalRunRequest, EvalCaseResult, EvalRunReport,
        EvalRunSummary, EvalRunDetail
    )

RoleProfile = role_profile if "role_profile" in locals() else None
