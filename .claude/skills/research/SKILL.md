---
name: research
description: |
  Deep codebase analysis and external resource gathering.
  Post-/clarify research phase for informed planning.
  Generates L1/L2/L3 progressive disclosure research reports.
user-invocable: true
disable-model-invocation: false
context: fork
model: opus
version: "2.0.0"
argument-hint: "[--scope <path>] [--external] [--clarify-slug <slug>]"
allowed-tools:
  - Read
  - Grep
  - Glob
  - WebSearch
  - WebFetch
  - Task
  - Bash
hooks:
  Setup:
    - type: command
      command: "/home/palantir/.claude/hooks/research-validate.sh"
      timeout: 10000
    - shared/parallel-agent.sh  # P2: Load parallel agent module
  Stop:
    - type: command
      command: "/home/palantir/.claude/hooks/research-finalize.sh"
      timeout: 180000
# P1: Agent Delegation (Sub-Orchestrator Mode)
agent_delegation:
  enabled: true  # Can operate as sub-orchestrator
  max_sub_agents: 5  # Maximum parallel sub-agents
  delegation_strategy: "scope-based"  # Delegate by codebase scope or topic
  description: |
    When research scope is large, break into sub-research tasks.
    Each sub-agent handles specific scope (e.g., frontend, backend, API).
# P2: Parallel Agent Configuration
parallel_agent_config:
  enabled: true  # Use parallel agents for faster research
  complexity_detection: "auto"  # Automatically detect complexity level
  agent_count_by_complexity:
    simple: 2      # Basic research (single module)
    moderate: 3    # Standard research (2-3 modules)
    complex: 4     # Complex research (multiple systems)
    very_complex: 5  # Comprehensive research (entire codebase)
  synchronization_strategy: "barrier"  # Wait for all agents (default)
  aggregation_strategy: "merge"  # Merge all research findings
  description: |
    Parallel agent execution for faster comprehensive analysis.
    Complexity-based scaling: 2-5 agents based on research scope.
---

# /research - Deep Codebase & External Analysis (V1.0.0)

> **Role:** Deep codebase analysis + external resource gathering
> **Position in Pipeline:** `/clarify` → `/research` → `/planning`
> **Output Format:** L1/L2/L3 Progressive Disclosure
> **Model:** Opus (for comprehensive analysis)

---

## 1. Purpose

The `/research` skill performs comprehensive analysis to inform implementation planning:

1. **Codebase Pattern Analysis** - Identify existing patterns, conventions, and dependencies
2. **External Resource Gathering** - Search documentation, best practices, and similar implementations
3. **Risk Assessment** - Identify potential blockers, breaking changes, and edge cases
4. **Integration Points** - Map where new code should connect with existing systems

---

## 2. Execution Protocol

### 2.1 Argument Parsing

```bash
# $ARGUMENTS parsing
SCOPE=""
EXTERNAL=false
CLARIFY_SLUG=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --scope)
            SCOPE="$2"
            shift 2
            ;;
        --external)
            EXTERNAL=true
            shift
            ;;
        --clarify-slug)
            CLARIFY_SLUG="$2"
            shift 2
            ;;
        *)
            QUERY="$1"
            shift
            ;;
    esac
done
```

### 2.2 Initialize Research Session

