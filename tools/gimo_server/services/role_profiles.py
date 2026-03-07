from __future__ import annotations

from tools.gimo_server.ops_models import RoleProfile


ROLE_PROFILES: dict[str, RoleProfile] = {
    "explorer": RoleProfile(
        tools_allowed={"read_file", "list_dir", "web_search", "grep_search", "core_read_file"},
        capability="read_only",
        trust_tier="t1",
        hitl_required=False,
    ),
    "auditor": RoleProfile(
        tools_allowed={"read_file", "grep_search", "list_dir", "safe_terminal_read", "core_read_file"},
        capability="propose_only",
        trust_tier="t1",
        hitl_required=False,
    ),
    "executor": RoleProfile(
        tools_allowed={
            "write_to_file",
            "replace_file_content",
            "run_command",
            "delete_file",
            "git_commit",
            "core_write_file",
            "core_read_file",
            "shell_exec",
            "file_write",
        },
        capability="execute_safe",
        trust_tier="t2",
        hitl_required=True,
    ),
}


def get_role_profile(role_name: str) -> RoleProfile:
    profile = ROLE_PROFILES.get(role_name)
    if profile is None:
        raise PermissionError(f"unknown role profile '{role_name}'")
    return profile


def assert_tool_allowed(role_name: str, tool: str) -> None:
    profile = get_role_profile(role_name)
    if tool not in profile.tools_allowed:
        raise PermissionError(f"tool '{tool}' not allowed for role profile '{role_name}'")
