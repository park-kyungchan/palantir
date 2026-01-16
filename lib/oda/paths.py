"""
Orion ODA - Centralized Path Management
=======================================
Single Source of Truth for all path configurations.

Resolves: ODA-RISK-004, ODA-RISK-005, ODA-RISK-012, ODA-RISK-016

Environment Variables:
    ORION_WORKSPACE_ROOT: Override workspace root (default: git root or cwd)
    ORION_DB_PATH: Override database path
    ORION_AGENT_ROOT: Override .agent directory location

Priority:
    1. Environment variables (explicit override)
    2. Git repository root detection
    3. Current working directory fallback
"""
import os
import platform
from pathlib import Path
from functools import lru_cache
import tempfile


@lru_cache(maxsize=1)
def _detect_git_root() -> Path | None:
    """Detect git repository root by walking up from cwd."""
    current = Path.cwd()
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    return None


@lru_cache(maxsize=1)
def get_workspace_root() -> Path:
    """
    Get the workspace root directory.

    Priority:
        1. ORION_WORKSPACE_ROOT environment variable
        2. Git repository root (if in a git repo)
        3. Current working directory

    Returns:
        Path to the workspace root
    """
    # 1. Check environment variable first
    if env_root := os.environ.get("ORION_WORKSPACE_ROOT"):
        return Path(env_root).resolve()

    # 2. Try to detect git root
    if git_root := _detect_git_root():
        return git_root

    # 3. Fallback to current directory
    return Path.cwd()


def get_home_dir() -> Path:
    """Get platform-appropriate home directory."""
    if platform.system() == "Windows":
        return Path(os.environ.get("USERPROFILE", Path.home()))
    return Path.home()


# =============================================================================
# Core Path Constants (lazily evaluated via functions for testability)
# =============================================================================

def get_workspace() -> Path:
    """Get workspace root (cached)."""
    return get_workspace_root()


def get_agent_root() -> Path:
    """
    Get .agent directory location.

    Priority:
        1. ORION_AGENT_ROOT environment variable
        2. {workspace}/.agent (project-level)
    """
    if env_root := os.environ.get("ORION_AGENT_ROOT"):
        return Path(env_root).resolve()
    return get_workspace_root() / ".agent"


def get_user_agent_root() -> Path:
    """Get user-level .agent directory (~/.agent)."""
    return get_home_dir() / ".agent"


def get_db_path() -> Path:
    """
    Get database file path.

    Priority:
        1. ORION_DB_PATH environment variable
        2. {agent_root}/tmp/ontology.db (when writable)
        3. {tmpdir}/orion/ontology.db (fallback)
    """
    if env_path := os.environ.get("ORION_DB_PATH"):
        return Path(env_path).resolve()

    agent_db = get_agent_root() / "tmp" / "ontology.db"
    agent_db_dir = agent_db.parent

    if _can_create_file(agent_db_dir):
        return agent_db

    tmp_root = Path(tempfile.gettempdir()) / "orion"
    tmp_root.mkdir(parents=True, exist_ok=True)
    return (tmp_root / "ontology.db").resolve()


@lru_cache(maxsize=64)
def _can_create_file(dir_path: Path) -> bool:
    """
    Return True if a new file can be created in dir_path.

    Some sandboxed environments allow reading existing files under the repo but
    deny creating new filesystem entries in certain directories (e.g., `.agent/tmp`).
    SQLite schema changes require creating journal/WAL files, so we need a safe fallback.
    """
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
    except Exception:
        return False

    try:
        with tempfile.NamedTemporaryFile(dir=dir_path, delete=True):
            return True
    except Exception:
        return False


def get_plans_dir() -> Path:
    """Get plans directory."""
    return get_agent_root() / "plans"


def get_user_plans_dir() -> Path:
    """Get user-level plans directory (~/.agent/plans)."""
    return get_user_agent_root() / "plans"


def get_memory_dir() -> Path:
    """Get semantic memory directory."""
    return get_agent_root() / "memory" / "semantic"


def get_system_facts_path() -> Path:
    """Get system facts file path."""
    return get_agent_root() / "memory" / "system_facts.md"


def get_workflows_dir() -> Path:
    """Get workflows directory."""
    return get_agent_root() / "workflows"


def get_logs_dir() -> Path:
    """Get logs directory."""
    return get_agent_root() / "logs"


def get_archives_dir() -> Path:
    """Get archives directory for old plans."""
    return get_agent_root() / "archives" / "plans"


def get_mcp_registry_path() -> Path:
    """Get MCP registry path."""
    return get_agent_root() / "mcp" / "registry.json"


def get_mcp_audit_log_path() -> Path:
    """Get MCP audit log path."""
    return get_logs_dir() / "mcp_audit.jsonl"


def get_claude_config_path() -> Path:
    """Get .claude.json config path (workspace level)."""
    return get_workspace_root() / ".claude.json"


def get_user_claude_config_path() -> Path:
    """Get user-level .claude.json (home directory)."""
    return get_home_dir() / ".claude.json"


def get_gemini_config_dir() -> Path:
    """Get .gemini configuration directory."""
    return get_workspace_root() / ".gemini"


def get_antigravity_mcp_config_path() -> Path:
    """Get Antigravity MCP configuration path."""
    return get_gemini_config_dir() / "antigravity" / "mcp_config.json"


# =============================================================================
# Convenience: Static-like access for backward compatibility
# These are evaluated at import time - use functions for dynamic behavior
# =============================================================================

# Only create these after first import to avoid circular imports
# Access via functions is preferred for testability

class _LazyPaths:
    """Lazy path accessor for backward compatibility."""

    @property
    def WORKSPACE_ROOT(self) -> Path:
        return get_workspace_root()

    @property
    def AGENT_ROOT(self) -> Path:
        return get_agent_root()

    @property
    def USER_AGENT_ROOT(self) -> Path:
        return get_user_agent_root()

    @property
    def DB_PATH(self) -> Path:
        return get_db_path()

    @property
    def PLANS_DIR(self) -> Path:
        return get_plans_dir()

    @property
    def USER_PLANS_DIR(self) -> Path:
        return get_user_plans_dir()

    @property
    def MEMORY_DIR(self) -> Path:
        return get_memory_dir()

    @property
    def SYSTEM_FACTS_PATH(self) -> Path:
        return get_system_facts_path()

    @property
    def WORKFLOWS_DIR(self) -> Path:
        return get_workflows_dir()

    @property
    def LOGS_DIR(self) -> Path:
        return get_logs_dir()

    @property
    def ARCHIVES_DIR(self) -> Path:
        return get_archives_dir()


# Singleton instance for convenience
paths = _LazyPaths()


# =============================================================================
# Utility Functions
# =============================================================================

def ensure_dir(path: Path) -> Path:
    """Ensure directory exists, create if not."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_parent_dir(path: Path) -> Path:
    """Ensure parent directory of a file path exists."""
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def is_within_workspace(path: Path) -> bool:
    """Check if a path is within the workspace root."""
    try:
        path.resolve().relative_to(get_workspace_root())
        return True
    except ValueError:
        return False


def resolve_relative(path: str | Path) -> Path:
    """Resolve a path relative to workspace root if not absolute."""
    p = Path(path)
    if p.is_absolute():
        return p
    return get_workspace_root() / p