```bash
# Source centralized slug generator
source "${WORKSPACE_ROOT:-.}/.claude/skills/shared/slug-generator.sh"

# Generate research ID using centralized slug generator
if [[ -n "$CLARIFY_SLUG" ]]; then
    # Reuse workload ID from /clarify
    CLARIFY_YAML=".agent/clarify/${CLARIFY_SLUG}.yaml"

    if [[ -f "$CLARIFY_YAML" ]]; then
        # Try to extract workload_id from clarify YAML (nested or top-level)
        # Priority 1: yq for reliable nested YAML parsing
        if command -v yq &> /dev/null; then
            WORKLOAD_ID=$(yq -r '.metadata.workload_id // .workload_id // .metadata.id // empty' "$CLARIFY_YAML" 2>/dev/null || echo "")
        fi

        # Priority 2: grep fallback for nested workload_id
        if [[ -z "$WORKLOAD_ID" ]]; then
            WORKLOAD_ID=$(grep -oP '^\s*workload_id:\s*["\x27]?\K[^"\x27\s]+' "$CLARIFY_YAML" | head -1 || echo "")
        fi

        # Priority 3: grep for metadata.id (common in clarify YAML)
        if [[ -z "$WORKLOAD_ID" ]]; then
            # Extract id from metadata section
            WORKLOAD_ID=$(awk '/^metadata:/,/^[a-z]/{if(/^\s+id:/) print $2}' "$CLARIFY_YAML" | tr -d '"' | head -1 || echo "")
        fi

        # Priority 4: use clarify slug as fallback
        if [[ -z "$WORKLOAD_ID" ]]; then
            WORKLOAD_ID="${CLARIFY_SLUG}"
        fi
    else
        # Clarify file not found, use slug as workload ID
        WORKLOAD_ID="${CLARIFY_SLUG}"
    fi

    # Derive research slug from workload ID
    RESEARCH_ID=$(generate_slug_from_workload "$WORKLOAD_ID")

    # Initialize workload directory (ensure directories exist)
    source "${WORKSPACE_ROOT:-.}/.claude/skills/shared/workload-tracker.sh"
    init_workload_directories "$WORKLOAD_ID"
else
    # Independent execution: generate new workload ID
    WORKLOAD_ID=$(generate_workload_id "$QUERY")
    RESEARCH_ID=$(generate_slug_from_workload "$WORKLOAD_ID")

    # Initialize workload context for independent research
    init_workload "$WORKLOAD_ID" "research" "$QUERY"
fi

# Store workload ID in output file metadata (Workload-scoped)
WORKLOAD_DIR=".agent/prompts/${RESEARCH_ID}"
OUTPUT_PATH="${WORKLOAD_DIR}/research.md"
mkdir -p "${WORKLOAD_DIR}"

# Log workload context
echo "Research Session Initialized:" >&2
echo "  Workload ID: $WORKLOAD_ID" >&2
echo "  Research Slug: $RESEARCH_ID" >&2
echo "  Output: $OUTPUT_PATH" >&2
```

### 2.3 Load Clarify Context (if available)

```python
if CLARIFY_SLUG:
    clarify_path = f".agent/clarify/{CLARIFY_SLUG}.yaml"
    if file_exists(clarify_path):
        clarify_data = Read(clarify_path)
        requirements = extract_requirements(clarify_data)
        context = extract_context(clarify_data)
```

---

## 3. Research Phases

### Phase 1: Codebase Pattern Analysis

```python
# 3.1 Structure Discovery
patterns = []

# Find relevant file patterns
files = Glob(pattern=f"**/*{topic}*")
related_files = Glob(pattern="**/*.{ts,js,py,md}")

# Search for existing implementations
existing = Grep(pattern=f"(class|function|def).*{keyword}", type="ts,js,py")

# Identify conventions
conventions = {
    "naming": analyze_naming_patterns(files),
    "structure": analyze_directory_structure(files),
    "imports": analyze_import_patterns(files),
    "error_handling": analyze_error_patterns(files)
}

# Find integration points
integration_points = Grep(pattern="(export|import|module\\.exports)", path=scope)
```

### Phase 2: External Resource Gathering (if --external)

```python
if EXTERNAL:
    # 3.2 Documentation Search
    docs = WebSearch(query=f"{topic} documentation best practices 2026")

    # Library/Framework specific
    if framework_detected:
        framework_docs = WebSearch(query=f"{framework} {topic} implementation guide")

    # Similar implementations
    similar = WebSearch(query=f"{topic} implementation example github")

    # Fetch and summarize key resources
    for url in top_results[:3]:
        content = WebFetch(url=url, prompt="Extract key implementation details and patterns")
        external_findings.append(content)
```

### Phase 3: Risk Assessment

