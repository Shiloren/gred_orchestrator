"""Legacy entry point for GIMO MCP Server.

Redirects to ``mcp_bridge`` while remaining resilient when the optional
``mcp`` dependency is not installed (common in minimal/test environments).
"""

from __future__ import annotations

import logging

logger = logging.getLogger("orchestrator")

try:
    from tools.gimo_server.mcp_bridge.server import mcp, main
except ModuleNotFoundError as exc:
    if exc.name == "mcp":
        mcp = None  # type: ignore[assignment]

        def main() -> None:
            raise RuntimeError(
                "MCP server dependency missing: install package 'mcp' to run MCP features."
            )

        logger.warning("MCP features disabled: optional dependency 'mcp' is not installed")
    else:
        raise

if __name__ == "__main__":
    main()
