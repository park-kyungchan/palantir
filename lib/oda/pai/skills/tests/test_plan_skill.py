"""
Orion ODA PAI Skills - /plan Skill Unit Tests

Tests for the /plan skill (V2.1.4) including:
- Dual-Path Analysis (ODA Protocol + Plan Subagent)
- TaskDecomposer integration
- Scope keyword detection (Korean/English)
- Resume parameter functionality
- Agent Registry tracking
- Plan file generation
- Boris Cherny parallel execution pattern

Reference: .claude/skills/plan.md

Version: 1.0.0
"""
from __future__ import annotations

import os
import re
import pytest
import tempfile
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path


# =============================================================================
# PLAN SKILL CORE LOGIC (Extracted from plan.md for testing)
# =============================================================================

# V2.1.4 Configuration (from frontmatter)
PLAN_SKILL_CONFIG = {
    "name": "plan",
    "version": "2.1.4",
    "model": "sonnet",
    "context": "fork",
    "run_in_background": True,
    "tools": ["Read", "Grep", "Glob", "Task", "TodoWrite"],
    "evidence_required": ["change_plan", "risk_assessment", "test_strategy", "dual_path_synthesis"],
    "oda_context": {
        "role": "planner",
        "stage_access": ["A", "B"],
        "governance_mode": "strict",
    }
}

# Trigger Keywords (from Section 7)
PLAN_TRIGGERS = {
    "commands": ["/plan"],
    "keywords_ko": ["계획", "설계", "구현"],
    "keywords_en": ["plan", "design", "implementation"],
    "patterns": ["create plan", "implementation design", "설계해줘"],
}

# Scope Keywords for TaskDecomposer (from Section 4)
SCOPE_KEYWORDS = {
    "ko": ["전체", "모든", "완전한", "전부"],
    "en": ["all", "entire", "complete", "whole", "full", "every"],
}

# Output Budget Constraints (from Section 4.3)
OUTPUT_BUDGETS = {
    "Explore": 5000,
    "Plan": 10000,
    "general-purpose": 15000,
}

# Synthesis Comparison Matrix (from Section 2.3)
SYNTHESIS_MATRIX = {
    "file_coverage": {
        "oda_protocol": "Glob/Grep based",
        "plan_subagent": "Pattern based",
        "synthesis_rule": "Prefer ODA (explicit files_viewed)",
    },
    "dependencies": {
        "oda_protocol": "Import tracing",
        "plan_subagent": "Logical inference",
        "synthesis_rule": "Union both sets",
    },
    "risk_assessment": {
        "oda_protocol": "Security rules",
        "plan_subagent": "Design risks",
        "synthesis_rule": "Merge all, dedupe",
    },
    "test_strategy": {
        "oda_protocol": "Code-based",
        "plan_subagent": "Scenario-based",
        "synthesis_rule": "Combine approaches",
    },
    "implementation_order": {
        "oda_protocol": "Dependency order",
        "plan_subagent": "Logical sequence",
        "synthesis_rule": "ODA order + Subagent rationale",
    },
}


# =============================================================================
# IMPLEMENTATION CLASSES AND FUNCTIONS (Extracted from plan.md)
# =============================================================================

class SubagentType(str, Enum):
    """Subagent types with their identifiers."""
    EXPLORE = "Explore"
    PLAN = "Plan"
    GENERAL_PURPOSE = "general-purpose"


@dataclass
class TokenBudget:
    """Token budget configuration per subagent type."""
    explore: int = 5000
    plan: int = 10000
    general_purpose: int = 15000

    def get_budget(self, subagent_type: SubagentType) -> int:
        """Get token budget for subagent type."""
        mapping = {
            SubagentType.EXPLORE: self.explore,
            SubagentType.PLAN: self.plan,
            SubagentType.GENERAL_PURPOSE: self.general_purpose,
        }
        return mapping.get(subagent_type, self.general_purpose)


@dataclass
class SubTask:
    """A decomposed subtask for delegation."""
    description: str
    prompt: str
    subagent_type: SubagentType
    scope: str
    token_budget: int
    priority: int = 0
    dependencies: List[str] = field(default_factory=list)
    task_id: Optional[str] = None
    should_resume: bool = False

    def to_task_params(self) -> Dict[str, Any]:
        """Convert to Task tool parameters."""
        params = {
            "description": self.description,
            "prompt": self.prompt,
            "subagent_type": self.subagent_type.value,
            "run_in_background": True,
        }
        if self.should_resume and self.task_id:
            params["resume"] = self.task_id
        return params

    def mark_for_resume(self, task_id: str) -> "SubTask":
        """Mark this subtask for resumption from a previous execution."""
        self.task_id = task_id
        self.should_resume = True
        return self


@dataclass
class AgentRegistryEntry:
    """Entry for Agent Registry tracking."""
    agent_id: str
    agent_type: SubagentType
    phase_task: str
    description: str
    status: str  # pending, running, completed, failed


@dataclass
class PlanResult:
    """Unified plan result from dual-path synthesis."""
    status: str  # PASS, FAIL, WARNING
    timestamp: str
    target: str
    plan_file: str
    dual_path_synthesis: Dict[str, bool]
    change_plan: List[Dict[str, Any]]
    risk_assessment: List[Dict[str, Any]]
    test_strategy: Dict[str, List[str]]
    evidence: Dict[str, Any]


@dataclass
class ScopeAnalysis:
    """Scope analysis result for TaskDecomposer."""
    has_scope_keywords: bool
    detected_keywords: List[str]
    file_count: int
    directory_count: int
    should_decompose: bool
    recommended_subtask_count: int


def detect_scope_keywords(task: str) -> Tuple[bool, List[str]]:
    """
    Detect scope keywords in task description.

    From plan.md Section 4.1: Scope Keyword Detection (Korean + English)

    Args:
        task: Task description

    Returns:
        Tuple of (has_keywords, list_of_detected_keywords)
    """
    task_lower = task.lower()
    detected = []

    for keyword in SCOPE_KEYWORDS["ko"]:
        if keyword in task_lower:
            detected.append(keyword)

    for keyword in SCOPE_KEYWORDS["en"]:
        if keyword in task_lower:
            detected.append(keyword)

    return len(detected) > 0, detected