```python
# 3.3 Risk Identification
risks = []

# Breaking change detection
breaking_changes = analyze_breaking_changes(affected_files)

# Dependency conflicts
dependency_risks = check_dependency_conflicts(requirements)

# Security considerations
security_risks = check_security_patterns(implementation_area)

# Complexity assessment
complexity = calculate_complexity(scope, requirements)

risks = {
    "breaking_changes": breaking_changes,
    "dependency_conflicts": dependency_risks,
    "security_concerns": security_risks,
    "complexity_level": complexity
}
```

### Phase 4: Findings Synthesis

```python
# 3.4 Compile Research Report
report = {
    "codebase_analysis": patterns,
    "external_findings": external_findings,
    "risk_assessment": risks,
    "integration_points": integration_points,
    "recommendations": generate_recommendations(patterns, risks),
    "next_steps": suggest_planning_approach()
}
```

---

## 3.5 P1/P2 Integration: Agent Delegation & Parallel Execution (NEW in v2.0.0)

### 3.5.1 Complexity Detection

```bash
#!/bin/bash
# Automatically detect research complexity for P2

detect_research_complexity() {
    local query="$1"
    local scope="$2"

    # Count affected areas
    local file_count=0
    local module_count=0
    local external_deps=0

    if [[ -n "$scope" ]]; then
        file_count=$(find "$scope" -type f \( -name "*.ts" -o -name "*.js" -o -name "*.py" \) 2>/dev/null | wc -l)
        module_count=$(find "$scope" -mindepth 1 -maxdepth 2 -type d 2>/dev/null | wc -l)
    else
        # Global scope - check workspace
        file_count=$(find . -path ./node_modules -prune -o -type f \( -name "*.ts" -o -name "*.js" -o -name "*.py" \) -print 2>/dev/null | wc -l)
        module_count=$(find . -mindepth 1 -maxdepth 3 -type d ! -path "*/node_modules/*" ! -path "*/.git/*" 2>/dev/null | wc -l)
    fi

    # Check for external research flag
    if [[ "$EXTERNAL" == "true" ]]; then
        external_deps=1
    fi

    # Determine complexity
    local complexity="simple"

    if [[ $file_count -gt 100 ]] || [[ $module_count -gt 10 ]]; then
        complexity="very_complex"
    elif [[ $file_count -gt 50 ]] || [[ $module_count -gt 5 ]]; then
        complexity="complex"
    elif [[ $file_count -gt 20 ]] || [[ $module_count -gt 3 ]] || [[ $external_deps -eq 1 ]]; then
        complexity="moderate"
    fi

    echo "$complexity"
}
```

### 3.5.2 P2: Parallel Agent Execution

```python
# Source P2 module
import sys
sys.path.append(".claude/skills/shared")
from parallel_agent import (
    parallel_agent_spawn,
    agent_synchronization,
    result_aggregation,
    get_agent_count_by_complexity
)

def execute_parallel_research(query, scope, complexity):
    """
    Execute research using multiple parallel agents.

    Returns:
        Aggregated research findings from all agents
    """
    # Get recommended agent count
    agent_count = get_agent_count_by_complexity(complexity)

    print(f"🔄 Parallel Research: {agent_count} agents for {complexity} complexity")

    # Decompose research into scopes (P1 delegation)
    research_scopes = decompose_research_scope(scope, agent_count)

    # Spawn parallel agents
    agent_ids = []
    for i, sub_scope in enumerate(research_scopes):
        agent_config = {
            "agent_type": "Explore",  # Use Explore agent for research
            "prompt": f"Research {query} in scope: {sub_scope}",
            "description": f"Research sub-task {i+1}/{agent_count}",
            "model": "sonnet",  # Use sonnet for sub-agents (opus for main)
            "run_in_background": True
        }

        agent_id = parallel_agent_spawn(agent_config)
        agent_ids.append(agent_id)

        # Launch Task tool for actual execution
        Task(
            subagent_type="Explore",
            description=f"Research {query} scope {i+1}",
            prompt=agent_config["prompt"],
            run_in_background=True
        )

    # Wait for all agents (barrier synchronization)
    sync_result = agent_synchronization(
        agent_ids=agent_ids,
        wait_strategy="barrier"  # Wait for all
    )

    # Aggregate results (merge strategy)
    aggregated = result_aggregation(
        results_array=sync_result["agent_results"],
        strategy="merge"  # Combine all findings
    )

    return aggregated
```

