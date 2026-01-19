"""
Orion ODA v3.0 - Scope Minimizer
================================

Audit-specific Socratic questioning for scope minimization.
Integrates with ClarificationTracker V2.1.8.

This module reduces audit scope through intelligent questioning:
- Detects implicit scope from user input
- Generates minimal Socratic questions (max 3)
- Determines focused targets for audit execution
- Supports Auto-Compact survival through serialization

Usage:
    from lib.oda.planning import ScopeMinimizer, create_clarification_tracker

    tracker = create_clarification_tracker("코드 검사해줘")
    minimizer = ScopeMinimizer(tracker)

    # Check for implicit scope first
    if minimizer.has_implicit_scope("lib/oda/ 검사해줘"):
        scope = minimizer.get_implicit_scope("lib/oda/ 검사해줘")
    else:
        questions = minimizer.generate_scope_questions("코드 검사해줘")
        # Ask questions via AskUserQuestion...
        scope = minimizer.minimize_scope(responses)

    targets = minimizer.get_focused_targets(scope)
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple

from .clarification_tracker import (
    ClarificationTracker,
    ClarificationState,
    ClarificationError,
)


class ScopeType(str, Enum):
    """Types of audit scope."""
    FILE = "file"           # 특정 파일
    DIRECTORY = "directory" # 특정 디렉토리
    MODULE = "module"       # Python 모듈
    PATTERN = "pattern"     # Glob 패턴
    RECENT = "recent"       # 최근 변경 파일


# Confidence levels (categorical, NO numerical scores)
ConfidenceLevel = Literal["high", "medium", "low"]


@dataclass
class MinimizedScope:
    """
    Result of scope minimization.

    Attributes:
        scope_type: Type of scope (file, directory, module, pattern)
        targets: List of target paths
        include_tests: Whether to include test files
        max_depth: Maximum directory depth (None = unlimited)
        confidence: Categorical confidence level
        reason: Why this scope was determined
    """
    scope_type: ScopeType
    targets: List[str]
    include_tests: bool = True
    max_depth: Optional[int] = None
    confidence: ConfidenceLevel = "medium"
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "scope_type": self.scope_type.value,
            "targets": self.targets,
            "include_tests": self.include_tests,
            "max_depth": self.max_depth,
            "confidence": self.confidence,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MinimizedScope":
        """Deserialize from dictionary."""
        return cls(
            scope_type=ScopeType(data["scope_type"]),
            targets=data["targets"],
            include_tests=data.get("include_tests", True),
            max_depth=data.get("max_depth"),
            confidence=data.get("confidence", "medium"),
            reason=data.get("reason", ""),
        )

    def format_summary(self) -> str:
        """Format scope for display."""
        type_display = {
            ScopeType.FILE: "파일",
            ScopeType.DIRECTORY: "디렉토리",
            ScopeType.MODULE: "모듈",
            ScopeType.PATTERN: "패턴",
            ScopeType.RECENT: "최근 변경",
        }

        targets_str = ", ".join(self.targets[:3])
        if len(self.targets) > 3:
            targets_str += f" 외 {len(self.targets) - 3}개"

        return (
            f"범위: {type_display[self.scope_type]} ({len(self.targets)}개)\n"
            f"대상: {targets_str}\n"
            f"테스트 포함: {'예' if self.include_tests else '아니오'}"
        )


@dataclass
class ScopeQuestion:
    """
    A single scope-minimizing question.

    Attributes:
        question: The question text
        header: Question header/title
        options: List of option dictionaries
        multi_select: Whether multiple selections are allowed
        question_type: Type of information being requested
    """
    question: str
    header: str
    options: List[Dict[str, str]]
    multi_select: bool = False
    question_type: str = "scope"  # scope, tests, depth

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "question": self.question,
            "header": self.header,
            "options": self.options,
            "multi_select": self.multi_select,
            "question_type": self.question_type,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScopeQuestion":
        """Deserialize from dictionary."""
        return cls(
            question=data["question"],
            header=data["header"],
            options=data["options"],
            multi_select=data.get("multi_select", False),
            question_type=data.get("question_type", "scope"),
        )

    def to_askuser_format(self) -> Dict[str, Any]:
        """Convert to AskUserQuestion format."""
        return {
            "question": self.question,
            "header": self.header,
            "options": self.options,
            "multiSelect": self.multi_select,
        }


@dataclass
class ScopeMinimizerState:
    """
    Serializable state for Auto-Compact survival.

    Attributes:
        questions_asked: Number of questions asked
        questions: List of questions generated
        responses: User responses by question index
        implicit_scope: Detected implicit scope (if any)
        finalized_scope: Final minimized scope (if determined)
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    questions_asked: int = 0
    questions: List[ScopeQuestion] = field(default_factory=list)
    responses: Dict[int, str] = field(default_factory=dict)
    implicit_scope: Optional[MinimizedScope] = None
    finalized_scope: Optional[MinimizedScope] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "questions_asked": self.questions_asked,
            "questions": [q.to_dict() for q in self.questions],
            "responses": self.responses,
            "implicit_scope": self.implicit_scope.to_dict() if self.implicit_scope else None,
            "finalized_scope": self.finalized_scope.to_dict() if self.finalized_scope else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScopeMinimizerState":
        """Deserialize from dictionary."""
        return cls(
            questions_asked=data["questions_asked"],
            questions=[ScopeQuestion.from_dict(q) for q in data.get("questions", [])],
            responses={int(k): v for k, v in data.get("responses", {}).items()},
            implicit_scope=(
                MinimizedScope.from_dict(data["implicit_scope"])
                if data.get("implicit_scope")
                else None
            ),
            finalized_scope=(
                MinimizedScope.from_dict(data["finalized_scope"])
                if data.get("finalized_scope")
                else None
            ),
            created_at=(
                datetime.fromisoformat(data["created_at"])
                if "created_at" in data
                else datetime.now()
            ),
            updated_at=(
                datetime.fromisoformat(data["updated_at"])
                if "updated_at" in data
                else datetime.now()
            ),
        )