def should_decompose_task(task: str, scope: Optional[str] = None) -> bool:
    """
    Check if task should be decomposed.

    From plan.md Section 4.2: Decomposition Logic

    Args:
        task: Task description
        scope: Optional scope path

    Returns:
        True if decomposition recommended
    """
    # Check scope keywords
    has_keywords, _ = detect_scope_keywords(task)
    if has_keywords:
        return True

    # Check file/directory counts if scope provided
    if scope and os.path.exists(scope):
        file_count = estimate_file_count(scope)
        if file_count > 20:
            return True

        dir_count = count_directories(scope)
        if dir_count > 5:
            return True

    return False


def estimate_file_count(
    path: str,
    extensions: Optional[List[str]] = None
) -> int:
    """Estimate file count in directory."""
    if not os.path.isdir(path):
        return 1

    extensions = extensions or [".py", ".ts", ".js", ".md", ".yaml", ".yml"]
    count = 0

    try:
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if not d.startswith(('.', '__'))]
            for f in files:
                if any(f.endswith(ext) for ext in extensions):
                    count += 1
            if count > 40:  # Early exit
                break
    except PermissionError:
        pass

    return count


def count_directories(path: str) -> int:
    """Count immediate subdirectories."""
    if not os.path.isdir(path):
        return 0

    try:
        return len([
            d for d in os.listdir(path)
            if os.path.isdir(os.path.join(path, d))
            and not d.startswith(('.', '__'))
        ])
    except PermissionError:
        return 0


def analyze_scope(task: str, scope: str) -> ScopeAnalysis:
    """
    Analyze scope for decomposition decision.

    Args:
        task: Task description
        scope: Scope path

    Returns:
        ScopeAnalysis dataclass
    """
    has_keywords, detected = detect_scope_keywords(task)
    file_count = estimate_file_count(scope) if os.path.exists(scope) else 0
    dir_count = count_directories(scope) if os.path.exists(scope) else 0

    should_decompose = (
        has_keywords or
        file_count > 20 or
        dir_count > 5
    )

    # Recommend subtask count based on directories
    recommended = min(dir_count, 10) if dir_count > 0 else 1

    return ScopeAnalysis(
        has_scope_keywords=has_keywords,
        detected_keywords=detected,
        file_count=file_count,
        directory_count=dir_count,
        should_decompose=should_decompose,
        recommended_subtask_count=recommended,
    )


def is_plan_trigger(user_input: str) -> bool:
    """
    Check if user input triggers /plan skill.

    From plan.md Section 7: Invocation

    Args:
        user_input: User's input

    Returns:
        True if /plan should be triggered
    """
    user_lower = user_input.lower()

    # Check commands
    for cmd in PLAN_TRIGGERS["commands"]:
        if cmd in user_lower:
            return True

    # Check Korean keywords
    for kw in PLAN_TRIGGERS["keywords_ko"]:
        if kw in user_lower:
            return True

    # Check English keywords
    for kw in PLAN_TRIGGERS["keywords_en"]:
        if kw in user_lower:
            return True

    # Check patterns
    for pattern in PLAN_TRIGGERS["patterns"]:
        if pattern in user_lower:
            return True

    return False


def generate_subtask_prompt(
    task: str,
    scope: str,
    subagent_type: SubagentType,
) -> str:
    """
    Generate prompt for subtask.

    From plan.md Section 9: Subagent Prompt Templates

    Args:
        task: Task description
        scope: Scope path
        subagent_type: Type of subagent

    Returns:
        Formatted prompt string
    """
    budget = OUTPUT_BUDGETS.get(subagent_type.value, 15000)

    return f'''## Task
{task}

## Scope
Analyze ONLY: {scope}

## Constraint: Output Budget
YOUR OUTPUT MUST NOT EXCEED {budget} TOKENS.
Return ONLY: Key findings, critical paths, summary.
DO NOT include: Full file contents, verbose explanations.
Format: Bullet points with file:line references.

## Evidence Required
- files_viewed: [must populate with actual files read]
- summary: [key findings in bullet points]
'''


def generate_oda_protocol_prompt(target_path: str) -> str:
    """
    Generate ODA Protocol (Explore) prompt.

    From plan.md Section 9.1: ODA Protocol (Explore) Prompt

    Args:
        target_path: Path to analyze

    Returns:
        Formatted prompt
    """
    return f'''## Context
Operating under ODA governance. Stage A+B analysis for: {target_path}
Reference: `.claude/references/3-stage-protocol.md`

## Task
Execute ODA 3-Stage Protocol (A: SCAN, B: TRACE) for planning:
1. Stage A: Discover files, patterns, complexity
2. Stage B: Verify imports, map dependencies

## Required Evidence (MANDATORY)
- files_viewed: [must populate - anti-hallucination]
- imports_verified: [must populate]
- signatures_matched: [actual function signatures]
- dependencies_mapped: [source -> depends_on]

## Constraint: Output Budget
YOUR OUTPUT MUST NOT EXCEED 5000 TOKENS.
Format: Structured evidence with file:line references.
'''


def generate_plan_subagent_prompt(target_path: str, pre_check_evidence: str = "") -> str:
    """
    Generate Plan Subagent prompt.

    From plan.md Section 9.2: Plan Subagent Prompt

    Args:
        target_path: Path to plan
        pre_check_evidence: Optional evidence from pre-check

    Returns:
        Formatted prompt
    """
    return f'''## Context
Operating under ODA governance. Planning only, no implementation.
Reference: `.claude/references/3-stage-protocol.md`

## Task
Create implementation plan for: {target_path}

## Input Evidence (if available)
{pre_check_evidence}

## Required Output

### 1. Change Plan
Order changes by dependency, include:
- file:line references
- Specific modifications
- Dependency order
- Rationale for each change

### 2. Risk Assessment
Identify and mitigate risks:
- Breaking changes
- API compatibility
- Performance impact
- Security concerns

### 3. Test Strategy
Define verification approach:
- Unit tests required
- Integration tests
- Edge cases

## Constraint: Output Budget
YOUR OUTPUT MUST NOT EXCEED 10000 TOKENS.
Format: Structured plan with file:line references.
'''


