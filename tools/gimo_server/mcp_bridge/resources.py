import logging
import httpx
from mcp.server.fastmcp import FastMCP
from mcp.types import PromptMessage, TextContent

logger = logging.getLogger("mcp_bridge.resources")
BACKEND_URL = "http://127.0.0.1:9325"

async def _fetch_resource(path: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{BACKEND_URL}{path}")
            if resp.status_code == 200:
                import json
                data = resp.json()
                return json.dumps(data, indent=2)
            else:
                return f"Error: HTTP {resp.status_code} - {resp.text}"
    except Exception as e:
        return f"Error fetching {path}: {e}"

def register_resources(mcp: FastMCP):
    @mcp.resource("config://app")
    async def get_app_config() -> str:
        """Global GIMO Application Configuration"""
        return await _fetch_resource("/ops/config")

    @mcp.resource("runs://recent")
    async def get_recent_runs() -> str:
        """List of 20 most recent GIMO Ops Runs"""
        return await _fetch_resource("/ops/runs?limit=20")

    @mcp.resource("drafts://recent")
    async def get_recent_drafts() -> str:
        """List of 20 most recent unapproved plan Drafts"""
        return await _fetch_resource("/ops/drafts?limit=20")

    @mcp.resource("metrics://roi")
    async def get_roi_metrics() -> str:
        """Return on Investment (ROI) metrics for sub-agents"""
        return await _fetch_resource("/ui/stats/roi")

    @mcp.resource("metrics://cascade")
    async def get_cascade_metrics() -> str:
        """Model delegation cascade statistics"""
        return await _fetch_resource("/ui/stats/cascade")

    @mcp.resource("metrics://cache")
    async def get_cache_metrics() -> str:
        """Semantic Cache hit/miss metrics"""
        return await _fetch_resource("/ui/stats/cache")

    @mcp.resource("security://trust")
    async def get_trust_dashboard() -> str:
        """Agent Trust and Circuit Breaker statuses"""
        return await _fetch_resource("/ui/trust")

    @mcp.resource("audit://log")
    async def get_audit_log() -> str:
        """Recent security audit logs"""
        return await _fetch_resource("/ui/audit?limit=50")

    logger.info("Registered 8 MCP Resources")

def register_prompts(mcp: FastMCP):
    @mcp.prompt("plan_creation")
    def prompt_plan_creation(goal: str) -> list[PromptMessage]:
        """A guided workflow to create a modular multi-agent plan."""
        return [
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text=f"Please create a comprehensive multi-agent plan to achieve the following goal: {goal}.\n"
                         "1. Use 'post_ops_drafts' tool to propose the plan.\n"
                         "2. The plan must include a Mermaid graph.\n"
                         "3. Wait for my approval before executing."
                )
            )
        ]

    @mcp.prompt("debug_run")
    def prompt_debug_run(run_id: str) -> list[PromptMessage]:
        """Analyze a failed or stuck GIMO Run."""
        return [
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text=f"The run with ID {run_id} seems to have failed or hanging. Please:\n"
                         f"1. Check the run status using 'get_ops_runs_run_id'.\n"
                         f"2. Look for error messages in the run logs.\n"
                         f"3. Propose a fix or use 'put_ops_runs_run_id_status' to manually override it."
                )
            )
        ]

    @mcp.prompt("optimize_cost")
    def prompt_optimize_cost() -> list[PromptMessage]:
        """Review recent metrics and suggest cost optimizations."""
        return [
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text="Review the 'metrics://cascade' and 'metrics://cache' resources.\n"
                         "Based on the data, suggest configuration changes to `provider_service.py` or new cache strategies to reduce LLM API costs."
                )
            )
        ]

    @mcp.prompt("security_audit")
    def prompt_security_audit() -> list[PromptMessage]:
        """Review security trust levels and find anomalous agents."""
        return [
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text="Examine the 'security://trust' resource.\n"
                         "Identify any agents that have low trust scores or triggered the circuit breaker. Provide a short incident report."
                )
            )
        ]

    @mcp.prompt("onboard_agent")
    def prompt_onboard_agent(task_description: str) -> list[PromptMessage]:
        """Draft a valid system prompt for a new specialized sub-agent."""
        return [
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text=f"I want to create a new specialized GIMO sub-agent to handle this task: '{task_description}'.\n"
                         "Please draft its system prompt following the GIMO persona format (Modular, Disruptive) and suggest the best model preference."
                )
            )
        ]

    logger.info("Registered 5 MCP Prompts")