### 3.5.3 Scope Decomposition (P1 Sub-Orchestrator)

```python
def decompose_research_scope(scope, agent_count):
    """
    Decompose research scope into sub-scopes for parallel execution.

    Strategies:
    - Directory-based: Split by top-level directories
    - Module-based: Split by detected modules
    - Topic-based: Split by aspect (patterns, risks, integration, external)
    """
    if scope:
        # Directory-based decomposition
        top_dirs = Glob(f"{scope}/*", directories_only=True)

        if len(top_dirs) >= agent_count:
            # Assign directories to agents
            scopes = distribute_evenly(top_dirs, agent_count)
        else:
            # Not enough directories, use module-based
            scopes = detect_modules(scope, agent_count)
    else:
        # Topic-based decomposition for global scope
        scopes = [
            "codebase patterns and conventions",
            "integration points and dependencies",
            "risk assessment and security",
            "external documentation and best practices"
        ][:agent_count]

    return scopes

def distribute_evenly(items, count):
    """Distribute items into count groups evenly."""
    chunk_size = len(items) // count
    return [items[i:i+chunk_size] for i in range(0, len(items), chunk_size)][:count]
```

### 3.5.4 Result Merging

```python
def merge_parallel_research_results(aggregated_result, complexity):
    """
    Merge parallel agent results into unified research report.

    Handles:
    - Deduplication of findings
    - Conflict resolution (voting on disagreements)
    - Priority assignment to findings
    """
    merged_report = {
        "metadata": {
            "parallel_execution": True,
            "agent_count": len(aggregated_result["agent_results"]),
            "complexity": complexity,
            "execution_time": aggregated_result.get("execution_time", "N/A")
        },
        "codebase_analysis": {},
        "external_findings": [],
        "risk_assessment": {},
        "integration_points": []
    }

    # Merge codebase patterns (deduplicate)
    seen_patterns = set()
    for result in aggregated_result["agent_results"]:
        patterns = result.get("codebase_analysis", {}).get("patterns", [])
        for pattern in patterns:
            pattern_key = f"{pattern.get('file')}:{pattern.get('name')}"
            if pattern_key not in seen_patterns:
                seen_patterns.add(pattern_key)
                merged_report["codebase_analysis"].setdefault("patterns", []).append(pattern)

    # Merge risks (aggregate severity)
    risk_votes = {}
    for result in aggregated_result["agent_results"]:
        risks = result.get("risk_assessment", {})
        for risk_type, risk_data in risks.items():
            if risk_type not in risk_votes:
                risk_votes[risk_type] = []
            risk_votes[risk_type].append(risk_data)

    # Vote on risk severity (highest severity wins)
    for risk_type, votes in risk_votes.items():
        severities = [v.get("severity", "LOW") for v in votes]
        # Priority: CRITICAL > HIGH > MEDIUM > LOW
        merged_report["risk_assessment"][risk_type] = max(
            votes,
            key=lambda v: {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}.get(v.get("severity", "LOW"), 0)
        )

    return merged_report
```

---

## 4. Output Format (L1/L2/L3)

### 4.1 Output File Schema