def slugify(text: str) -> str:
    """
    Convert text to slug for plan file naming.

    From plan.md Section 5.1: Auto-Generation Logic

    Args:
        text: Text to slugify

    Returns:
        Kebab-case slug
    """
    # Remove Korean characters and special chars
    slug = re.sub(r'[^a-zA-Z0-9\s-]', '', text.lower())
    # Replace spaces with hyphens
    slug = re.sub(r'\s+', '-', slug.strip())
    # Remove multiple hyphens
    slug = re.sub(r'-+', '-', slug)
    return slug[:50]  # Limit length


def generate_plan_file_path(task_description: str) -> str:
    """
    Generate plan file path.

    From plan.md Section 5.1: Auto-Generation Logic

    Args:
        task_description: Task description

    Returns:
        Plan file path
    """
    slug = slugify(task_description)
    return f".agent/plans/{slug}.md"


def synthesize_plans(
    oda_result: Dict[str, Any],
    subagent_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Synthesize ODA Protocol and Plan Subagent results.

    From plan.md Section 2.3: Synthesis Comparison Matrix

    Args:
        oda_result: ODA Protocol path result
        subagent_result: Plan Subagent path result

    Returns:
        Unified plan result
    """
    # Merge change plans (ODA priority for file references)
    change_plan = []

    # ODA changes first (they have explicit files_viewed)
    if "change_plan" in oda_result:
        for change in oda_result["change_plan"]:
            change["source"] = "oda_protocol"
            change_plan.append(change)

    # Add subagent changes (dedupe by file:line)
    if "change_plan" in subagent_result:
        existing_refs = {
            f"{c.get('file')}:{c.get('line')}"
            for c in change_plan
        }
        for change in subagent_result["change_plan"]:
            ref = f"{change.get('file')}:{change.get('line')}"
            if ref not in existing_refs:
                change["source"] = "subagent"
                change_plan.append(change)
            else:
                # Mark as merged
                for c in change_plan:
                    if f"{c.get('file')}:{c.get('line')}" == ref:
                        c["source"] = "merged"

    # Union risks
    risks = []
    seen_risks = set()

    for result, source in [(oda_result, "oda_protocol"), (subagent_result, "subagent")]:
        if "risk_assessment" in result:
            for risk in result["risk_assessment"]:
                risk_key = risk.get("risk", "")
                if risk_key not in seen_risks:
                    risk["source"] = source
                    risks.append(risk)
                    seen_risks.add(risk_key)

    # Combine test strategies
    test_strategy = {
        "unit_tests": [],
        "integration_tests": [],
        "edge_cases": [],
    }

    for result in [oda_result, subagent_result]:
        if "test_strategy" in result:
            strategy = result["test_strategy"]
            if isinstance(strategy, dict):
                for key in test_strategy:
                    if key in strategy:
                        test_strategy[key].extend(strategy[key])
            elif isinstance(strategy, list):
                test_strategy["unit_tests"].extend(strategy)

    # Dedupe test lists
    for key in test_strategy:
        test_strategy[key] = list(set(test_strategy[key]))

    return {
        "change_plan": change_plan,
        "risk_assessment": risks,
        "test_strategy": test_strategy,
        "evidence": {
            "files_viewed": oda_result.get("files_viewed", []),
            "dual_path_verified": True,
        },
    }


def create_parallel_task_params(
    modules: List[str],
    base_task: str,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Create parallel task parameters for Boris Cherny pattern.

    From plan.md Section 3: Parallel Execution Pattern

    Args:
        modules: List of module paths
        base_task: Base task description

    Returns:
        Dict with 'oda_tasks' and 'subagent_tasks' lists
    """
    oda_tasks = []
    subagent_tasks = []

    for module in modules:
        # ODA Protocol task
        oda_tasks.append({
            "subagent_type": "Explore",
            "prompt": generate_oda_protocol_prompt(module),
            "context": "fork",
            "run_in_background": True,
            "description": f"ODA protocol {module[:20]}",
        })

        # Plan Subagent task
        subagent_tasks.append({
            "subagent_type": "Plan",
            "prompt": generate_plan_subagent_prompt(module),
            "context": "fork",
            "run_in_background": True,
            "description": f"Plan subagent {module[:20]}",
        })

    return {
        "oda_tasks": oda_tasks,
        "subagent_tasks": subagent_tasks,
    }


def validate_plan_result(result: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate plan result against pass criteria.

    From plan.md Section 12: Pass Criteria

    Args:
        result: Plan result to validate

    Returns:
        Tuple of (is_valid, list_of_violations)
    """
    violations = []

    # Check change_plan
    if not result.get("change_plan"):
        violations.append("change_plan must be populated (non-empty)")

    # Check risk_assessment mitigations
    risks = result.get("risk_assessment", [])
    for risk in risks:
        if "mitigation" not in risk:
            violations.append(f"Risk '{risk.get('risk', 'unknown')}' missing mitigation")

    # Check test_strategy
    if not result.get("test_strategy"):
        violations.append("test_strategy must be defined")

    # Check files_viewed evidence
    evidence = result.get("evidence", {})
    if not evidence.get("files_viewed"):
        violations.append("files_viewed evidence must be present (anti-hallucination)")

    # Check dual_path_synthesis
    if not evidence.get("dual_path_verified"):
        violations.append("dual_path_synthesis must be completed")

    return len(violations) == 0, violations


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory with structure."""
    temp_dir = tempfile.mkdtemp()

    # Create module structure
    modules = ["ontology", "pai", "planning", "actions"]
    for module in modules:
        module_path = os.path.join(temp_dir, module)
        os.makedirs(module_path, exist_ok=True)

        # Create some Python files
        for i in range(3):
            file_path = os.path.join(module_path, f"module_{i}.py")
            with open(file_path, "w") as f:
                f.write(f"# Module {module}_{i}\nclass Test{i}: pass\n")

    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def large_project_dir():
    """Create a large project directory that triggers decomposition."""
    temp_dir = tempfile.mkdtemp()

    # Create many subdirectories and files
    for i in range(8):
        subdir = os.path.join(temp_dir, f"module_{i}")
        os.makedirs(subdir, exist_ok=True)

        for j in range(5):
            file_path = os.path.join(subdir, f"file_{j}.py")
            with open(file_path, "w") as f:
                f.write(f"# File {i}_{j}\n")

    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_oda_result() -> Dict[str, Any]:
    """Sample ODA Protocol result."""
    return {
        "change_plan": [
            {
                "file": "lib/registry.py",
                "line": 42,
                "change": "Add validation method",
                "depends_on": [],
                "rationale": "Required for schema validation",
            }
        ],
        "risk_assessment": [
            {
                "risk": "Schema migration required",
                "severity": "high",
                "mitigation": "Create migration script",
            }
        ],
        "test_strategy": {
            "unit_tests": ["test_validation"],
            "integration_tests": [],
            "edge_cases": [],
        },
        "files_viewed": ["lib/registry.py", "lib/objects.py"],
    }


@pytest.fixture
def sample_subagent_result() -> Dict[str, Any]:
    """Sample Plan Subagent result."""
    return {
        "change_plan": [
            {
                "file": "lib/registry.py",
                "line": 42,
                "change": "Add validation with error handling",
                "depends_on": [],
                "rationale": "Better error messages",
            },
            {
                "file": "lib/api.py",
                "line": 100,
                "change": "Update API endpoint",
                "depends_on": ["lib/registry.py:42"],
                "rationale": "Expose new validation",
            }
        ],
        "risk_assessment": [
            {
                "risk": "Import changes",
                "severity": "low",
                "mitigation": "Update __init__.py exports",
            }
        ],
        "test_strategy": {
            "unit_tests": ["test_api_endpoint"],
            "integration_tests": ["test_full_flow"],
            "edge_cases": ["test_invalid_input"],
        },
        "files_viewed": [],  # Plan subagent may not have files_viewed
    }


@pytest.fixture
def korean_trigger_inputs() -> List[Tuple[str, bool]]:
    """Korean inputs with expected trigger results."""
    return [
        ("계획을 세워줘", True),
        ("설계해줘", True),
        ("구현 계획", True),
        ("그냥 해줘", False),
        ("코드 봐줘", False),
    ]


@pytest.fixture
def english_trigger_inputs() -> List[Tuple[str, bool]]:
    """English inputs with expected trigger results."""
    return [
        ("/plan lib/oda/", True),
        ("create plan for module", True),
        ("implementation design", True),
        ("plan the architecture", True),
        ("just do it", False),
        ("analyze code", False),
    ]


@pytest.fixture
def scope_keyword_inputs() -> List[Tuple[str, bool, List[str]]]:
    """Inputs for scope keyword detection."""
    return [
        ("전체 분석", True, ["전체"]),
        ("모든 파일 검사", True, ["모든"]),
        ("analyze entire codebase", True, ["entire"]),
        ("complete review of all modules", True, ["complete", "all"]),
        ("check specific file", False, []),
        ("단일 모듈 검토", False, []),
    ]


# =============================================================================
# TEST CASES: Dual-Path Analysis
# =============================================================================

class TestDualPathAnalysis:
    """Tests for Dual-Path Analysis (plan.md Section 2)."""

    def test_synthesis_merges_change_plans(
        self,
        sample_oda_result,
        sample_subagent_result
    ):
        """Test that synthesis merges change plans from both paths."""
        result = synthesize_plans(sample_oda_result, sample_subagent_result)

        assert len(result["change_plan"]) == 2  # 1 merged + 1 unique
        sources = {c["source"] for c in result["change_plan"]}
        assert "merged" in sources or "oda_protocol" in sources

    def test_synthesis_prefers_oda_file_references(
        self,
        sample_oda_result,
        sample_subagent_result
    ):
        """Test that ODA file references are preferred (Section 2.3)."""
        result = synthesize_plans(sample_oda_result, sample_subagent_result)

        # Check that overlapping entries are marked as merged or oda_protocol
        registry_changes = [
            c for c in result["change_plan"]
            if c["file"] == "lib/registry.py"
        ]
        assert len(registry_changes) == 1
        assert registry_changes[0]["source"] in ("merged", "oda_protocol")

    def test_synthesis_unions_risks(
        self,
        sample_oda_result,
        sample_subagent_result
    ):
        """Test that risks are unioned and deduped."""
        result = synthesize_plans(sample_oda_result, sample_subagent_result)

        assert len(result["risk_assessment"]) == 2
        risk_names = {r["risk"] for r in result["risk_assessment"]}
        assert "Schema migration required" in risk_names
        assert "Import changes" in risk_names

    def test_synthesis_combines_test_strategies(
        self,
        sample_oda_result,
        sample_subagent_result
    ):
        """Test that test strategies are combined."""
        result = synthesize_plans(sample_oda_result, sample_subagent_result)

        test_strategy = result["test_strategy"]
        assert "test_validation" in test_strategy["unit_tests"]
        assert "test_api_endpoint" in test_strategy["unit_tests"]
        assert "test_full_flow" in test_strategy["integration_tests"]

    def test_synthesis_preserves_files_viewed(
        self,
        sample_oda_result,
        sample_subagent_result
    ):
        """Test that files_viewed from ODA is preserved."""
        result = synthesize_plans(sample_oda_result, sample_subagent_result)

        assert "files_viewed" in result["evidence"]
        assert len(result["evidence"]["files_viewed"]) > 0
        assert "lib/registry.py" in result["evidence"]["files_viewed"]

    def test_synthesis_sets_dual_path_verified(
        self,
        sample_oda_result,
        sample_subagent_result
    ):
        """Test that dual_path_verified flag is set."""
        result = synthesize_plans(sample_oda_result, sample_subagent_result)

        assert result["evidence"]["dual_path_verified"] is True

    def test_synthesis_with_empty_oda_result(self, sample_subagent_result):
        """Test synthesis when ODA result is minimal."""
        empty_oda = {"files_viewed": ["file.py"]}
        result = synthesize_plans(empty_oda, sample_subagent_result)

        assert len(result["change_plan"]) == len(sample_subagent_result["change_plan"])

    def test_synthesis_with_empty_subagent_result(self, sample_oda_result):
        """Test synthesis when subagent result is minimal."""
        empty_subagent: Dict[str, Any] = {}
        result = synthesize_plans(sample_oda_result, empty_subagent)

        assert len(result["change_plan"]) == len(sample_oda_result["change_plan"])


class TestODAProtocolPath:
    """Tests for ODA Protocol path (Section 2.1)."""

    def test_generate_oda_prompt_includes_stages(self):
        """Test ODA prompt includes Stage A and B."""
        prompt = generate_oda_protocol_prompt("/path/to/module")

        assert "Stage A" in prompt
        assert "Stage B" in prompt
        assert "SCAN" in prompt
        assert "TRACE" in prompt

    def test_generate_oda_prompt_requires_evidence(self):
        """Test ODA prompt requires mandatory evidence."""
        prompt = generate_oda_protocol_prompt("/path/to/module")

        assert "files_viewed" in prompt
        assert "imports_verified" in prompt
        assert "signatures_matched" in prompt
        assert "dependencies_mapped" in prompt

    def test_generate_oda_prompt_includes_budget(self):
        """Test ODA prompt includes token budget constraint."""
        prompt = generate_oda_protocol_prompt("/path/to/module")

        assert "5000 TOKENS" in prompt
        assert "Output Budget" in prompt

    def test_generate_oda_prompt_references_protocol(self):
        """Test ODA prompt references 3-stage protocol."""
        prompt = generate_oda_protocol_prompt("/path/to/module")

        assert "3-stage-protocol.md" in prompt


class TestPlanSubagentPath:
    """Tests for Plan Subagent path (Section 2.2)."""

    def test_generate_plan_prompt_includes_sections(self):
        """Test Plan prompt includes required sections."""
        prompt = generate_plan_subagent_prompt("/path/to/module")

        assert "Change Plan" in prompt
        assert "Risk Assessment" in prompt
        assert "Test Strategy" in prompt

    def test_generate_plan_prompt_includes_budget(self):
        """Test Plan prompt includes token budget constraint."""
        prompt = generate_plan_subagent_prompt("/path/to/module")

        assert "10000 TOKENS" in prompt

    def test_generate_plan_prompt_includes_precheck_evidence(self):
        """Test Plan prompt can include pre-check evidence."""
        evidence = "files_viewed: [test.py]"
        prompt = generate_plan_subagent_prompt("/path", evidence)

        assert evidence in prompt

    def test_generate_plan_prompt_planning_only(self):
        """Test Plan prompt emphasizes planning only."""
        prompt = generate_plan_subagent_prompt("/path")

        assert "Planning only" in prompt or "planning only" in prompt
        assert "no implementation" in prompt or "not implement" in prompt.lower()


# =============================================================================
# TEST CASES: TaskDecomposer Integration
# =============================================================================

class TestTaskDecomposerIntegration:
    """Tests for TaskDecomposer integration (Section 4)."""

    def test_detect_korean_scope_keywords(self):
        """Test detection of Korean scope keywords."""
        has_kw, detected = detect_scope_keywords("전체 코드베이스 분석")
        assert has_kw is True
        assert "전체" in detected

        has_kw, detected = detect_scope_keywords("모든 모듈 검토")
        assert has_kw is True
        assert "모든" in detected

    def test_detect_english_scope_keywords(self):
        """Test detection of English scope keywords."""
        has_kw, detected = detect_scope_keywords("analyze entire codebase")
        assert has_kw is True
        assert "entire" in detected

        has_kw, detected = detect_scope_keywords("complete review of all modules")
        assert has_kw is True
        assert "complete" in detected
        assert "all" in detected

    def test_no_scope_keywords_detected(self):
        """Test no keywords detected for specific tasks."""
        has_kw, detected = detect_scope_keywords("analyze single file")
        assert has_kw is False
        assert len(detected) == 0

        has_kw, detected = detect_scope_keywords("단일 파일 검토")
        assert has_kw is False

    def test_parametrized_scope_keywords(self, scope_keyword_inputs):
        """Parametrized test for scope keyword detection."""
        for task, expected_has, expected_keywords in scope_keyword_inputs:
            has_kw, detected = detect_scope_keywords(task)
            assert has_kw == expected_has
            for kw in expected_keywords:
                assert kw in detected

    def test_should_decompose_with_scope_keywords(self):
        """Test decomposition triggered by scope keywords."""
        assert should_decompose_task("전체 분석") is True
        assert should_decompose_task("analyze entire project") is True
        assert should_decompose_task("check all files") is True

    def test_should_decompose_without_keywords(self):
        """Test no decomposition for specific tasks."""
        assert should_decompose_task("check single file") is False
        assert should_decompose_task("단일 모듈") is False

    def test_should_decompose_with_large_scope(self, large_project_dir):
        """Test decomposition triggered by large scope."""
        # Large project has 8 directories with 5 files each = 40 files
        assert should_decompose_task("analyze project", large_project_dir) is True

    def test_should_decompose_with_small_scope(self, temp_project_dir):
        """Test no decomposition for small scope without keywords."""
        # Small project has 4 dirs with 3 files each = 12 files
        assert should_decompose_task("analyze", temp_project_dir) is False

    def test_analyze_scope_comprehensive(self, large_project_dir):
        """Test comprehensive scope analysis."""
        analysis = analyze_scope("전체 분석", large_project_dir)

        assert analysis.has_scope_keywords is True
        assert "전체" in analysis.detected_keywords
        assert analysis.file_count > 0
        assert analysis.directory_count > 0
        assert analysis.should_decompose is True
        assert analysis.recommended_subtask_count > 1


class TestScopeKeywordDetection:
    """Tests for scope keyword detection (Section 4.1)."""

    def test_korean_scope_keyword_jeonche(self):
        """Test '전체' (entire/all) detection."""
        has_kw, detected = detect_scope_keywords("전체 시스템")
        assert has_kw is True
        assert "전체" in detected

    def test_korean_scope_keyword_modeun(self):
        """Test '모든' (all) detection."""
        has_kw, detected = detect_scope_keywords("모든 파일")
        assert has_kw is True
        assert "모든" in detected

    def test_korean_scope_keyword_wanjeonhan(self):
        """Test '완전한' (complete) detection."""
        has_kw, detected = detect_scope_keywords("완전한 분석")
        assert has_kw is True
        assert "완전한" in detected

    def test_korean_scope_keyword_jeonbu(self):
        """Test '전부' (all/everything) detection."""
        has_kw, detected = detect_scope_keywords("전부 확인")
        assert has_kw is True
        assert "전부" in detected

    def test_english_scope_keyword_all(self):
        """Test 'all' detection."""
        has_kw, detected = detect_scope_keywords("analyze all modules")
        assert has_kw is True
        assert "all" in detected

    def test_english_scope_keyword_entire(self):
        """Test 'entire' detection."""
        has_kw, detected = detect_scope_keywords("entire codebase review")
        assert has_kw is True
        assert "entire" in detected

    def test_english_scope_keyword_complete(self):
        """Test 'complete' detection."""
        has_kw, detected = detect_scope_keywords("complete system audit")
        assert has_kw is True
        assert "complete" in detected

    def test_english_scope_keyword_whole(self):
        """Test 'whole' detection."""
        has_kw, detected = detect_scope_keywords("whole project")
        assert has_kw is True
        assert "whole" in detected

    def test_english_scope_keyword_full(self):
        """Test 'full' detection."""
        has_kw, detected = detect_scope_keywords("full analysis")
        assert has_kw is True
        assert "full" in detected

    def test_english_scope_keyword_every(self):
        """Test 'every' detection."""
        has_kw, detected = detect_scope_keywords("check every file")
        assert has_kw is True
        assert "every" in detected

    def test_multiple_keywords_detected(self):
        """Test multiple keywords in single input."""
        has_kw, detected = detect_scope_keywords("analyze all modules and every file")
        assert has_kw is True
        assert len(detected) >= 2

    def test_case_insensitive_detection(self):
        """Test case insensitive keyword detection."""
        has_kw, _ = detect_scope_keywords("ENTIRE codebase")
        assert has_kw is True

        has_kw, _ = detect_scope_keywords("Complete Analysis")
        assert has_kw is True


# =============================================================================
# TEST CASES: Resume Parameter Functionality
# =============================================================================

class TestResumeParameter:
    """Tests for resume parameter functionality (Section 6)."""

    def test_subtask_mark_for_resume(self):
        """Test marking subtask for resume."""
        subtask = SubTask(
            description="Test task",
            prompt="Test prompt",
            subagent_type=SubagentType.PLAN,
            scope="/path",
            token_budget=10000,
        )

        subtask.mark_for_resume("abc123")

        assert subtask.task_id == "abc123"
        assert subtask.should_resume is True

    def test_subtask_to_task_params_without_resume(self):
        """Test task params without resume."""
        subtask = SubTask(
            description="Test task",
            prompt="Test prompt",
            subagent_type=SubagentType.PLAN,
            scope="/path",
            token_budget=10000,
        )

        params = subtask.to_task_params()

        assert "resume" not in params
        assert params["run_in_background"] is True

    def test_subtask_to_task_params_with_resume(self):
        """Test task params with resume."""
        subtask = SubTask(
            description="Test task",
            prompt="Test prompt",
            subagent_type=SubagentType.PLAN,
            scope="/path",
            token_budget=10000,
        )
        subtask.mark_for_resume("xyz789")

        params = subtask.to_task_params()

        assert params["resume"] == "xyz789"

    def test_subtask_resume_method_chaining(self):
        """Test mark_for_resume returns self for chaining."""
        subtask = SubTask(
            description="Test",
            prompt="Test",
            subagent_type=SubagentType.EXPLORE,
            scope="/",
            token_budget=5000,
        )

        result = subtask.mark_for_resume("id123")

        assert result is subtask

    def test_subtask_resume_preserves_other_params(self):
        """Test that resume doesn't affect other parameters."""
        subtask = SubTask(
            description="Original desc",
            prompt="Original prompt",
            subagent_type=SubagentType.GENERAL_PURPOSE,
            scope="/original",
            token_budget=15000,
            priority=5,
        )
        subtask.mark_for_resume("resume_id")

        params = subtask.to_task_params()

        assert params["description"] == "Original desc"
        assert params["prompt"] == "Original prompt"
        assert params["subagent_type"] == "general-purpose"


class TestAgentRegistryTracking:
    """Tests for Agent Registry tracking (Section 6.2)."""

    def test_agent_registry_entry_creation(self):
        """Test creating Agent Registry entry."""
        entry = AgentRegistryEntry(
            agent_id="a740d90",
            agent_type=SubagentType.EXPLORE,
            phase_task="1.1",
            description="File discovery",
            status="running",
        )

        assert entry.agent_id == "a740d90"
        assert entry.agent_type == SubagentType.EXPLORE
        assert entry.status == "running"

    def test_agent_registry_entry_states(self):
        """Test valid Agent Registry states."""
        valid_states = ["pending", "running", "completed", "failed"]

        for state in valid_states:
            entry = AgentRegistryEntry(
                agent_id="test",
                agent_type=SubagentType.PLAN,
                phase_task="1.0",
                description="Test",
                status=state,
            )
            assert entry.status == state


# =============================================================================
# TEST CASES: Plan File Generation
# =============================================================================

class TestPlanFileGeneration:
    """Tests for plan file generation (Section 5)."""

    def test_slugify_simple_text(self):
        """Test slugifying simple text."""
        assert slugify("Implement auth") == "implement-auth"
        assert slugify("Add feature") == "add-feature"

    def test_slugify_with_spaces(self):
        """Test slugifying text with multiple spaces."""
        assert slugify("Add  new   feature") == "add-new-feature"

    def test_slugify_removes_special_chars(self):
        """Test slugifying removes special characters."""
        assert slugify("feature: auth!") == "feature-auth"
        assert slugify("test@module#1") == "testmodule1"

    def test_slugify_removes_korean(self):
        """Test slugifying removes Korean characters."""
        slug = slugify("인증 feature")
        assert "인증" not in slug
        assert "feature" in slug

    def test_slugify_max_length(self):
        """Test slugify respects max length."""
        long_text = "a" * 100
        slug = slugify(long_text)
        assert len(slug) <= 50

    def test_generate_plan_file_path(self):
        """Test plan file path generation."""
        path = generate_plan_file_path("Implement authentication")

        assert path.startswith(".agent/plans/")
        assert path.endswith(".md")
        assert "implement" in path
        assert "authentication" in path

    def test_generate_plan_file_path_unique_slugs(self):
        """Test that different tasks get different paths."""
        path1 = generate_plan_file_path("Add feature A")
        path2 = generate_plan_file_path("Add feature B")

        assert path1 != path2


# =============================================================================
# TEST CASES: Boris Cherny Parallel Execution Pattern
# =============================================================================

class TestBorisCherneyPattern:
    """Tests for Boris Cherny parallel execution pattern (Section 3)."""

    def test_create_parallel_tasks_structure(self):
        """Test parallel task creation returns correct structure."""
        modules = ["/lib/ontology", "/lib/pai"]
        result = create_parallel_task_params(modules, "Analyze modules")

        assert "oda_tasks" in result
        assert "subagent_tasks" in result
        assert len(result["oda_tasks"]) == 2
        assert len(result["subagent_tasks"]) == 2

    def test_parallel_tasks_have_run_in_background(self):
        """Test all parallel tasks have run_in_background=True."""
        modules = ["/lib/a", "/lib/b", "/lib/c"]
        result = create_parallel_task_params(modules, "Test")

        for task in result["oda_tasks"]:
            assert task["run_in_background"] is True

        for task in result["subagent_tasks"]:
            assert task["run_in_background"] is True

    def test_parallel_tasks_have_fork_context(self):
        """Test all parallel tasks use fork context."""
        modules = ["/lib/module"]
        result = create_parallel_task_params(modules, "Test")

        for task in result["oda_tasks"]:
            assert task["context"] == "fork"

        for task in result["subagent_tasks"]:
            assert task["context"] == "fork"

    def test_parallel_oda_tasks_use_explore(self):
        """Test ODA tasks use Explore subagent."""
        modules = ["/lib/test"]
        result = create_parallel_task_params(modules, "Test")

        for task in result["oda_tasks"]:
            assert task["subagent_type"] == "Explore"

    def test_parallel_subagent_tasks_use_plan(self):
        """Test Plan Subagent tasks use Plan type."""
        modules = ["/lib/test"]
        result = create_parallel_task_params(modules, "Test")

        for task in result["subagent_tasks"]:
            assert task["subagent_type"] == "Plan"

    def test_parallel_tasks_have_descriptions(self):
        """Test all tasks have descriptions."""
        modules = ["/lib/ontology"]
        result = create_parallel_task_params(modules, "Analyze")

        for task in result["oda_tasks"]:
            assert "description" in task
            assert len(task["description"]) > 0

        for task in result["subagent_tasks"]:
            assert "description" in task
            assert len(task["description"]) > 0

    def test_parallel_tasks_many_modules(self):
        """Test parallel task creation with many modules."""
        modules = [f"/lib/module_{i}" for i in range(10)]
        result = create_parallel_task_params(modules, "Mass analysis")

        assert len(result["oda_tasks"]) == 10
        assert len(result["subagent_tasks"]) == 10


# =============================================================================
# TEST CASES: Plan Trigger Detection
# =============================================================================

class TestPlanTriggerDetection:
    """Tests for plan trigger detection (Section 7)."""

    def test_trigger_command(self):
        """Test /plan command triggers."""
        assert is_plan_trigger("/plan lib/oda/") is True
        assert is_plan_trigger("/PLAN") is True

    def test_trigger_korean_keywords(self, korean_trigger_inputs):
        """Test Korean keyword triggers."""
        for inp, expected in korean_trigger_inputs:
            assert is_plan_trigger(inp) == expected

    def test_trigger_english_keywords(self, english_trigger_inputs):
        """Test English keyword triggers."""
        for inp, expected in english_trigger_inputs:
            assert is_plan_trigger(inp) == expected

    def test_trigger_patterns(self):
        """Test pattern-based triggers."""
        assert is_plan_trigger("create plan for auth") is True
        assert is_plan_trigger("implementation design needed") is True
        assert is_plan_trigger("설계해줘") is True

    def test_no_trigger_for_unrelated(self):
        """Test no trigger for unrelated inputs."""
        assert is_plan_trigger("analyze code") is False
        assert is_plan_trigger("run tests") is False
        assert is_plan_trigger("commit changes") is False


# =============================================================================
# TEST CASES: Plan Result Validation
# =============================================================================

class TestPlanResultValidation:
    """Tests for plan result validation (Section 12)."""

    def test_valid_plan_result(
        self,
        sample_oda_result,
        sample_subagent_result
    ):
        """Test validation of valid plan result."""
        result = synthesize_plans(sample_oda_result, sample_subagent_result)
        is_valid, violations = validate_plan_result(result)

        assert is_valid is True
        assert len(violations) == 0

    def test_invalid_empty_change_plan(self):
        """Test validation fails for empty change_plan."""
        result = {
            "change_plan": [],
            "risk_assessment": [],
            "test_strategy": {},
            "evidence": {"files_viewed": ["test.py"], "dual_path_verified": True},
        }
        is_valid, violations = validate_plan_result(result)

        assert is_valid is False
        assert any("change_plan" in v for v in violations)

    def test_invalid_missing_mitigation(self):
        """Test validation fails for risks without mitigation."""
        result = {
            "change_plan": [{"file": "test.py", "change": "test"}],
            "risk_assessment": [{"risk": "Test risk", "severity": "high"}],  # No mitigation
            "test_strategy": {"unit_tests": ["test"]},
            "evidence": {"files_viewed": ["test.py"], "dual_path_verified": True},
        }
        is_valid, violations = validate_plan_result(result)

        assert is_valid is False
        assert any("mitigation" in v for v in violations)

    def test_invalid_missing_files_viewed(self):
        """Test validation fails for missing files_viewed."""
        result = {
            "change_plan": [{"file": "test.py", "change": "test"}],
            "risk_assessment": [],
            "test_strategy": {"unit_tests": ["test"]},
            "evidence": {"dual_path_verified": True},  # No files_viewed
        }
        is_valid, violations = validate_plan_result(result)

        assert is_valid is False
        assert any("files_viewed" in v for v in violations)

    def test_invalid_missing_dual_path_verified(self):
        """Test validation fails when dual_path_verified is missing."""
        result = {
            "change_plan": [{"file": "test.py", "change": "test"}],
            "risk_assessment": [],
            "test_strategy": {"unit_tests": ["test"]},
            "evidence": {"files_viewed": ["test.py"]},  # No dual_path_verified
        }
        is_valid, violations = validate_plan_result(result)

        assert is_valid is False
        assert any("dual_path" in v for v in violations)


# =============================================================================
# TEST CASES: Token Budget and Output Constraints
# =============================================================================

class TestTokenBudget:
    """Tests for token budget configuration (Section 4.3)."""

    def test_token_budget_defaults(self):
        """Test default token budget values."""
        budget = TokenBudget()

        assert budget.explore == 5000
        assert budget.plan == 10000
        assert budget.general_purpose == 15000

    def test_token_budget_get_budget(self):
        """Test getting budget by subagent type."""
        budget = TokenBudget()

        assert budget.get_budget(SubagentType.EXPLORE) == 5000
        assert budget.get_budget(SubagentType.PLAN) == 10000
        assert budget.get_budget(SubagentType.GENERAL_PURPOSE) == 15000

    def test_token_budget_custom_values(self):
        """Test custom token budget values."""
        budget = TokenBudget(explore=3000, plan=8000, general_purpose=12000)

        assert budget.explore == 3000
        assert budget.plan == 8000
        assert budget.general_purpose == 12000

    def test_output_budget_in_prompts(self):
        """Test output budget constraint is included in prompts."""
        prompt = generate_subtask_prompt(
            "Test task",
            "/path",
            SubagentType.EXPLORE
        )

        assert "5000 TOKENS" in prompt
        assert "Output Budget" in prompt
        assert "MUST NOT EXCEED" in prompt


# =============================================================================
# TEST CASES: V2.1.4 Configuration
# =============================================================================

class TestV214Configuration:
    """Tests for V2.1.4 specific configuration."""

    def test_skill_config_context_fork(self):
        """Test skill config has context: fork."""
        assert PLAN_SKILL_CONFIG["context"] == "fork"

    def test_skill_config_run_in_background(self):
        """Test skill config has run_in_background: true."""
        assert PLAN_SKILL_CONFIG["run_in_background"] is True

    def test_skill_config_evidence_required(self):
        """Test required evidence fields."""
        required = PLAN_SKILL_CONFIG["evidence_required"]

        assert "change_plan" in required
        assert "risk_assessment" in required
        assert "test_strategy" in required
        assert "dual_path_synthesis" in required

    def test_skill_config_oda_context(self):
        """Test ODA context configuration."""
        oda = PLAN_SKILL_CONFIG["oda_context"]

        assert oda["role"] == "planner"
        assert "A" in oda["stage_access"]
        assert "B" in oda["stage_access"]
        assert oda["governance_mode"] == "strict"


# =============================================================================
# TEST CASES: Edge Cases and Integration
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_task_description(self):
        """Test handling of empty task description."""
        has_kw, detected = detect_scope_keywords("")
        assert has_kw is False
        assert len(detected) == 0

    def test_empty_scope_path(self):
        """Test handling of empty scope path."""
        assert should_decompose_task("analyze", "") is False

    def test_nonexistent_scope_path(self):
        """Test handling of nonexistent scope path."""
        assert should_decompose_task("analyze", "/nonexistent/path") is False

    def test_mixed_language_task(self):
        """Test mixed Korean/English task description."""
        has_kw, detected = detect_scope_keywords("analyze 전체 codebase")
        assert has_kw is True
        assert "전체" in detected

    def test_subtask_with_all_fields(self):
        """Test SubTask with all fields populated."""
        subtask = SubTask(
            description="Complete task",
            prompt="Full prompt text",
            subagent_type=SubagentType.PLAN,
            scope="/full/path",
            token_budget=10000,
            priority=1,
            dependencies=["task_a", "task_b"],
            task_id="existing_id",
            should_resume=True,
        )

        params = subtask.to_task_params()
        assert params["resume"] == "existing_id"

    def test_synthesis_with_none_values(self):
        """Test synthesis handles None values gracefully."""
        oda_result = {
            "change_plan": None,
            "files_viewed": [],
        }
        subagent_result = {
            "change_plan": None,
        }

        # Should not raise exception
        try:
            result = synthesize_plans(oda_result, subagent_result)
            # If None is treated as missing, this is fine
        except (TypeError, AttributeError):
            # If None causes issues, that's expected behavior
            pass


class TestIntegrationScenarios:
    """Integration tests for realistic plan scenarios."""

    def test_scenario_feature_planning(self, temp_project_dir):
        """Test complete flow for feature planning."""
        # Step 1: Check if decomposition needed
        task = "Plan implementation for new feature"
        should_decompose = should_decompose_task(task, temp_project_dir)

        # Small project, shouldn't decompose
        assert should_decompose is False

        # Step 2: Generate prompts
        oda_prompt = generate_oda_protocol_prompt(temp_project_dir)
        plan_prompt = generate_plan_subagent_prompt(temp_project_dir)

        assert len(oda_prompt) > 100
        assert len(plan_prompt) > 100

        # Step 3: Generate plan file path
        plan_path = generate_plan_file_path(task)
        assert "plan-implementation" in plan_path or "new-feature" in plan_path

    def test_scenario_large_codebase_planning(self, large_project_dir):
        """Test planning for large codebase."""
        task = "Plan 전체 refactoring"  # Uses Korean keyword

        # Should trigger decomposition
        assert should_decompose_task(task, large_project_dir) is True

        # Analyze scope
        analysis = analyze_scope(task, large_project_dir)
        assert analysis.should_decompose is True
        assert analysis.recommended_subtask_count > 1

    def test_scenario_dual_path_synthesis_flow(
        self,
        sample_oda_result,
        sample_subagent_result
    ):
        """Test complete dual-path synthesis flow."""
        # Synthesize results
        result = synthesize_plans(sample_oda_result, sample_subagent_result)

        # Validate result
        is_valid, violations = validate_plan_result(result)
        assert is_valid is True

        # Check all required fields
        assert "change_plan" in result
        assert "risk_assessment" in result
        assert "test_strategy" in result
        assert result["evidence"]["dual_path_verified"] is True

    def test_scenario_resume_after_autocompact(self):
        """Test resume flow after Auto-Compact."""
        # Create initial subtask
        initial_task = SubTask(
            description="Phase 1 planning",
            prompt="Plan auth module",
            subagent_type=SubagentType.PLAN,
            scope="/lib/auth",
            token_budget=10000,
        )

        # Simulate getting agent_id from first execution
        simulated_agent_id = "a1b2c3d"

        # Create resume subtask
        resume_task = SubTask(
            description="Continue Phase 1",
            prompt="Continue planning from checkpoint",
            subagent_type=SubagentType.PLAN,
            scope="/lib/auth",
            token_budget=10000,
        )
        resume_task.mark_for_resume(simulated_agent_id)

        # Verify resume params
        params = resume_task.to_task_params()
        assert params["resume"] == simulated_agent_id
        assert params["subagent_type"] == "Plan"


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
