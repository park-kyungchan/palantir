"""
ODA PAI Tools - Tool Categories
===============================

Defines the ToolCategory enum that classifies Claude Code tools.
Tool categories determine access control, sandboxing behavior,
and risk levels for each tool type.

Categories:
    FILE_READ     - Read-only file operations (Read, Glob, Grep)
    FILE_WRITE    - File modification operations (Write, Edit)
    EXECUTION     - Code/command execution (Bash, Task)
    SEARCH        - Web/external search (WebSearch, WebFetch)
    COMMUNICATION - User interaction (AskUserQuestion)
    MEMORY        - State tracking (TodoWrite)
    MCP           - MCP server tools
    ANALYSIS      - Code analysis tools
    VALIDATION    - Schema validation tools

Phase: AIP-02 Tool Category System
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, Set


class ToolCategory(str, Enum):
    """
    Categories of Claude Code tools.

    Each category defines operational boundaries and risk characteristics:

    - FILE_READ: Safe read operations, no side effects
    - FILE_WRITE: Modifies filesystem, requires caution
    - EXECUTION: Runs code/commands, highest risk level
    - SEARCH: External information retrieval
    - COMMUNICATION: User interaction channels
    - MEMORY: Internal state management
    - MCP: Model Context Protocol extensions
    - ANALYSIS: Code inspection without modification
    - VALIDATION: Schema and type checking
    """

    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    EXECUTION = "execution"
    SEARCH = "search"
    COMMUNICATION = "communication"
    MEMORY = "memory"
    MCP = "mcp"
    ANALYSIS = "analysis"
    VALIDATION = "validation"

    @property
    def is_read_only(self) -> bool:
        """
        Check if this category contains only read-only operations.

        Read-only categories have no side effects and are safe
        to execute without additional approval.

        Returns:
            True if the category is read-only
        """
        read_only_categories: Set[ToolCategory] = {
            ToolCategory.FILE_READ,
            ToolCategory.SEARCH,
            ToolCategory.ANALYSIS,
        }
        return self in read_only_categories

    @property
    def is_hazardous(self) -> bool:
        """
        Check if this category contains potentially hazardous operations.

        Hazardous categories can modify state, execute code,
        or have other side effects requiring caution.

        Returns:
            True if the category is hazardous
        """
        hazardous_categories: Set[ToolCategory] = {
            ToolCategory.EXECUTION,
            ToolCategory.FILE_WRITE,
        }
        return self in hazardous_categories

    @property
    def allowed_in_sandbox(self) -> bool:
        """
        Check if this category is allowed in sandboxed execution.

        Sandboxed execution restricts certain operations for safety.

        Returns:
            True if the category is allowed in sandbox mode
        """
        sandbox_allowed: Set[ToolCategory] = {
            ToolCategory.FILE_READ,
            ToolCategory.SEARCH,
            ToolCategory.ANALYSIS,
            ToolCategory.VALIDATION,
            ToolCategory.MEMORY,
            ToolCategory.COMMUNICATION,
        }
        return self in sandbox_allowed

    @property
    def description(self) -> str:
        """
        Human-readable description of this category.

        Returns:
            Description string
        """
        descriptions: Dict[ToolCategory, str] = {
            ToolCategory.FILE_READ: "Read-only file operations",
            ToolCategory.FILE_WRITE: "File modification operations",
            ToolCategory.EXECUTION: "Code and command execution",
            ToolCategory.SEARCH: "Web and external search",
            ToolCategory.COMMUNICATION: "User interaction",
            ToolCategory.MEMORY: "State tracking and persistence",
            ToolCategory.MCP: "Model Context Protocol tools",
            ToolCategory.ANALYSIS: "Code analysis and inspection",
            ToolCategory.VALIDATION: "Schema and type validation",
        }
        return descriptions.get(self, "Unknown category")

    @property
    def risk_level(self) -> int:
        """
        Numeric risk level for this category (0-10).

        Higher values indicate greater risk:
        - 0-2: Safe, no side effects
        - 3-5: Moderate, may affect state
        - 6-8: High, modifies filesystem/executes code
        - 9-10: Critical, requires explicit approval

        Returns:
            Risk level integer (0-10)
        """
        risk_levels: Dict[ToolCategory, int] = {
            ToolCategory.FILE_READ: 1,
            ToolCategory.SEARCH: 2,
            ToolCategory.ANALYSIS: 1,
            ToolCategory.VALIDATION: 1,
            ToolCategory.MEMORY: 2,
            ToolCategory.COMMUNICATION: 3,
            ToolCategory.MCP: 5,
            ToolCategory.FILE_WRITE: 7,
            ToolCategory.EXECUTION: 9,
        }
        return risk_levels.get(self, 5)

    @classmethod
    def from_string(cls, value: str) -> "ToolCategory":
        """
        Parse a tool category from a string.

        Args:
            value: String representation (case-insensitive)

        Returns:
            The corresponding ToolCategory

        Raises:
            ValueError: If the value is not a valid tool category
        """
        try:
            return cls(value.lower())
        except ValueError:
            valid_values = [c.value for c in cls]
            raise ValueError(
                f"Invalid tool category: '{value}'. "
                f"Valid values: {valid_values}"
            )

    @classmethod
    def read_only_categories(cls) -> Set["ToolCategory"]:
        """
        Get all read-only categories.

        Returns:
            Set of read-only ToolCategory values
        """
        return {c for c in cls if c.is_read_only}

    @classmethod
    def hazardous_categories(cls) -> Set["ToolCategory"]:
        """
        Get all hazardous categories.

        Returns:
            Set of hazardous ToolCategory values
        """
        return {c for c in cls if c.is_hazardous}

    @classmethod
    def sandbox_allowed_categories(cls) -> Set["ToolCategory"]:
        """
        Get all categories allowed in sandbox mode.

        Returns:
            Set of sandbox-allowed ToolCategory values
        """
        return {c for c in cls if c.allowed_in_sandbox}


# Category to default tools mapping (for reference)
CATEGORY_DEFAULT_TOOLS: Dict[ToolCategory, Set[str]] = {
    ToolCategory.FILE_READ: {"Read", "Glob", "Grep"},
    ToolCategory.FILE_WRITE: {"Write", "Edit", "NotebookEdit"},
    ToolCategory.EXECUTION: {"Bash", "Task"},
    ToolCategory.SEARCH: {"WebSearch", "WebFetch"},
    ToolCategory.COMMUNICATION: {"AskUserQuestion"},
    ToolCategory.MEMORY: {"TodoWrite"},
    ToolCategory.MCP: set(),  # Dynamically discovered
    ToolCategory.ANALYSIS: set(),  # Code analysis tools
    ToolCategory.VALIDATION: set(),  # Schema validation tools
}