```markdown
# Research Report: {topic}

> Generated: {timestamp}
> Clarify Reference: {clarify_slug}
> Scope: {scope}

---

## L1 Summary (< 500 tokens)

### Key Findings
- **Codebase Patterns:** {pattern_count} patterns identified
- **External Resources:** {resource_count} relevant sources
- **Risk Level:** {LOW|MEDIUM|HIGH|CRITICAL}
- **Complexity:** {SIMPLE|MODERATE|COMPLEX}

### Recommendations
1. {primary_recommendation}
2. {secondary_recommendation}

### Next Step
`/planning --research-slug {research_id}`

---

## L2 Detailed Analysis

### 2.1 Codebase Pattern Analysis

#### Existing Implementations
| File | Pattern | Relevance |
|------|---------|-----------|
| {file_path} | {pattern_name} | {HIGH/MEDIUM/LOW} |

#### Conventions Identified
- **Naming:** {convention_description}
- **Structure:** {convention_description}
- **Error Handling:** {convention_description}

### 2.2 Integration Points

```
{integration_diagram}
```

### 2.3 Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| {risk_description} | {HIGH/MEDIUM/LOW} | {mitigation_strategy} |

---

## L3 Full Findings

### 3.1 Complete File Analysis
{detailed_file_by_file_analysis}

### 3.2 External Resource Details
{full_external_research}

### 3.3 Code Evidence
{code_snippets_and_examples}

### 3.4 Implementation Notes
{detailed_implementation_considerations}
```

### 4.2 L1 Return to Main Agent

```yaml
taskId: research-{id}
agentType: research
status: success
summary: "Analyzed {file_count} files, found {pattern_count} patterns, risk level: {risk}"

priority: HIGH
l2Path: .agent/research/{research_id}.md
requiresL2Read: false

findings:
  codebase_patterns: {count}
  external_resources: {count}
  risk_level: "{LEVEL}"
  complexity: "{LEVEL}"

recommendations:
  - "{recommendation_1}"
  - "{recommendation_2}"

nextActionHint: "/planning --research-slug {research_id}"
clarifySlug: "{clarify_slug}"
researchSlug: "{research_id}"
```

---

## 5. Integration Points

### 5.1 Pipeline Position

```
/clarify                     Requirements clarification (YAML log)
    │
    │ clarify_slug
    ▼
/research  ◄── THIS SKILL
    │
    │ research_slug
    ▼
/planning                    Implementation planning (YAML)
    │
    ▼
/orchestrate                 Task decomposition
```

### 5.2 Input/Output Contract

| Direction | Skill | Data Format | Key Fields |
|-----------|-------|-------------|------------|
| **Input From** | `/clarify` | YAML | `final_output.approved_prompt`, `pipeline.context_hash` |
| **Output To** | `/planning` | Markdown | L1 summary, risk assessment, recommendations |

### 5.3 Cross-Reference

```python
# In /planning skill
if research_slug:
    research_data = Read(f".agent/research/{research_slug}.md")
    patterns = extract_patterns(research_data)
    risks = extract_risks(research_data)

    # Incorporate into planning
    planning_context["research_findings"] = patterns
    planning_context["risk_mitigations"] = risks
```

---

## 6. Delegation Patterns

### 6.1 Parallel Analysis

```python
# Run codebase and external research in parallel
Task(
    subagent_type="Explore",
    prompt="Analyze codebase structure for {topic}",
    run_in_background=True
)

if EXTERNAL:
    Task(
        subagent_type="general-purpose",
        prompt="Search and summarize external resources for {topic}",
        run_in_background=True
    )
```

### 6.2 Deep Dive Delegation

```python
# For complex areas, delegate focused analysis
if complexity_detected(area):
    Task(
        subagent_type="Explore",
        prompt=f"Deep dive into {area}, focusing on edge cases and dependencies",
        model="opus"
    )
```

---

## 7. Error Handling

| Error | Detection | Recovery |
|-------|-----------|----------|
| Clarify slug not found | File not exists | Proceed without context |
| WebSearch failure | API error | Skip external, warn user |
| Large codebase timeout | >5min analysis | Reduce scope, use sampling |
| Pattern detection failure | No matches | Report "no existing patterns" |
| Write failure | I/O error | Return results inline |

---

## 8. Shift-Left Validation (Gate 2)

### 8.1 Purpose

Gate 2 validates scope access **before** starting research:
- Verifies target paths exist and are readable
- Prevents wasted effort on inaccessible directories
- Warns about overly broad scopes

### 8.2 Hook Integration

```yaml
hooks:
  Setup:
    - research-validate.sh  # Gate 2: Scope Access Validation
  Stop:
    - research-finalize.sh  # Pipeline integration
```

### 8.3 Validation Results

