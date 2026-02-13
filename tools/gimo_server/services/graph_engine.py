from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import inspect
import logging
from pathlib import Path
import time
import uuid
from typing import Any, Dict, List, Optional

from ..ops_models import (
    ContractCheck,
    WorkflowCheckpoint, 
    WorkflowContract,
    WorkflowEdge, 
    WorkflowGraph, 
    WorkflowNode, 
    WorkflowState
)
from .model_router_service import ModelRouterService
from .observability_service import ObservabilityService
from .storage_service import StorageService

logger = logging.getLogger("orchestrator.services.graph_engine")


class GraphEngine:
    """MVP Graph Execution Engine."""

    def __init__(
        self,
        graph: WorkflowGraph,
        max_iterations: int = 100,
        storage: Optional[StorageService] = None,
        persist_checkpoints: bool = False,
        workflow_timeout_seconds: Optional[int] = None,
    ):
        self.graph = graph
        self.state = WorkflowState()
        self.max_iterations = max_iterations
        self.storage = storage
        self.persist_checkpoints = persist_checkpoints
        self.workflow_timeout_seconds = workflow_timeout_seconds
        self._nodes_by_id = {node.id: node for node in self.graph.nodes}
        self._resume_from_node_id: Optional[str] = None
        self._execution_started_at: Optional[float] = None
        self._edges_from = {}
        for edge in self.graph.edges:
            self._edges_from.setdefault(edge.from_node, []).append(edge)
        self._model_router = ModelRouterService()

    async def execute(self, initial_state: Optional[Dict[str, Any]] = None) -> WorkflowState:
        if initial_state:
            self.state.data.update(initial_state)
        if self._execution_started_at is None:
            self._execution_started_at = time.perf_counter()

        trace_id = str(self.state.data.get("trace_id") or uuid.uuid4().hex)
        self.state.data["trace_id"] = trace_id
        ObservabilityService.record_workflow_start(self.graph.id, trace_id)

        # Structured execution trace (MVP) stored in workflow state
        self.state.data.setdefault("step_logs", [])
        self.state.data.setdefault("budget_counters", {"steps": 0, "tokens": 0, "cost_usd": 0.0})

        if self.persist_checkpoints and self.storage:
            self.storage.save_workflow(self.graph.id, self._serialize_graph())

        if not self.graph.nodes:
            return self.state

        current_node_id = self._resume_from_node_id or self.graph.nodes[0].id
        self._resume_from_node_id = None
        iterations = 0
        
        while current_node_id and iterations < self.max_iterations:
            timeout_reason = self._check_workflow_timeout()
            if timeout_reason:
                self.state.data["aborted_reason"] = timeout_reason
                break

            budget_reason = self._check_budget_before_step()
            if budget_reason:
                self._handle_budget_exceeded(budget_reason)
                break

            iterations += 1
            node = self._nodes_by_id[current_node_id]
            step_id = f"step_{iterations}"
            logger.info("%s: executing node=%s type=%s", step_id, node.id, node.type)
            started_at = time.perf_counter()
            
            try:
                output = await self._run_node_with_retries(node)

                # Every node can mutate state by returning a dict
                if isinstance(output, dict):
                    self.state.data.update(output)

                self._update_budget_counters(output)

                if isinstance(output, dict) and output.get("pause_execution"):
                    self._resume_from_node_id = node.id
                    self.state.data["execution_paused"] = True
                    self.state.data["pause_reason"] = output.get("pause_reason", "human_review_pending")
                    self._append_step_log(
                        step_id=step_id,
                        node=node,
                        status="paused",
                        started_at=started_at,
                        output=output,
                    )
                    break

                self.state.data["execution_paused"] = False

                checkpoint = WorkflowCheckpoint(
                    node_id=node.id,
                    state=self.state.data.copy(),
                    output=output,
                    status="completed"
                )
                self.state.checkpoints.append(checkpoint)
                self._persist_checkpoint(checkpoint)

                self._append_step_log(
                    step_id=step_id,
                    node=node,
                    status="completed",
                    started_at=started_at,
                    output=output,
                )

                # Determine next node
                current_node_id = self._get_next_node(node.id, output)

                budget_reason = self._check_budget_after_step()
                if budget_reason:
                    self._handle_budget_exceeded(budget_reason)
                    break
                
            except Exception as e:
                logger.error(f"Error executing node {node.id}: {e}")
                if isinstance(e, TimeoutError):
                    error_text = "timed out"
                else:
                    error_text = str(e) or e.__class__.__name__
                checkpoint = WorkflowCheckpoint(
                    node_id=node.id,
                    state=self.state.data.copy(),
                    output=None,
                    status="failed"
                )
                self.state.checkpoints.append(checkpoint)
                self._persist_checkpoint(checkpoint)
                self._append_step_log(
                    step_id=step_id,
                    node=node,
                    status="failed",
                    started_at=started_at,
                    output={"error": error_text},
                )
                break

        if current_node_id and iterations >= self.max_iterations:
            logger.warning("max_iterations reached (%s) at node=%s", self.max_iterations, current_node_id)
            self.state.data["aborted_reason"] = "max_iterations_exceeded"

        return self.state

    async def _run_node_with_retries(self, node: WorkflowNode) -> Any:
        attempts = 0
        max_attempts = max(int(node.retries or 0) + 1, 1)
        base_backoff = float(node.config.get("retry_backoff_seconds", 0.0) or 0.0)
        last_error: Optional[Exception] = None

        while attempts < max_attempts:
            attempts += 1
            try:
                if node.timeout and int(node.timeout) > 0:
                    output = await asyncio.wait_for(self._run_node(node), timeout=int(node.timeout))
                else:
                    output = await self._run_node(node)

                if attempts > 1 and isinstance(output, dict):
                    output.setdefault("retry_attempts", attempts)
                return output
            except Exception as exc:
                last_error = exc
                if attempts >= max_attempts:
                    raise
                if base_backoff > 0:
                    await asyncio.sleep(base_backoff * (2 ** (attempts - 1)))

        raise RuntimeError(str(last_error) if last_error else f"Node failed without error: {node.id}")

    async def _run_node(self, node: WorkflowNode) -> Any:
        if node.type == "human_review":
            return await self._run_human_review(node)

        if node.type == "contract_check":
            return self._run_contract_check(node)

        if node.type == "agent_task":
            return await self._run_agent_task(node)

        return await self._call_execute_node(node)

    async def _call_execute_node(self, node: WorkflowNode) -> Any:
        """Run node and support both legacy and new execution signatures.

        Supported execution callables:
        - _execute_node(node)
        - _execute_node(node, state)
        """
        execute_callable = self._execute_node
        if node.type in {"llm_call", "agent_task"}:
            routing = self._model_router.choose_model(node, self.state.data)
            self.state.data["model_router_last"] = {
                "node_id": node.id,
                "selected_model": routing.model,
                "reason": routing.reason,
            }
            self.state.data.setdefault("model_router_trace", []).append(self.state.data["model_router_last"])

            if isinstance(node.config, dict):
                node.config.setdefault("selected_model", routing.model)

        params = inspect.signature(execute_callable).parameters
        if len(params) >= 2:
            return await execute_callable(node, self.state.data)
        return await execute_callable(node)

    async def _run_agent_task(self, node: WorkflowNode) -> Dict[str, Any]:
        pattern = str(node.config.get("pattern", "single")).strip().lower()

        if pattern == "supervisor_workers":
            workers = node.config.get("workers") or []
            worker_results: Dict[str, Any] = {}
            for idx, worker in enumerate(workers):
                worker_id = str(worker.get("id") or f"worker_{idx + 1}")
                payload = {
                    "task": worker.get("task"),
                    "shared_context": dict(self.state.data),
                    "role": "worker",
                    "worker_id": worker_id,
                }
                worker_output = await self._run_agent_child(node, child_suffix=worker_id, payload=payload)
                worker_results[worker_id] = worker_output
            return {
                "pattern": "supervisor_workers",
                "worker_results": worker_results,
            }

        if pattern == "reviewer_loop":
            max_rounds = max(int(node.config.get("max_rounds", 3) or 3), 1)
            candidate: Any = None
            feedback: Optional[str] = None
            reviews: List[Dict[str, Any]] = []

            for round_idx in range(1, max_rounds + 1):
                gen_output = await self._run_agent_child(
                    node,
                    child_suffix=f"generator_r{round_idx}",
                    payload={
                        "role": "generator",
                        "round": round_idx,
                        "candidate": candidate,
                        "feedback": feedback,
                    },
                )
                candidate = gen_output.get("candidate", gen_output)

                review_output = await self._run_agent_child(
                    node,
                    child_suffix=f"reviewer_r{round_idx}",
                    payload={
                        "role": "reviewer",
                        "round": round_idx,
                        "candidate": candidate,
                    },
                )
                approved = bool(review_output.get("approved", False))
                feedback = review_output.get("feedback")
                reviews.append(
                    {
                        "round": round_idx,
                        "approved": approved,
                        "feedback": feedback,
                    }
                )
                if approved:
                    return {
                        "pattern": "reviewer_loop",
                        "approved": True,
                        "rounds": round_idx,
                        "candidate": candidate,
                        "reviews": reviews,
                    }

            return {
                "pattern": "reviewer_loop",
                "approved": False,
                "rounds": max_rounds,
                "candidate": candidate,
                "reviews": reviews,
            }

        if pattern == "handoff":
            context_keys = node.config.get("context_keys") or []
            curated_context = {
                str(k): self.state.data.get(str(k))
                for k in context_keys
            }
            source_output = await self._run_agent_child(
                node,
                child_suffix="source",
                payload={
                    "role": "source",
                    "handoff_context": curated_context,
                },
            )
            target_output = await self._run_agent_child(
                node,
                child_suffix="target",
                payload={
                    "role": "target",
                    "handoff_context": curated_context,
                    "source_output": source_output,
                },
            )
            return {
                "pattern": "handoff",
                "handoff_context": curated_context,
                "source_output": source_output,
                "target_output": target_output,
            }

        # default agent_task behaves as a single executable node
        output = await self._call_execute_node(node)
        if isinstance(output, dict):
            output.setdefault("pattern", "single")
        return output

    async def _run_agent_child(self, parent_node: WorkflowNode, *, child_suffix: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        child_node = WorkflowNode(
            id=f"{parent_node.id}__{child_suffix}",
            type="agent_task",
            config=payload,
            agent=parent_node.agent,
            timeout=parent_node.timeout,
            retries=0,
        )
        result = await self._call_execute_node(child_node)
        return result if isinstance(result, dict) else {"result": result}

    def _run_contract_check(self, node: WorkflowNode) -> Dict[str, Any]:
        """Execute contract checks in pre/post mode.

        Expected node.config:
        {
          "phase": "pre" | "post",
          "contract": { ... WorkflowContract-compatible ... }
        }
        """
        raw_contract = node.config.get("contract", node.config)
        contract = WorkflowContract.model_validate(raw_contract)
        phase = str(node.config.get("phase", "pre")).lower()
        checks = contract.pre_conditions if phase == "pre" else contract.post_conditions

        failed: List[Dict[str, Any]] = []
        for check in checks:
            passed = self._evaluate_contract_check(check)
            if not passed:
                failed.append({"type": check.type, "params": check.params})

        output = {
            "contract_phase": phase,
            "checks_total": len(checks),
            "checks_failed": failed,
            "contract_passed": len(failed) == 0,
            "blast_radius": contract.blast_radius,
        }

        if failed and phase == "post":
            rollback_result = self._run_rollback(contract.rollback)
            output["rollback_executed"] = rollback_result
            self.state.data["contract_failure"] = output
            raise RuntimeError(f"Post-contract checks failed: {failed}")

        if failed:
            self.state.data["contract_failure"] = output
            raise RuntimeError(f"Pre-contract checks failed: {failed}")

        self.state.data["last_contract_check"] = output
        return output

    async def _run_human_review(self, node: WorkflowNode) -> Dict[str, Any]:
        """Interactive HITL node.

        Uses state.data["human_reviews"][node.id] as operator/admin decision payload.
        Supported decision values:
        - approve
        - reject
        - edit_state
        - takeover
        - fork
        """
        reviews = self.state.data.setdefault("human_reviews", {})
        annotations = self.state.data.setdefault("human_annotations", [])
        decision_payload = reviews.get(node.id)

        timeout_seconds = int(node.config.get("timeout_seconds", 0) or 0)
        default_action = str(node.config.get("default_action", "block"))
        now = datetime.now(timezone.utc)
        pending_key = "human_review_pending"
        pending = dict(self.state.data.get(pending_key) or {})

        if not decision_payload:
            pending_started_at = pending.get("started_at")
            started_dt = self._parse_iso_ts(pending_started_at)
            if pending.get("node_id") != node.id or not started_dt:
                started_dt = now
                pending = {
                    "node_id": node.id,
                    "started_at": started_dt.isoformat(),
                    "timeout_seconds": timeout_seconds,
                    "default_action": default_action,
                }
                self.state.data[pending_key] = pending

            if timeout_seconds > 0 and (now - started_dt).total_seconds() >= timeout_seconds:
                if default_action == "approve":
                    self.state.data.pop(pending_key, None)
                    return {
                        "human_review": "auto_approved_timeout",
                        "human_review_node": node.id,
                    }
                raise RuntimeError(f"Human review timeout at node {node.id}; default_action={default_action}")

            return {
                "pause_execution": True,
                "pause_reason": "human_review_pending",
                "human_review_node": node.id,
                "timeout_seconds": timeout_seconds,
                "default_action": default_action,
            }

        decision = str(decision_payload.get("decision", "")).lower().strip()
        edited_state = decision_payload.get("edited_state") or {}
        annotation = decision_payload.get("annotation")
        if annotation:
            annotations.append(
                {
                    "node_id": node.id,
                    "timestamp": now.isoformat(),
                    "note": str(annotation),
                }
            )

        self.state.data.pop(pending_key, None)

        if decision == "approve":
            return {
                "human_review": "approved",
                "human_review_node": node.id,
            }

        if decision == "reject":
            raise RuntimeError(f"Human review rejected at node {node.id}")

        if decision in {"edit", "edit_state"}:
            if isinstance(edited_state, dict):
                self.state.data.update(edited_state)
            return {
                "human_review": "edited",
                "human_review_node": node.id,
                "edited_keys": sorted(list(edited_state.keys())) if isinstance(edited_state, dict) else [],
            }

        if decision == "takeover":
            if isinstance(edited_state, dict):
                self.state.data.update(edited_state)
            return {
                "human_review": "takeover",
                "human_review_node": node.id,
                "takeover": True,
            }

        if decision == "fork":
            branches = node.config.get("fork_options") or []
            selected_branch = decision_payload.get("selected_branch")
            if not isinstance(branches, list) or not branches:
                raise RuntimeError(f"Fork requested at node {node.id} but no branch selected")

            async def _run_branch(idx: int, branch: Any) -> Dict[str, Any]:
                await asyncio.sleep(0)
                if isinstance(branch, dict):
                    branch_id = str(branch.get("id") or branch.get("name") or f"branch_{idx + 1}")
                    return {
                        "branch_id": branch_id,
                        "state_patch": dict(branch.get("state_patch") or {}),
                        "output": branch.get("output"),
                    }

                branch_id = str(branch)
                return {
                    "branch_id": branch_id,
                    "state_patch": {},
                    "output": None,
                }

            branch_results = await asyncio.gather(*[_run_branch(i, b) for i, b in enumerate(branches)])
            by_id = {item["branch_id"]: item for item in branch_results}

            if selected_branch is None:
                selected_branch = branch_results[0]["branch_id"]

            selected_branch = str(selected_branch)
            selected_payload = by_id.get(selected_branch)
            if selected_payload is None:
                raise RuntimeError(f"Fork requested at node {node.id} but selected branch is invalid: {selected_branch}")

            state_patch = selected_payload.get("state_patch")
            if isinstance(state_patch, dict) and state_patch:
                self.state.data.update(state_patch)

            return {
                "human_review": "fork_selected",
                "human_review_node": node.id,
                "selected_branch": selected_branch,
                "fork_results": branch_results,
            }

        raise RuntimeError(f"Unsupported human review decision at node {node.id}: {decision}")

    def _evaluate_contract_check(self, check: ContractCheck) -> bool:
        check_type = check.type
        params = check.params

        if check_type == "file_exists":
            path = params.get("path")
            return bool(path and Path(path).exists())

        if check_type == "function_exists":
            func_name = params.get("function_name")
            content = params.get("content")
            if content is None and params.get("path"):
                try:
                    content = Path(params["path"]).read_text(encoding="utf-8")
                except Exception:
                    return False
            if not func_name or not isinstance(content, str):
                return False
            return f"def {func_name}(" in content

        if check_type == "tests_pass":
            key = params.get("state_key", "tests_passed")
            return bool(self.state.data.get(key, False))

        if check_type == "no_new_vulnerabilities":
            key = params.get("state_key", "new_vulnerabilities")
            return int(self.state.data.get(key, 0) or 0) == 0

        if check_type == "custom":
            key = params.get("state_key")
            expected = params.get("equals", True)
            if key is None:
                return False
            return self.state.data.get(key) == expected

        return False

    def _run_rollback(self, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        executed: List[Dict[str, Any]] = []
        for action in actions:
            action_type = action.get("type")
            if action_type == "set_state":
                key = action.get("key")
                if key is not None:
                    self.state.data[key] = action.get("value")
                    executed.append({"type": action_type, "key": key})
            elif action_type == "remove_state":
                key = action.get("key")
                if key in self.state.data:
                    self.state.data.pop(key, None)
                    executed.append({"type": action_type, "key": key})

        self.state.data["rollback_actions"] = executed
        return {"count": len(executed), "actions": executed}

    def _append_step_log(
        self,
        *,
        step_id: str,
        node: WorkflowNode,
        status: str,
        started_at: float,
        output: Any,
    ) -> None:
        duration_ms = int((time.perf_counter() - started_at) * 1000)
        log_entry = {
            "step_id": step_id,
            "node_id": node.id,
            "node_type": node.type,
            "status": status,
            "duration_ms": duration_ms,
            "agent_used": node.agent,
            "output": output,
        }
        self.state.data.setdefault("step_logs", []).append(log_entry)

        tokens_used = 0
        cost_usd = 0.0
        if isinstance(output, dict):
            tokens_used = int(output.get("tokens_used", 0) or 0)
            cost_usd = float(output.get("cost_usd", 0.0) or 0.0)

        ObservabilityService.record_node_span(
            workflow_id=self.graph.id,
            trace_id=str(self.state.data.get("trace_id", "")),
            step_id=step_id,
            node_id=node.id,
            node_type=node.type,
            status=status,
            duration_ms=duration_ms,
            tokens_used=tokens_used,
            cost_usd=cost_usd,
        )

    def _get_budget(self) -> Dict[str, Any]:
        runtime_budget = self.state.data.get("budget")
        if isinstance(runtime_budget, dict):
            return runtime_budget
        schema_budget = self.graph.state_schema.get("budget", {}) if isinstance(self.graph.state_schema, dict) else {}
        return schema_budget if isinstance(schema_budget, dict) else {}

    def _update_budget_counters(self, output: Any) -> None:
        counters = self.state.data.setdefault("budget_counters", {"steps": 0, "tokens": 0, "cost_usd": 0.0})
        counters["steps"] = int(counters.get("steps", 0)) + 1
        if isinstance(output, dict):
            counters["tokens"] = int(counters.get("tokens", 0)) + int(output.get("tokens_used", 0) or 0)
            counters["cost_usd"] = float(counters.get("cost_usd", 0.0)) + float(output.get("cost_usd", 0.0) or 0.0)

    def _check_workflow_timeout(self) -> Optional[str]:
        if not self.workflow_timeout_seconds or self.workflow_timeout_seconds <= 0:
            return None
        if self._execution_started_at is None:
            return None
        elapsed = time.perf_counter() - self._execution_started_at
        if elapsed > self.workflow_timeout_seconds:
            return "workflow_timeout_exceeded"
        return None

    def _check_budget_before_step(self) -> Optional[str]:
        budget = self._get_budget()
        counters = self.state.data.get("budget_counters", {})
        max_steps = budget.get("max_steps")
        if isinstance(max_steps, int) and max_steps >= 0:
            if int(counters.get("steps", 0)) >= max_steps:
                return "budget_max_steps_exceeded"
        return None

    def _check_budget_after_step(self) -> Optional[str]:
        budget = self._get_budget()
        counters = self.state.data.get("budget_counters", {})

        max_tokens = budget.get("max_tokens")
        if isinstance(max_tokens, int) and max_tokens >= 0 and int(counters.get("tokens", 0)) > max_tokens:
            return "budget_max_tokens_exceeded"

        max_cost = budget.get("max_cost_usd")
        if isinstance(max_cost, (int, float)) and max_cost >= 0 and float(counters.get("cost_usd", 0.0)) > float(max_cost):
            return "budget_max_cost_exceeded"

        max_duration = budget.get("max_duration_seconds")
        if isinstance(max_duration, int) and max_duration >= 0 and self._execution_started_at is not None:
            elapsed = time.perf_counter() - self._execution_started_at
            if elapsed > max_duration:
                return "budget_max_duration_exceeded"

        return None

    def _handle_budget_exceeded(self, reason: str) -> None:
        budget = self._get_budget()
        on_exceed = str(budget.get("on_exceed", "pause")).lower().strip()
        if on_exceed == "abort":
            self.state.data["execution_paused"] = False
            self.state.data["aborted_reason"] = reason
            return

        self.state.data["execution_paused"] = True
        self.state.data["pause_reason"] = reason

    def resume_from_checkpoint(self, checkpoint_index: int = -1) -> Optional[str]:
        if not self.state.checkpoints:
            raise ValueError("No checkpoints available to resume from")

        checkpoint = self.state.checkpoints[checkpoint_index]
        self.state.data = dict(checkpoint.state)
        self.state.data["resumed_from_checkpoint"] = {
            "node_id": checkpoint.node_id,
            "checkpoint_index": checkpoint_index,
        }
        self.state.data["execution_paused"] = False

        next_node = self._get_next_node(checkpoint.node_id, checkpoint.output)
        self._resume_from_node_id = next_node
        return next_node

    def _serialize_graph(self) -> Dict[str, Any]:
        return {
            "id": self.graph.id,
            "nodes": [
                {
                    "id": node.id,
                    "type": node.type,
                    "config": node.config,
                    "agent": node.agent,
                    "timeout": node.timeout,
                    "retries": node.retries,
                }
                for node in self.graph.nodes
            ],
            "edges": [
                {
                    "from": edge.from_node,
                    "to": edge.to_node,
                    "condition": edge.condition,
                }
                for edge in self.graph.edges
            ],
            "state_schema": self.graph.state_schema,
        }

    def _persist_checkpoint(self, checkpoint: WorkflowCheckpoint) -> None:
        if not (self.persist_checkpoints and self.storage):
            return

        try:
            self.storage.save_checkpoint(
                workflow_id=self.graph.id,
                node_id=checkpoint.node_id,
                state=checkpoint.state,
                output=checkpoint.output,
                status=checkpoint.status,
            )
        except Exception as exc:
            logger.error("Failed to persist checkpoint for node=%s: %s", checkpoint.node_id, exc)

    async def _execute_node(self, node: WorkflowNode, state: Optional[Dict[str, Any]] = None) -> Any:
        # Placeholder for actual node execution logic
        # In a real implementation, this would dispatch to specific services
        await asyncio.sleep(0.1) # Simulate work
        return {"status": "ok"}

    def _get_next_node(self, node_id: str, output: Any) -> Optional[str]:
        edges = self._edges_from.get(node_id, [])
        if not edges:
            return None
        
        for edge in edges:
            if edge.condition:
                # Simple condition evaluation (MVP: check if key in output or simple eval)
                if self._evaluate_condition(edge.condition, output):
                    return edge.to_node
            else:
                # First edge without condition is the default
                return edge.to_node
                
        return None

    def _evaluate_condition(self, condition: str, output: Any) -> bool:
        """Very basic condition evaluator for MVP."""
        try:
            # Dangerous in prod, but for MVP we might use simple string matching
            # or check if a flag exists in output
            if isinstance(output, dict):
                return bool(output.get(condition))
            return False
        except Exception:
            return False

    @staticmethod
    def _parse_iso_ts(value: Any) -> Optional[datetime]:
        if not value:
            return None
        try:
            txt = str(value)
            if txt.endswith("Z"):
                txt = txt[:-1] + "+00:00"
            return datetime.fromisoformat(txt).astimezone(timezone.utc)
        except Exception:
            return None
