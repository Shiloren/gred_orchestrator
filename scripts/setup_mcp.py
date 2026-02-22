#!/usr/bin/env python3
"""
GIMO MCP Auto-Setup Script.

Registers the GIMO MCP server in the user's Antigravity/Gemini MCP configuration
so it starts automatically when the IDE opens.

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
from typing import Any, Dict, Optional


# ─── Config Paths ────────────────────────────────────────────────────────────

def _find_mcp_config() -> Optional[Path]:
    """Locate the MCP config file across known IDE integrations."""
    home = Path.home()
    candidates = [
        home / ".gemini" / "antigravity" / "mcp_config.json",  # Antigravity
        home / ".gemini" / "mcp_config.json",                   # Gemini direct
        home / ".cursor" / "mcp.json",                          # Cursor
        home / ".vscode" / "mcp.json",                          # VS Code
        home / ".config" / "mcp" / "servers.json",              # XDG Linux
    ]
    for p in candidates:
        if p.exists():
            return p
    # Default: create in Antigravity location
    default = home / ".gemini" / "antigravity" / "mcp_config.json"
    return default


def _get_repo_root() -> Path:
    """Get the GIMO repository root (parent of scripts/)."""
    return Path(__file__).resolve().parent.parent


# ─── GIMO Server Entry ──────────────────────────────────────────────────────

def _build_gimo_entry(repo_root: Path) -> Dict[str, Any]:
    """Build the GIMO MCP server config entry."""
    return {
        "command": "python",
        "args": ["-m", "tools.gimo_mcp.server"],
        "cwd": str(repo_root),
        "env": {
            "PYTHONIOENCODING": "utf-8",
            "ORCH_REPO_ROOT": str(repo_root),
        },
    }


# ─── Operations ──────────────────────────────────────────────────────────────

def install(config_path: Path, repo_root: Path) -> bool:
    """Add or update the GIMO entry in the MCP config."""
    config: Dict[str, Any] = {}
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            print(f"⚠  Could not parse {config_path} — creating fresh config.")

    servers = config.setdefault("mcpServers", {})

    if "gimo" in servers:
        print(f"[RELOAD] Updating existing GIMO entry in {config_path}")
    else:
        print(f"[OK] Adding GIMO MCP server to {config_path}")

    servers["gimo"] = _build_gimo_entry(repo_root)

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"   Command: python -m tools.gimo_mcp.server")
    print(f"   CWD:     {repo_root}")
    print(f"\n[DONE] Restart your IDE/editor to activate GIMO MCP.")
    return True


def check(config_path: Path) -> bool:
    """Verify GIMO is registered in the MCP config."""
    if not config_path.exists():
        print(f"❌ No MCP config found at {config_path}")
        return False

    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(f"❌ Cannot read {config_path}: {e}")
        return False

    servers = config.get("mcpServers", {})
    if "gimo" not in servers:
        print(f"❌ GIMO not registered in {config_path}")
        print(f"   Run: python scripts/setup_mcp.py")
        return False

    entry = servers["gimo"]
    print(f"✅ GIMO MCP server is registered in {config_path}")
    print(f"   Command: {entry.get('command')} {' '.join(entry.get('args', []))}")
    print(f"   CWD:     {entry.get('cwd', 'N/A')}")
    return True


def remove(config_path: Path) -> bool:
    """Remove GIMO from the MCP config."""
    if not config_path.exists():
        print(f"⚠  No MCP config found at {config_path}")
        return True

    config = json.loads(config_path.read_text(encoding="utf-8"))
    servers = config.get("mcpServers", {})

    if "gimo" not in servers:
        print(f"ℹ  GIMO was not registered in {config_path}")
        return True

    del servers["gimo"]
    config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"🗑  GIMO removed from {config_path}")
    return True


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    config_path = _find_mcp_config()
    repo_root = _get_repo_root()

    if "--check" in sys.argv:
        ok = check(config_path)
        sys.exit(0 if ok else 1)
    elif "--remove" in sys.argv:
        remove(config_path)
    else:
        install(config_path, repo_root)


if __name__ == "__main__":
    main()
