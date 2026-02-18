from typing import Any, Dict, List, Optional
import uuid
import logging

from ..ops_models import WorkflowNode, CascadeConfig, CascadeResult, QualityRating
from .provider_service import ProviderService
from .quality_service import QualityService
from .model_router_service import ModelRouterService
from .cost_service import CostService

logger = logging.getLogger("orchestrator.services.cascade")

class CascadeService:
    """Service that manages cascading execution (retries with different models)."""

    def __init__(self, provider_service: ProviderService, model_router: ModelRouterService):
        self.provider_service = provider_service
        self.model_router = model_router

    async def execute_with_cascade(
        self, 
        prompt: str, 
        context: Dict[str, Any], 
        cascade_config: CascadeConfig,
        node_budget: Optional[Dict[str, Any]] = None,
        current_state: Optional[Dict[str, Any]] = None
    ) -> CascadeResult:
        """
        Executes a node with cascading logic if enabled.
        
        Refinement: 
        - Track input/output tokens separately.
        - Check budgets before escalating.
        - Graceful exception handling.
        """
        chain = []
        current_model = context.get("model")
        
        if not current_model:
            current_model = self.model_router._TIERS[1] # Default to haiku

        attempts = 0
        max_attempts = max(1, cascade_config.max_escalations + 1)
        
        final_output = None
        total_cost = 0.0
        total_in = 0
        total_out = 0
        success = False
        
        while attempts < max_attempts:
            attempts += 1
            logger.info("Cascade attempt %s/%s using model %s", attempts, max_attempts, current_model)
            
            # Pass the override model in context
            context["model"] = current_model
            
            try:
                output = await self.provider_service.generate(prompt, context)
                
                # Update counters
                step_cost = float(output.get("cost_usd", 0.0) or 0.0)
                step_in = int(output.get("prompt_tokens", 0) or 0)
                step_out = int(output.get("completion_tokens", 0) or 0)
                
                total_cost += step_cost
                total_in += step_in
                total_out += step_out
                
                # 2. Evaluate
                text_output = str(output.get("content") or output.get("result") or "")
                task_type = context.get("task_type")
                expected_format = context.get("expected_format")
                
                quality: QualityRating = QualityService.analyze_output(
                    text_output, 
                    task_type=task_type, 
                    expected_format=expected_format
                )
                
                chain.append({
                    "attempt": attempts,
                    "model": current_model,
                    "quality_score": quality.score,
                    "alerts": quality.alerts,
                    "input_tokens": step_in,
                    "output_tokens": step_out,
                    "cost_usd": step_cost,
                    "success": quality.score >= cascade_config.quality_threshold
                })
                
                final_output = output
                final_output["quality_rating"] = quality.model_dump()
                final_output["cascade_level"] = attempts - 1
                
                # 3. Decision
                if quality.score >= cascade_config.quality_threshold:
                    logger.info("Quality threshold met (%s >= %s)", quality.score, cascade_config.quality_threshold)
                    success = True
                    break
                else:
                    logger.warning("Low quality output (score %s < %s)", quality.score, cascade_config.quality_threshold)

            except Exception as e:
                logger.error("Cascade attempt %s failed with exception: %s", attempts, e)
                chain.append({
                    "attempt": attempts,
                    "model": current_model,
                    "quality_score": 0,
                    "error": str(e),
                    "success": False
                })
                if final_output is None:
                    final_output = {"error": str(e), "success": False, "cascade_level": attempts - 1}

            if attempts < max_attempts:
                # 4. Before Escalating: Check budget (Safety first)
                if node_budget:
                    max_cost = node_budget.get("max_cost_usd")
                    if max_cost and total_cost >= float(max_cost):
                        logger.warning("Cascade stopped: Next escalation would exceed node budget cost limit (%s)", max_cost)
                        break
                    
                    max_tokens = node_budget.get("max_tokens")
                    if max_tokens and (total_in + total_out) >= int(max_tokens):
                         logger.warning("Cascade stopped: Next escalation would exceed node budget token limit (%s)", max_tokens)
                         break

                # Escalation logic
                next_model = self._get_next_tier(current_model, cascade_config)
                if next_model == current_model:
                    logger.warning("No higher tier available for escalation")
                    break
                current_model = next_model
            else:
                logger.warning("Max cascade attempts reached")

        # Calculate savings
        savings = 0.0
        if success:
            last_step_in = chain[-1]["input_tokens"] if chain else 0
            last_step_out = chain[-1]["output_tokens"] if chain else 0
            
            # Determine the baseline model for comparison (usually the max_tier user would have used)
            # If max_tier isn't specified, use Opus as the standard "expensive" benchmark
            benchmark_model = cascade_config.max_tier if cascade_config.max_tier else "opus"
            
            hypothetical_cost = CostService.calculate_cost(
                benchmark_model, 
                last_step_in, 
                last_step_out
            )
            
            savings = hypothetical_cost - total_cost

        return CascadeResult(
            final_output=final_output,
            cascade_chain=chain,
            total_input_tokens=total_in,
            total_output_tokens=total_out,
            total_tokens=(total_in + total_out),
            total_cost_usd=total_cost,
            savings=savings,
            success=success
        )

    def _get_next_tier(self, current_model: str, config: CascadeConfig) -> str:
        """Finds the next model in the hierarchy, respecting max_tier."""
        tiers = self.model_router._TIERS
        
        # Normalize current_model to match tiers if possible
        normalized_model = str(current_model).lower()
        matched_tier_idx = -1
        
        # Try exact match first
        for i, tier_name in enumerate(tiers):
            if tier_name == normalized_model:
                matched_tier_idx = i
                break
        
        # Fallback to partial match if no exact match found
        if matched_tier_idx == -1:
            for i, tier_name in enumerate(tiers):
                if tier_name in normalized_model:
                    matched_tier_idx = i
                    break
                
        if matched_tier_idx == -1:
            logger.warning("Current model '%s' not found in tiers %s", current_model, tiers)
            return current_model
            
        max_idx = -1
        normalized_max = str(config.max_tier).lower() if config.max_tier else ""
        for i, tier_name in enumerate(tiers):
            if tier_name == normalized_max or tier_name in normalized_max:
                max_idx = i
                break
        
        if max_idx == -1:
             max_idx = len(tiers) - 1
             
        next_idx = min(matched_tier_idx + 1, max_idx)
        return tiers[next_idx]
