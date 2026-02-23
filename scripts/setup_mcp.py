#!/usr/bin/env python3
"""
GIMO MCP Auto-Setup Script.

Registers the GIMO MCP server in the user's various IDE MCP configurations
(Claude Desktop, Cline, Windsurf, Continue, Antigravity)
so it starts automatically.

Usage:
    python scripts/setup_mcp.py           # Auto-detect and install
    python scripts/setup_mcp.py --check   # Verify installation without modifying
    python scripts/setup_mcp.py --remove  # Unregister GIMO from MCP config
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List


# ─── Config Paths ────────────────────────────────────────────────────────────

def _get_platform_paths() -> List[Path]:
    """Locate MCP config files across known IDE integrations."""
    home = Path.home()
    
    # System dependent APPDATA / paths
    if sys.platform == "win32":
        app_data = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming"))
        claude_path = app_data / "Claude" / "claude_desktop_config.json"
        cline_path = app_data / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json"
        cursor_path = app_data / "Cursor" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json"
    elif sys.platform == "darwin":
        app_data = home / "Library" / "Application Support"
        claude_path = app_data / "Claude" / "claude_desktop_config.json"
        cline_path = app_data / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json"
        cursor_path = app_data / "Cursor" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json"
    else:  # Linux
        app_data = home / ".config"
        claude_path = app_data / "Claude" / "claude_desktop_config.json"
        cline_path = app_data / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json"
        cursor_path = app_data / "Cursor" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json"

    candidates = [
        home / ".gemini" / "antigravity" / "mcp_config.json",  # Antigravity
        home / ".gemini" / "mcp_config.json",                   # Gemini direct
        home / ".codeium" / "windsurf" / "mcp_config.json",     # Windsurf
        claude_path,                                            # Claude Desktop
        cline_path,                                             # Cline (VS Code)
        cursor_path,                                            # Cline (Cursor)
    ]
    
    return [p for p in candidates if p.exists() or p.parent.exists()]


def _get_repo_root() -> Path:
    """Get the GIMO repository root (parent of scripts/)."""
    return Path(__file__).resolve().parent.parent


# ─── GIMO Server Entry ──────────────────────────────────────────────────────

def _build_gimo_entry(repo_root: Path) -> Dict[str, Any]:
    """Build the GIMO MCP server config entry."""
    # Note: Use the new bridge package entry point
    return {
        "command": "python",
        "args": ["-m", "tools.gimo_server.mcp_bridge.server"],
        "cwd": str(repo_root),
        "env": {
            "PYTHONIOENCODING": "utf-8",
            "ORCH_REPO_ROOT": str(repo_root),
        },
    }


# ─── Operations ──────────────────────────────────────────────────────────────

def install(repo_root: Path) -> bool:
    """Add or update the GIMO entry in all found MCP configs."""
    paths = _get_platform_paths()
    if not paths:
        # Default to antigravity if no dirs exist
        paths = [Path.home() / ".gemini" / "antigravity" / "mcp_config.json"]

    success_count = 0
    for config_path in paths:
        config: Dict[str, Any] = {}
        if config_path.exists():
            try:
                config = json.loads(config_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                print(f"[WARN] Could not parse {config_path} — creating fresh config.")

        servers = config.setdefault("mcpServers", {})
        if "gimo" in servers:
            print(f"[RELOAD] Updating GIMO in {config_path.name}")
        else:
            print(f"[OK] Adding GIMO to {config_path.name}")

        servers["gimo"] = _build_gimo_entry(repo_root)

        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        success_count += 1
        
    print("\n[OK] Install summary:")
    print(f"   Configs updated: {success_count}")
    print(f"   Command: python -m tools.gimo_server.mcp_bridge.server")
    print(f"   CWD:     {repo_root}")
    
    print("\\n   [CONTINUE / JETBRAINS MANUEL SETUP]")
    print("   If you are using Continue.dev, add this to your ~/.continue/config.json in the mcpServers array:")
    print("   {")
    print('      "name": "gimo",')
    print('      "command": "python",')
    print('      "args": ["-m", "tools.gimo_server.mcp_bridge.server"],')
    print(f'      "env": {{"ORCH_REPO_ROOT": "{str(repo_root)}"}}')
    print("   }")
    print("\\n[DONE] Restart your IDE/editor to activate GIMO MCP.")
    return True


def check() -> bool:
    """Verify GIMO is registered in the MCP config."""
    paths = _get_platform_paths()
    found = False
    
    for config_path in paths:
        if not config_path.exists():
            continue

        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
            servers = config.get("mcpServers", {})
            if "gimo" in servers:
                found = True
                print(f"[OK] GIMO registered in {config_path.name}")
        except:
            pass

    if not found:
        print("[ERROR] GIMO not registered in any known config paths.")
        print("   Run: python scripts/setup_mcp.py")
        return False
    return True


def remove() -> bool:
    """Remove GIMO from the MCP config."""
    paths = _get_platform_paths()
    removed = 0
    
    for config_path in paths:
        if not config_path.exists():
            continue

        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
            servers = config.get("mcpServers", {})
            if "gimo" in servers:
                del servers["gimo"]
                config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                print(f"[REMOVED] GIMO removed from {config_path.name}")
                removed += 1
        except:
            pass

    if removed == 0:
        print("[INFO] GIMO was not registered in any known config.")
    return True


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    repo_root = _get_repo_root()

    if "--check" in sys.argv:
        ok = check()
        sys.exit(0 if ok else 1)
    elif "--remove" in sys.argv:
        remove()
    else:
        install(repo_root)


if __name__ == "__main__":
    main()
