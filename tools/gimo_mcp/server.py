"""
Proxy module to maintain compatibility with legacy imports while 
redirecting to the canonical GIMO MCP server implementation.
"""
from tools.gimo_server.mcp_server import mcp, gimo_get_status, gimo_list_agents, gimo_run_task, gimo_get_task_status

__all__ = ["mcp", "gimo_get_status", "gimo_list_agents", "gimo_run_task", "gimo_get_task_status"]

if __name__ == "__main__":
    import asyncio
    import sys
    import logging
    from tools.gimo_server.mcp_server import _startup_and_run

    logging.basicConfig(level=logging.INFO, stream=sys.stderr)
    asyncio.run(_startup_and_run())
