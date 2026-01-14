"""
Orion ODA v4.0 - Context Injector (Auto Full-Context-Injection System)
======================================================================

Automatic context injection system for skill execution.

Injects relevant reference documents and plan files into skill context
before execution, ensuring each skill has access to required knowledge.

V4.0 FEATURES:
    - REFERENCE_MAP: Skill-to-reference file mapping
    - Plan file auto-loading for resume scenarios
    - Auto-detection of references from user input
    - Integration with SkillRouter for pre-execution injection

Reference: .claude/CLAUDE.md Section 2.4 Progressive Reference System

Version: 1.0.0
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional, Set

from pydantic import BaseModel, Field


# =============================================================================
# CONFIGURATION
# =============================================================================

# Default workspace root - can be overridden via environment variable
WORKSPACE_ROOT = os.environ.get(
    "ODA_WORKSPACE_ROOT",
    "/home/palantir/park-kyungchan/palantir"
)


# =============================================================================
# REFERENCE MAP (Skill -> Reference Files)
# =============================================================================

REFERENCE_MAP: Dict[str, List[str]] = {
    # /ask skill: Prompt engineering and clarification
    "ask": [
        ".claude/references/native-capabilities.md",
    ],

    # /plan skill: 3-stage protocol, delegation patterns
    "plan": [
        ".claude/references/3-stage-protocol.md",
        ".claude/references/delegation-patterns.md",
    ],

    # /audit skill: 3-stage protocol, governance rules
    "audit": [
        ".claude/references/3-stage-protocol.md",
        ".claude/references/governance-rules.md",
    ],

    # /deep-audit skill: Same as audit (RSIL method uses same references)
    "deep-audit": [
        ".claude/references/3-stage-protocol.md",
        ".claude/references/governance-rules.md",
    ],

    # /quality-check skill: Governance and testing
    "quality-check": [
        ".claude/references/governance-rules.md",
    ],

    # /protocol skill: Full 3-stage protocol reference
    "protocol": [
        ".claude/references/3-stage-protocol.md",
        ".claude/references/native-capabilities.md",
    ],

    # /governance skill: Governance rules
    "governance": [
        ".claude/references/governance-rules.md",
    ],

    # /memory skill: PAI integration for memory management
    "memory": [
        ".claude/references/pai-integration.md",
    ],

    # /consolidate skill: Memory and PAI
    "consolidate": [
        ".claude/references/pai-integration.md",
    ],

    # /teleport skill: Native capabilities
    "teleport": [
        ".claude/references/native-capabilities.md",
    ],

    # /init skill: Full setup
    "init": [
        ".claude/references/native-capabilities.md",
        ".claude/references/3-stage-protocol.md",
    ],
}

# Auto-detection keyword-to-reference mapping
AUTO_DETECT_KEYWORDS: Dict[str, List[str]] = {
    # Keywords that trigger 3-stage-protocol reference
    "protocol": [
        ".claude/references/3-stage-protocol.md",
    ],
    "stage": [
        ".claude/references/3-stage-protocol.md",
    ],
    "scan": [
        ".claude/references/3-stage-protocol.md",
    ],
    "trace": [
        ".claude/references/3-stage-protocol.md",
    ],
    "verify": [
        ".claude/references/3-stage-protocol.md",
    ],

    # Keywords that trigger governance reference
    "governance": [
        ".claude/references/governance-rules.md",
    ],
    "proposal": [
        ".claude/references/governance-rules.md",
        ".claude/references/llm-agnostic-architecture.md",
    ],
    "hazardous": [
        ".claude/references/governance-rules.md",
    ],
    "blocked": [
        ".claude/references/governance-rules.md",
    ],

    # Keywords that trigger delegation reference
    "delegate": [
        ".claude/references/delegation-patterns.md",
    ],
    "subagent": [
        ".claude/references/delegation-patterns.md",
    ],
    "task": [
        ".claude/references/delegation-patterns.md",
    ],

    # Keywords that trigger PAI reference
    "pai": [
        ".claude/references/pai-integration.md",
    ],
    "trait": [
        ".claude/references/pai-integration.md",
    ],
    "hook": [
        ".claude/references/pai-integration.md",
    ],

    # Keywords that trigger intent classification reference
    "intent": [
        ".claude/references/intent-classification.md",
    ],
    "classify": [
        ".claude/references/intent-classification.md",
    ],

    # Keywords that trigger orchestration reference
    "orchestrat": [
        ".claude/references/orchestration-flow.md",
    ],
    "workflow": [
        ".claude/references/orchestration-flow.md",
    ],
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class InjectedContext:
    """
    Result of context injection.

    Contains loaded reference content and metadata.
    """
    skill_name: str
    references_loaded: List[str] = field(default_factory=list)
    plan_file: Optional[str] = None
    content: str = ""
    auto_detected: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    errors: List[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        """True if at least some content was loaded."""
        return bool(self.content.strip())

    @property
    def reference_count(self) -> int:
        """Number of references successfully loaded."""
        return len(self.references_loaded)

    def to_prompt_prefix(self) -> str:
        """
        Generate a prompt prefix for skill execution.

        Returns:
            Formatted context string to prepend to skill prompt
        """
        if not self.content:
            return ""

        sections = []

        # Header
        sections.append(f"## Injected Context for /{self.skill_name}")
        sections.append("")

        # Reference list
        if self.references_loaded:
            sections.append("### Loaded References:")
            for ref in self.references_loaded:
                sections.append(f"- `{ref}`")
            sections.append("")

        # Auto-detected references
        if self.auto_detected:
            sections.append("### Auto-Detected References:")
            for ref in self.auto_detected:
                sections.append(f"- `{ref}`")
            sections.append("")

        # Plan file
        if self.plan_file:
            sections.append(f"### Active Plan File: `{self.plan_file}`")
            sections.append("")

        # Content
        sections.append("### Reference Content:")
        sections.append("")
        sections.append(self.content)

        # Footer
        sections.append("")
        sections.append("---")
        sections.append("")

        return "\n".join(sections)


# =============================================================================
# CONTEXT INJECTOR
# =============================================================================

class ContextInjector:
    """
    Auto Full-Context-Injection System.

    Automatically loads and injects relevant reference documents
    into skill context before execution.

    Usage:
        ```python
        injector = ContextInjector()

        # Basic injection for a skill
        context = injector.inject("audit", "코드 리뷰해줘")

        # Get prompt prefix
        prompt = context.to_prompt_prefix() + original_prompt

        # Auto-detect references from user input
        refs = injector.auto_detect_references("protocol stage A를 실행해줘")
        # Returns: ['.claude/references/3-stage-protocol.md']
        ```

    Attributes:
        workspace_root: Root directory for resolving relative paths
        reference_map: Skill-to-reference file mapping
        cache: Cached reference content (optional)
    """

    def __init__(
        self,
        workspace_root: Optional[str] = None,
        reference_map: Optional[Dict[str, List[str]]] = None,
        enable_cache: bool = True,
    ):
        """
        Initialize ContextInjector.

        Args:
            workspace_root: Root directory for paths (default: WORKSPACE_ROOT)
            reference_map: Custom reference map (default: REFERENCE_MAP)
            enable_cache: Whether to cache loaded references
        """
        self.workspace_root = Path(workspace_root or WORKSPACE_ROOT)
        self.reference_map = reference_map or REFERENCE_MAP
        self.enable_cache = enable_cache
        self._cache: Dict[str, str] = {}

    def inject(
        self,
        skill_name: str,
        user_input: str = "",
        include_plan: bool = True,
        plan_slug: Optional[str] = None,
    ) -> InjectedContext:
        """
        Inject context for a skill.

        Loads all relevant references for the skill and optionally
        auto-detects additional references from user input.

        Args:
            skill_name: Name of the skill (e.g., "audit", "plan")
            user_input: User's input text for auto-detection
            include_plan: Whether to include active plan file
            plan_slug: Specific plan file slug to load

        Returns:
            InjectedContext with loaded content
        """
        context = InjectedContext(skill_name=skill_name)
        content_parts: List[str] = []

        # 1. Load skill-specific references
        skill_refs = self.reference_map.get(skill_name, [])
        for ref_path in skill_refs:
            content = self._load_reference(ref_path)
            if content:
                context.references_loaded.append(ref_path)
                content_parts.append(f"<!-- Reference: {ref_path} -->")
                content_parts.append(content)
                content_parts.append("")
            else:
                context.errors.append(f"Failed to load: {ref_path}")

        # 2. Auto-detect additional references from user input
        if user_input:
            auto_refs = self.auto_detect_references(user_input)
            for ref_path in auto_refs:
                if ref_path not in context.references_loaded:
                    content = self._load_reference(ref_path)
                    if content:
                        context.auto_detected.append(ref_path)
                        context.references_loaded.append(ref_path)
                        content_parts.append(f"<!-- Auto-Detected: {ref_path} -->")
                        content_parts.append(content)
                        content_parts.append("")

        # 3. Load plan file for resume support
        if include_plan:
            plan_content = self._load_plan_file(plan_slug)
            if plan_content:
                context.plan_file = plan_slug or self._detect_active_plan()
                content_parts.append("<!-- Active Plan File -->")
                content_parts.append(plan_content)
                content_parts.append("")

        context.content = "\n".join(content_parts)
        return context

    def _load_reference(self, ref_path: str) -> Optional[str]:
        """
        Load a reference file.

        Args:
            ref_path: Relative path to reference file

        Returns:
            File content or None if not found
        """
        # Check cache first
        if self.enable_cache and ref_path in self._cache:
            return self._cache[ref_path]

        full_path = self.workspace_root / ref_path
        try:
            if full_path.exists():
                content = full_path.read_text(encoding="utf-8")
                if self.enable_cache:
                    self._cache[ref_path] = content
                return content
        except Exception:
            pass

        return None

    def _load_plan_file(self, plan_slug: Optional[str] = None) -> Optional[str]:
        """
        Load a plan file for resume support.

        If no slug is provided, attempts to detect the active plan file.

        Args:
            plan_slug: Plan file slug (without extension)

        Returns:
            Plan file content or None if not found
        """
        if plan_slug:
            plan_path = self.workspace_root / ".agent" / "plans" / f"{plan_slug}.md"
            try:
                if plan_path.exists():
                    return plan_path.read_text(encoding="utf-8")
            except Exception:
                pass
            return None

        # Try to detect active plan
        active_plan = self._detect_active_plan()
        if active_plan:
            return self._load_plan_file(active_plan)

        return None

    def _detect_active_plan(self) -> Optional[str]:
        """
        Detect the active plan file.

        Looks for plan files with status: in_progress.

        Returns:
            Plan slug or None if no active plan
        """
        plans_dir = self.workspace_root / ".agent" / "plans"
        if not plans_dir.exists():
            return None

        try:
            for plan_file in plans_dir.glob("*.md"):
                content = plan_file.read_text(encoding="utf-8")
                # Check for active status
                if "Status: in_progress" in content or "status: in_progress" in content:
                    return plan_file.stem
        except Exception:
            pass

        return None

    def auto_detect_references(self, user_input: str) -> List[str]:
        """
        Auto-detect relevant references from user input.

        Scans user input for keywords that map to reference files.

        Args:
            user_input: User's input text

        Returns:
            List of reference file paths
        """
        if not user_input:
            return []

        detected: Set[str] = set()
        user_lower = user_input.lower()

        for keyword, ref_paths in AUTO_DETECT_KEYWORDS.items():
            if keyword in user_lower:
                for ref_path in ref_paths:
                    detected.add(ref_path)

        return sorted(list(detected))

    def get_skill_references(self, skill_name: str) -> List[str]:
        """
        Get reference files for a skill without loading content.

        Args:
            skill_name: Skill name

        Returns:
            List of reference file paths
        """
        return self.reference_map.get(skill_name, [])

    def add_skill_reference(self, skill_name: str, ref_path: str) -> None:
        """
        Add a reference to a skill's reference list.

        Args:
            skill_name: Skill name
            ref_path: Reference file path to add
        """
        if skill_name not in self.reference_map:
            self.reference_map[skill_name] = []
        if ref_path not in self.reference_map[skill_name]:
            self.reference_map[skill_name].append(ref_path)

    def clear_cache(self) -> None:
        """Clear the reference cache."""
        self._cache.clear()

    def preload_references(self, skill_names: Optional[List[str]] = None) -> int:
        """
        Preload references into cache.

        Args:
            skill_names: Skills to preload (None = all)

        Returns:
            Number of references loaded
        """
        loaded = 0
        skills = skill_names or list(self.reference_map.keys())

        for skill in skills:
            for ref_path in self.reference_map.get(skill, []):
                content = self._load_reference(ref_path)
                if content:
                    loaded += 1

        return loaded


# =============================================================================
# CONTEXT INJECTION ACTION (Non-hazardous)
# =============================================================================

class InjectContextAction:
    """
    Action to inject context for skill execution.

    Non-hazardous action that loads and prepares context.
    """

    api_name: ClassVar[str] = "inject_context"
    display_name: ClassVar[str] = "Inject Context"
    description: ClassVar[str] = "Inject reference context for skill execution"
    is_hazardous: ClassVar[bool] = False

    def __init__(
        self,
        skill_name: str,
        user_input: str = "",
        include_plan: bool = True,
        injector: Optional[ContextInjector] = None,
    ):
        """
        Initialize context injection action.

        Args:
            skill_name: Skill to inject context for
            user_input: User input for auto-detection
            include_plan: Whether to include plan file
            injector: Optional ContextInjector instance
        """
        self.skill_name = skill_name
        self.user_input = user_input
        self.include_plan = include_plan
        self.injector = injector or ContextInjector()

    def execute(self) -> InjectedContext:
        """Execute context injection."""
        return self.injector.inject(
            self.skill_name,
            self.user_input,
            self.include_plan,
        )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def inject_context(
    skill_name: str,
    user_input: str = "",
    include_plan: bool = True,
) -> InjectedContext:
    """
    Convenience function for context injection.

    Args:
        skill_name: Skill name
        user_input: User input for auto-detection
        include_plan: Whether to include plan file

    Returns:
        InjectedContext with loaded content
    """
    injector = ContextInjector()
    return injector.inject(skill_name, user_input, include_plan)


def get_default_injector() -> ContextInjector:
    """Get a default ContextInjector instance."""
    return ContextInjector()


def get_reference_map() -> Dict[str, List[str]]:
    """Get the current reference map."""
    return REFERENCE_MAP.copy()
