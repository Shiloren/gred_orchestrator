from __future__ import annotations

import logging
import os
import fnmatch
from pathlib import Path
from typing import Any, Dict, List, Optional
from ...services.file_service import FileService

logger = logging.getLogger(__name__)

class ToolExecutionResult(Dict[str, Any]):
    def __init__(self, status: str, message: str, data: Optional[Dict[str, Any]] = None):
        super().__init__({"status": status, "message": message, "data": data or {}})

class ToolExecutor:
    """
    Handles execution of artifact tools with safety checks.
    """
    def __init__(self, workspace_root: str, policy: Optional[Dict[str, Any]] = None, token: str = "SYSTEM"):
        self.workspace_root = workspace_root
        self.policy = policy or {}
        self.token = token

    def _is_path_allowed(self, full_path: str) -> bool:
        allowed_paths = []
        if hasattr(self.policy, "allowed_paths"):
            allowed_paths = list(getattr(self.policy, "allowed_paths") or [])
        elif isinstance(self.policy, dict):
            allowed_paths = list(self.policy.get("allowed_paths") or [])
        if not allowed_paths or "*" in allowed_paths:
            return True

        normalized = full_path.replace("\\", "/")
        rel_normalized = normalized
        try:
            rel_normalized = os.path.relpath(full_path, self.workspace_root).replace("\\", "/")
        except Exception:
            rel_normalized = normalized
        for allowed in allowed_paths:
            allowed_norm = str(allowed).replace("\\", "/")
            if (
                normalized == allowed_norm
                or normalized.startswith(f"{allowed_norm}/")
                or rel_normalized == allowed_norm
                or rel_normalized.startswith(f"{allowed_norm}/")
                or fnmatch.fnmatch(normalized, allowed_norm)
                or fnmatch.fnmatch(rel_normalized, allowed_norm)
            ):
                return True
        return False


    async def execute_tool_call(self, name: str, arguments: Dict[str, Any]) -> ToolExecutionResult:
        """Routes a tool call to the appropriate internal handler."""
        handler = getattr(self, f"handle_{name}", None)
        if not handler:
            return ToolExecutionResult("error", f"Unknown tool: {name}")
        
        try:
            return await handler(arguments)
        except Exception as e:
            logger.exception(f"Error executing tool {name}")
            return ToolExecutionResult("error", f"Internal error in {name}: {str(e)}")

    async def handle_write_file(self, args: Dict[str, Any]) -> ToolExecutionResult:
        path = args.get("path")
        content = args.get("content", "")
        if not path:
            return ToolExecutionResult("error", "Missing 'path' argument")
            
        full_path = self._to_abs_path(path)
        if not self._is_path_allowed(full_path):
            return ToolExecutionResult("error", f"Path not allowed by runtime policy: {path}")
        logger.info(f"Writing {len(content)} characters to {full_path}")
        FileService.write_file(Path(full_path), str(content), self.token)
        return ToolExecutionResult("success", f"File written: {path}", {"path": full_path, "size": len(content)})


    async def handle_patch_file(self, args: Dict[str, Any]) -> ToolExecutionResult:
        path = args.get("path")
        diff = args.get("diff")
        if not path or not diff:
            return ToolExecutionResult("error", "Missing 'path' or 'diff' argument")
        
        full_path = self._to_abs_path(path)
        if not self._is_path_allowed(full_path):
            return ToolExecutionResult("error", f"Path not allowed by runtime policy: {path}")
        FileService.patch_file(Path(full_path), diff=str(diff), token=self.token)
        return ToolExecutionResult("success", f"File patched: {path}")

    async def handle_create_dir(self, args: Dict[str, Any]) -> ToolExecutionResult:
        path = args.get("path")
        if not path:
            return ToolExecutionResult("error", "Missing 'path' argument")
        
        full_path = self._to_abs_path(path)
        if not self._is_path_allowed(full_path):
            return ToolExecutionResult("error", f"Path not allowed by runtime policy: {path}")
        FileService.create_dir(Path(full_path), self.token)
        return ToolExecutionResult("success", f"Directory created: {path}")


    def _to_abs_path(self, path: str) -> str:
        if os.path.isabs(path):
            return path
        return os.path.normpath(os.path.join(self.workspace_root, path))
