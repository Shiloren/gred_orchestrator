"""
Legacy entry point for GIMO MCP Server.
Redirects to the new mcp_bridge module to maintain backwards compatibility.
"""
from tools.gimo_server.mcp_bridge.server import mcp, main

if __name__ == "__main__":
    main()