| Result | Behavior | User Action |
|--------|----------|-------------|
| `passed` | ✅ Start research | None required |
| `passed_with_warnings` | ⚠️ Warn about broad scope, proceed | Consider narrowing scope |
| `failed` | ❌ Block execution, show error | Fix scope path, retry |

### 8.4 Scope Validation Examples

```bash
# Valid scope - passes
/research --scope src/auth/ "authentication patterns"

# Missing path - fails
/research --scope nonexistent/ "query"

# Too broad - warning
/research --scope . "query"  # Warning: scope very broad
```

---

## 9. Exit Conditions

### 9.1 Normal Exit (Success)

- Gate 2 validation passes
- Research report generated at `.agent/research/{id}.md`
- L1 summary returned to Main Agent
- Stop hook triggers: `research-finalize.sh`

### 8.2 Partial Exit

- External search failed but codebase analysis complete
- Status: `partial_success`
- Warning included in L1 summary

### 8.3 Error Exit

- Critical failure (no analysis possible)
- Status: `error`
- Error details in response

---

## 9. Usage Examples

### Basic Usage

```bash
/research "authentication system"
```

### With Clarify Context

```bash
/research --clarify-slug auth-impl-2026
```

### Scoped Analysis

```bash
/research --scope src/auth/ "OAuth2 implementation"
```

### Full External Research

```bash
/research --external --clarify-slug auth-impl-2026 "JWT token refresh patterns"
```

---

## 10. Testing Checklist

### Basic Functionality
- [ ] `/research "test query"` basic execution
- [ ] `/research --clarify-slug {slug}` context loading
- [ ] `/research --scope {path}` scoped analysis
- [ ] `/research --scope nonexistent/` failure handling
- [ ] `/research --scope .` broad scope warning
- [ ] Gate 2 validation execution
- [ ] `/research --external` external resource gathering
- [ ] L1/L2/L3 output format validation
- [ ] Setup hook trigger verification
- [ ] Stop hook trigger verification
- [ ] Pipeline integration with `/planning`

### P1: Agent Delegation (Sub-Orchestrator)
- [ ] Complexity detection: simple (≤10 files)
- [ ] Complexity detection: moderate (11-30 files)
- [ ] Complexity detection: complex (31-100 files)
- [ ] Complexity detection: very_complex (>100 files)
- [ ] Complexity detection: external flag forces very_complex
- [ ] Scope decomposition: directory-based strategy
- [ ] Scope decomposition: module-based strategy
- [ ] Scope decomposition: topic-based strategy
- [ ] Sub-agent spawn and state management
- [ ] Max 5 sub-agents limit enforcement

### P2: Parallel Agent Execution
- [ ] Agent count mapping: simple → 2 agents
- [ ] Agent count mapping: moderate → 3 agents
- [ ] Agent count mapping: complex → 4 agents
- [ ] Agent count mapping: very_complex → 5 agents
- [ ] Parallel agent spawn via `parallel_agent_spawn()`
- [ ] Barrier synchronization strategy
- [ ] Merge aggregation strategy
- [ ] Result deduplication across agents
- [ ] Conflict resolution via voting
- [ ] Agent timeout handling (10 minutes)

---

## 11. Parameter Module Compatibility (V2.1.0)

> `/build/parameters/` module compatibility checklist

| Module | Status | Notes |
|--------|--------|-------|
| `model-selection.md` | ✅ | `opus` for comprehensive analysis |
| `context-mode.md` | ✅ | `fork` for isolated execution |
| `tool-config.md` | ✅ | V2.1.0: Read, Grep, Glob, WebSearch, WebFetch, Task, Bash |
| `hook-config.md` | ✅ | Stop hook, 180000ms timeout |
| `permission-mode.md` | N/A | Skill-specific, not Agent |
| `task-params.md` | ✅ | Section 6 Delegation Patterns |

### Version History

| Version | Change |
|---------|--------|
| 2.0.0 | P1 Agent Delegation and P2 Parallel Agent integration |
| 1.0.0 | Initial /research skill implementation |

---

*Created by Terminal-B Worker | 2026-01-24*