class ScopeMinimizer:
    """
    Audit-specific Socratic questioning for scope minimization.

    Integrates with ClarificationTracker to manage state and follows
    the Semantic Integrity Protocol.

    Key features:
    - Implicit scope detection (skip questions if scope is clear)
    - Maximum 3 questions to prevent infinite loops
    - Integration with ClarificationTracker state machine
    - Auto-Compact survival through JSON serialization

    Example:
        tracker = create_clarification_tracker("lib/oda 검사해줘")
        minimizer = ScopeMinimizer(tracker)

        # Implicit scope detected - no questions needed
        if minimizer.has_implicit_scope("lib/oda 검사해줘"):
            scope = minimizer.get_implicit_scope("lib/oda 검사해줘")
            targets = minimizer.get_focused_targets(scope)
            # Proceed to audit execution...
    """

    MAX_QUESTIONS = 3  # Prevent excessive questioning

    # Path patterns for implicit scope detection
    PATH_PATTERN = re.compile(
        r'(?:^|\s)(?:\.?/)?'  # Optional leading ./ or /
        r'([a-zA-Z_][a-zA-Z0-9_]*(?:/[a-zA-Z_][a-zA-Z0-9_\.]*)+)'  # Path like lib/oda/planning
        r'(?:\s|$|,|\.(?:\s|$))',
        re.UNICODE
    )

    # File extension pattern
    FILE_PATTERN = re.compile(
        r'(?:^|\s)'
        r'([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z]+))'  # filename.ext
        r'(?:\s|$|,)',
        re.UNICODE
    )

    # Glob pattern detection
    GLOB_PATTERN = re.compile(
        r'\*+|\?|'  # Wildcards
        r'\[.+\]',  # Character classes
        re.UNICODE
    )

    # Keywords indicating specific scope
    SCOPE_KEYWORDS = {
        "recent": ["최근", "방금", "recent", "changed", "modified"],
        "tests": ["테스트", "test", "tests", "spec", "specs"],
        "specific": ["만", "only", "just", "특정"],
    }

    def __init__(
        self,
        tracker: ClarificationTracker,
        workspace_root: Optional[str] = None,
    ):
        """
        Initialize ScopeMinimizer.

        Args:
            tracker: ClarificationTracker for state management
            workspace_root: Root directory for scope resolution
        """
        self.tracker = tracker
        self.workspace_root = workspace_root or self._detect_workspace_root()
        self._state = ScopeMinimizerState()

    @staticmethod
    def _detect_workspace_root() -> str:
        """Detect workspace root from environment or git."""
        # Try environment variable
        if "WORKSPACE_ROOT" in os.environ:
            return os.environ["WORKSPACE_ROOT"]

        # Try to find git root
        cwd = os.getcwd()
        check_dir = cwd
        while check_dir != "/":
            if os.path.isdir(os.path.join(check_dir, ".git")):
                return check_dir
            check_dir = os.path.dirname(check_dir)

        return cwd

    # ========== Implicit Scope Detection ==========

    def has_implicit_scope(self, user_input: str) -> bool:
        """
        Check if user input already specifies a clear scope.

        Args:
            user_input: Original user input

        Returns:
            True if scope can be determined without questions
        """
        scope = self._detect_implicit_scope(user_input)
        return scope is not None

    def get_implicit_scope(self, user_input: str) -> Optional[MinimizedScope]:
        """
        Get implicit scope from user input if clear.

        Args:
            user_input: Original user input

        Returns:
            MinimizedScope if detected, None otherwise
        """
        scope = self._detect_implicit_scope(user_input)
        if scope:
            self._state.implicit_scope = scope
            self._state.finalized_scope = scope
            self._state.updated_at = datetime.now()
        return scope

    def _detect_implicit_scope(self, user_input: str) -> Optional[MinimizedScope]:
        """
        Internal method to detect scope from user input.

        Looks for:
        - Explicit paths (lib/oda/, ./src/components)
        - File names (module.py, config.yaml)
        - Glob patterns (*.py, **/*.ts)

        Args:
            user_input: Original user input

        Returns:
            MinimizedScope if detected, None otherwise
        """
        targets: List[str] = []
        scope_type = ScopeType.DIRECTORY

        # Check for path patterns
        path_matches = self.PATH_PATTERN.findall(user_input)
        for path in path_matches:
            full_path = os.path.join(self.workspace_root, path)
            if os.path.exists(full_path):
                targets.append(path)
                if os.path.isfile(full_path):
                    scope_type = ScopeType.FILE

        # Check for file patterns
        file_matches = self.FILE_PATTERN.findall(user_input)
        for filename in file_matches:
            # Search for file in workspace
            found_path = self._find_file(filename)
            if found_path:
                targets.append(found_path)
                scope_type = ScopeType.FILE

        # Check for glob patterns
        if self.GLOB_PATTERN.search(user_input):
            # Extract glob pattern
            glob_match = re.search(r'([^\s]+\*[^\s]*)', user_input)
            if glob_match:
                targets.append(glob_match.group(1))
                scope_type = ScopeType.PATTERN

        # Check for "recent" keyword
        if any(kw in user_input.lower() for kw in self.SCOPE_KEYWORDS["recent"]):
            scope_type = ScopeType.RECENT
            if not targets:
                targets = ["HEAD~5"]  # Default to last 5 commits

        if targets:
            # Determine test inclusion from input
            include_tests = not any(
                kw in user_input.lower()
                for kw in ["테스트 제외", "without test", "no test", "skip test"]
            )

            return MinimizedScope(
                scope_type=scope_type,
                targets=targets,
                include_tests=include_tests,
                confidence="high",
                reason=f"Detected from input: {user_input[:50]}",
            )

        return None

    def _find_file(self, filename: str) -> Optional[str]:
        """Find file in workspace by name."""
        for root, _, files in os.walk(self.workspace_root):
            # Skip hidden and cache directories
            if any(part.startswith(('.', '__')) for part in root.split(os.sep)):
                continue

            if filename in files:
                return os.path.relpath(os.path.join(root, filename), self.workspace_root)

        return None

    # ========== Question Generation ==========

    def generate_scope_questions(self, user_input: str) -> List[ScopeQuestion]:
        """
        Generate Socratic questions to minimize audit scope.

        Args:
            user_input: Original user input

        Returns:
            List of questions (max 3)
        """
        if self._state.questions_asked >= self.MAX_QUESTIONS:
            return []

        questions: List[ScopeQuestion] = []

        # Question 1: Scope type
        if self._state.questions_asked == 0:
            questions.append(self._create_scope_type_question())

        # Question 2: Specific target (if needed)
        if self._state.questions_asked <= 1 and len(questions) < self.MAX_QUESTIONS:
            target_question = self._create_target_question()
            if target_question:
                questions.append(target_question)

        # Question 3: Test inclusion (if still needed)
        if self._state.questions_asked <= 2 and len(questions) < self.MAX_QUESTIONS:
            questions.append(self._create_test_inclusion_question())

        # Store questions
        self._state.questions = questions
        self._state.updated_at = datetime.now()

        return questions

    def _create_scope_type_question(self) -> ScopeQuestion:
        """Create question about scope type."""
        return ScopeQuestion(
            question="어떤 범위를 검사할까요?",
            header="검사 범위",
            options=[
                {"label": "특정 파일", "description": "하나 이상의 특정 파일"},
                {"label": "특정 디렉토리", "description": "하나의 디렉토리와 하위 파일"},
                {"label": "모듈", "description": "Python 모듈 또는 패키지"},
                {"label": "최근 변경", "description": "최근 수정된 파일"},
                {"label": "전체", "description": "프로젝트 전체 (시간이 오래 걸림)"},
            ],
            multi_select=False,
            question_type="scope_type",
        )

    def _create_target_question(self) -> Optional[ScopeQuestion]:
        """Create question about specific target."""
        # Get available directories for suggestions
        suggestions = self._get_directory_suggestions()

        if not suggestions:
            return None

        return ScopeQuestion(
            question="어떤 경로를 검사할까요?",
            header="검사 대상",
            options=[
                {"label": path, "description": f"{count}개 파일"}
                for path, count in suggestions[:6]
            ],
            multi_select=True,
            question_type="target",
        )

    def _create_test_inclusion_question(self) -> ScopeQuestion:
        """Create question about test file inclusion."""
        return ScopeQuestion(
            question="테스트 파일도 포함할까요?",
            header="테스트 포함 여부",
            options=[
                {"label": "예", "description": "테스트 파일 포함 검사"},
                {"label": "아니오", "description": "테스트 제외, 소스만 검사"},
            ],
            multi_select=False,
            question_type="tests",
        )

    def _get_directory_suggestions(self) -> List[Tuple[str, int]]:
        """Get directory suggestions with file counts."""
        suggestions: List[Tuple[str, int]] = []

        try:
            for item in os.listdir(self.workspace_root):
                if item.startswith(('.', '__')):
                    continue

                item_path = os.path.join(self.workspace_root, item)
                if os.path.isdir(item_path):
                    file_count = self._count_source_files(item_path)
                    if file_count > 0:
                        suggestions.append((item, file_count))
        except PermissionError:
            pass

        # Sort by file count descending
        suggestions.sort(key=lambda x: x[1], reverse=True)
        return suggestions

    def _count_source_files(self, path: str) -> int:
        """Count source files in directory."""
        count = 0
        extensions = {".py", ".ts", ".js", ".tsx", ".jsx", ".go", ".rs", ".java"}

        try:
            for root, dirs, files in os.walk(path):
                # Skip hidden directories
                dirs[:] = [d for d in dirs if not d.startswith(('.', '__'))]

                for f in files:
                    if any(f.endswith(ext) for ext in extensions):
                        count += 1

                # Early exit for large directories
                if count > 100:
                    return count
        except PermissionError:
            pass

        return count

    # ========== Response Processing ==========

    def record_response(self, question_index: int, response: str) -> None:
        """
        Record user response to a question.

        Args:
            question_index: Index of the question (0-based)
            response: User's response
        """
        self._state.responses[question_index] = response
        self._state.questions_asked += 1
        self._state.updated_at = datetime.now()

        # Also record in tracker if in questioning state
        if self.tracker.state == ClarificationState.QUESTIONING:
            self.tracker.record_response(question_index, response)

    def minimize_scope(
        self,
        responses: Optional[Dict[int, str]] = None,
    ) -> MinimizedScope:
        """
        Determine minimal scope from user responses.

        Args:
            responses: Optional responses dict (uses internal state if None)

        Returns:
            MinimizedScope determined from responses
        """
        if responses:
            self._state.responses.update(responses)

        responses = self._state.responses

        # Determine scope type from first response
        scope_type_response = responses.get(0, "전체")
        scope_type = self._parse_scope_type(scope_type_response)

        # Determine targets from second response
        target_response = responses.get(1, "")
        targets = self._parse_targets(target_response)

        # Determine test inclusion from third response
        test_response = responses.get(2, "예")
        include_tests = test_response.lower() in ["예", "yes", "y", "true"]

        # Calculate confidence
        confidence = self._calculate_confidence(responses)

        scope = MinimizedScope(
            scope_type=scope_type,
            targets=targets if targets else ["."],
            include_tests=include_tests,
            confidence=confidence,
            reason=f"Determined from {len(responses)} responses",
        )

        self._state.finalized_scope = scope
        self._state.updated_at = datetime.now()

        return scope

    def _parse_scope_type(self, response: str) -> ScopeType:
        """Parse scope type from response."""
        response_lower = response.lower()

        if any(kw in response_lower for kw in ["파일", "file"]):
            return ScopeType.FILE
        if any(kw in response_lower for kw in ["디렉토리", "directory", "dir", "폴더", "folder"]):
            return ScopeType.DIRECTORY
        if any(kw in response_lower for kw in ["모듈", "module", "패키지", "package"]):
            return ScopeType.MODULE
        if any(kw in response_lower for kw in ["최근", "recent", "changed"]):
            return ScopeType.RECENT
        if any(kw in response_lower for kw in ["패턴", "pattern", "*", "glob"]):
            return ScopeType.PATTERN

        return ScopeType.DIRECTORY  # Default

    def _parse_targets(self, response: str) -> List[str]:
        """Parse target paths from response."""
        targets: List[str] = []

        if not response:
            return targets

        # Split by common separators
        parts = re.split(r'[,;\s]+', response)

        for part in parts:
            part = part.strip()
            if not part:
                continue

            # Check if it's a valid path
            full_path = os.path.join(self.workspace_root, part)
            if os.path.exists(full_path):
                targets.append(part)
            elif self.GLOB_PATTERN.search(part):
                # It's a glob pattern
                targets.append(part)

        return targets

    def _calculate_confidence(self, responses: Dict[int, str]) -> ConfidenceLevel:
        """Calculate confidence level from responses."""
        if len(responses) >= 2 and all(responses.values()):
            # Multiple clear responses
            return "high"
        if len(responses) >= 1 and any(responses.values()):
            # At least one clear response
            return "medium"
        return "low"

    # ========== Target Resolution ==========

    def get_focused_targets(self, scope: MinimizedScope) -> List[str]:
        """
        Return actual file/directory paths for focused audit.

        Args:
            scope: MinimizedScope to resolve

        Returns:
            List of absolute paths ready for audit
        """
        targets: List[str] = []

        for target in scope.targets:
            if scope.scope_type == ScopeType.PATTERN:
                # Resolve glob pattern
                resolved = self._resolve_glob(target)
                targets.extend(resolved)
            elif scope.scope_type == ScopeType.RECENT:
                # Get recently modified files
                resolved = self._get_recent_files(target)
                targets.extend(resolved)
            else:
                # Direct path resolution
                full_path = os.path.join(self.workspace_root, target)
                if os.path.exists(full_path):
                    targets.append(full_path)

        # Filter out test files if not included
        if not scope.include_tests:
            targets = [t for t in targets if not self._is_test_file(t)]

        # Apply max depth if specified
        if scope.max_depth is not None:
            targets = self._apply_max_depth(targets, scope.max_depth)

        return targets

    def _resolve_glob(self, pattern: str) -> List[str]:
        """Resolve glob pattern to actual paths."""
        from pathlib import Path as PLPath

        try:
            base_path = PLPath(self.workspace_root)
            matches = list(base_path.glob(pattern))
            return [str(m) for m in matches[:50]]  # Limit to 50 matches
        except Exception:
            return []

    def _get_recent_files(self, ref: str = "HEAD~5") -> List[str]:
        """Get recently modified files from git."""
        import subprocess

        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", ref],
                capture_output=True,
                text=True,
                cwd=self.workspace_root,
            )

            if result.returncode == 0:
                files = result.stdout.strip().split("\n")
                return [
                    os.path.join(self.workspace_root, f)
                    for f in files
                    if f and os.path.exists(os.path.join(self.workspace_root, f))
                ]
        except Exception:
            pass

        return []

    def _is_test_file(self, path: str) -> bool:
        """Check if path is a test file."""
        path_lower = path.lower()
        test_indicators = [
            "test_",
            "_test.",
            ".test.",
            "/tests/",
            "/test/",
            "_spec.",
            ".spec.",
            "/specs/",
        ]
        return any(indicator in path_lower for indicator in test_indicators)

    def _apply_max_depth(self, targets: List[str], max_depth: int) -> List[str]:
        """Filter targets to max depth from workspace root."""
        result: List[str] = []

        for target in targets:
            try:
                rel_path = os.path.relpath(target, self.workspace_root)
                depth = len(Path(rel_path).parts)
                if depth <= max_depth:
                    result.append(target)
            except ValueError:
                # Path on different drive (Windows)
                result.append(target)

        return result

    # ========== Persistence (Auto-Compact Survival) ==========

    def to_json(self) -> str:
        """
        Serialize to JSON for persistence.

        Returns:
            JSON string for storage
        """
        data = {
            "workspace_root": self.workspace_root,
            "state": self._state.to_dict(),
            "tracker_json": self.tracker.to_json(),
        }
        return json.dumps(data, ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "ScopeMinimizer":
        """
        Deserialize from JSON.

        Args:
            json_str: JSON string from to_json()

        Returns:
            Restored ScopeMinimizer
        """
        data = json.loads(json_str)

        # Restore tracker
        tracker = ClarificationTracker.from_json(data["tracker_json"])

        # Create instance
        minimizer = cls(tracker, data.get("workspace_root"))

        # Restore state
        minimizer._state = ScopeMinimizerState.from_dict(data["state"])

        return minimizer

    # ========== State Access ==========

    @property
    def questions_asked(self) -> int:
        """Number of questions asked so far."""
        return self._state.questions_asked

    @property
    def can_ask_more(self) -> bool:
        """Whether more questions can be asked."""
        return self._state.questions_asked < self.MAX_QUESTIONS

    @property
    def finalized_scope(self) -> Optional[MinimizedScope]:
        """Get finalized scope if determined."""
        return self._state.finalized_scope

    def get_state(self) -> ScopeMinimizerState:
        """Get internal state for debugging/audit."""
        return self._state


# ========== Convenience Functions ==========

def create_scope_minimizer(
    user_input: str,
    workspace_root: Optional[str] = None,
) -> ScopeMinimizer:
    """
    Create a ScopeMinimizer with new ClarificationTracker.

    Args:
        user_input: Original user input
        workspace_root: Optional workspace root

    Returns:
        New ScopeMinimizer instance
    """
    from .clarification_tracker import create_clarification_tracker

    tracker = create_clarification_tracker(user_input)
    return ScopeMinimizer(tracker, workspace_root)


def load_scope_minimizer(json_str: str) -> ScopeMinimizer:
    """
    Load ScopeMinimizer from JSON (for Auto-Compact recovery).

    Args:
        json_str: JSON string from to_json()

    Returns:
        Restored ScopeMinimizer
    """
    return ScopeMinimizer.from_json(json_str)


def detect_scope_from_input(
    user_input: str,
    workspace_root: Optional[str] = None,
) -> Optional[MinimizedScope]:
    """
    Quick check for implicit scope in user input.

    Args:
        user_input: User input to analyze
        workspace_root: Optional workspace root

    Returns:
        MinimizedScope if detected, None otherwise
    """
    from .clarification_tracker import create_clarification_tracker

    tracker = create_clarification_tracker(user_input)
    minimizer = ScopeMinimizer(tracker, workspace_root)
    return minimizer.get_implicit_scope(user_input)


def get_audit_questions(
    user_input: str,
    workspace_root: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Get AskUserQuestion-formatted questions for audit scope.

    Args:
        user_input: User input to analyze
        workspace_root: Optional workspace root

    Returns:
        List of questions in AskUserQuestion format
    """
    from .clarification_tracker import create_clarification_tracker

    tracker = create_clarification_tracker(user_input)
    minimizer = ScopeMinimizer(tracker, workspace_root)

    # Check for implicit scope first
    if minimizer.has_implicit_scope(user_input):
        return []  # No questions needed

    questions = minimizer.generate_scope_questions(user_input)
    return [q.to_askuser_format() for q in questions]
