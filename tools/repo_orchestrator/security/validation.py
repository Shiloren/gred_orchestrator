import os
import re
import json
import time
from pathlib import Path
from typing import Optional
from fastapi import HTTPException
from tools.repo_orchestrator.config import (
    REPO_REGISTRY_PATH,
    ALLOWLIST_PATH,
    ALLOWLIST_TTL_SECONDS,
)

from tools.repo_orchestrator.services.registry_service import RegistryService

def get_active_repo_dir() -> Path:
    # Proxy to the new service for backward compatibility during refactor if needed, 
    # but best to replace usage.
    # However, keeping it as a wrapper for now to minimize import breakage in other files 
    # that might trust this module provided the imports are updated.
    # actually, I will remove them and update importers.
    return RegistryService.get_active_repo_dir()


def _normalize_path(path_str: str, base_dir: Path) -> Optional[Path]:
    try:
        # Check for null bytes
        if '\0' in path_str:
            return None
        
        # Check for Windows reserved names
        reserved_names = {'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 
                         'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 
                         'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'}
        path_upper = path_str.upper()
        if any(name in path_upper for name in reserved_names):
            return None
        
        requested = Path(path_str)
        if requested.is_absolute():
            resolved = requested.resolve()
        else:
            resolved = (base_dir / requested).resolve()
        
        # Ensure resolved path is within base_dir
        base_resolved = base_dir.resolve()
        try:
            resolved.relative_to(base_resolved)
        except ValueError:
            # Path is not relative to base_dir, it's outside
            return None
            
        return resolved
    except Exception:
        return None

def validate_path(requested_path: str, base_dir: Path) -> Path:
    target = _normalize_path(requested_path, base_dir)
    if not target:
        raise HTTPException(status_code=403, detail="Access denied: Path traversal detected or invalid path.")
    return target


def get_allowed_paths(base_dir: Path) -> set[Path]:
    """Load allowed paths from allowlist.json with TTL check."""
    if not ALLOWLIST_PATH.exists():
        return set()
    try:
        data = json.loads(ALLOWLIST_PATH.read_text(encoding="utf-8"))
        timestamp = data.get("timestamp", 0)
        if time.time() - timestamp > ALLOWLIST_TTL_SECONDS:
            return set()
        return {base_dir / p for p in data.get("paths", [])}
    except Exception:
        return set()


def serialize_allowlist(paths: set[Path]) -> list[dict]:
    """Convert set of paths to serializable list for API response."""
    result = []
    for p in paths:
        try:
            result.append({
                "path": str(p),
                "type": "file" if p.is_file() else "dir"
            })
        except Exception:
            continue
    return result

