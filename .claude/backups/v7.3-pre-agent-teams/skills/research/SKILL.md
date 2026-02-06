---
name: research
description: |
  Deep codebase analysis and external resource gathering for informed planning.

  Core Capabilities:
  - Codebase Pattern Analysis: Identify existing patterns, conventions, dependencies
  - External Resource Gathering: Search documentation, best practices, similar implementations
  - Risk Assessment: Identify blockers, breaking changes, edge cases
  - Integration Point Mapping: Determine where new code connects with existing systems
  - EFL Pattern Execution: Full P1-P6 implementation with Phase 3-A/3-B synthesis

  Output Format:
  - L1: Summary for main orchestrator (500 tokens)
  - L2: Detailed analysis (research/l2_detailed.md)
  - L3: Full synthesis (research/l3_synthesis.md)

  Pipeline Position:
  - Post-/clarify research phase (or standalone execution)
  - Handoff to /planning when research is complete
user-invocable: true
disable-model-invocation: false
context: fork
model: opus
version: "3.0.0"
argument-hint: "[--scope <path>] [--external] [--clarify-slug <slug>]"
allowed-tools:
  - Read
  - Grep
  - Glob
  - Write
  - WebSearch
  - mcp__sequential-thinking__sequentialthinking
  - WebFetch
  - Task
  - Bash
# =============================================================================
# P1: Skill as Sub-Orchestrator
# =============================================================================
agent_delegation:
  enabled: true
  default_mode: true  # V1.1.0: Auto-delegation by default
  max_sub_agents: 5
  delegation_strategy: "auto"
  strategies:
    scope_based:
      description: "Decompose by directory/module boundaries (frontend, backend, API)"
      use_when: "--scope provided"
    topic_based:
      description: "Decompose by research aspect (patterns, risks, integration, external)"
      use_when: "Global scope research"
    complexity_based:
      description: "Decompose based on detected complexity level"
      use_when: "Auto-detect"
  slug_orchestration:
    enabled: true
  default_mode: true  # V1.1.0: Auto-delegation by default
    source: "clarify_slug OR active_workload"
    action: "reuse upstream workload context"
  sub_agent_permissions:
    - Read
    - Write  # Required for L1/L2/L3 output
    - Grep
    - Glob
    - WebSearch
    - WebFetch
  output_paths:
    l1: ".agent/prompts/{slug}/research/l1_summary.yaml"
    l2: ".agent/prompts/{slug}/research/l2_index.md"
    l3: ".agent/prompts/{slug}/research/l3_details/"
  return_format:
    l1: "Research summary with findings count and risk level (≤500 tokens)"
    l2_path: ".agent/prompts/{slug}/research/l2_index.md"
    l3_path: ".agent/prompts/{slug}/research/l3_details/"
    requires_l2_read: false
    next_action_hint: "/planning"
  description: |
    This skill operates as a Sub-Orchestrator (P1).
    It delegates research work to Research Agents rather than executing directly.
    L1 returns to main context; L2/L3 always saved to files.

# =============================================================================
# P2: Parallel Agent Configuration
# =============================================================================
parallel_agent_config:
  enabled: true
  complexity_detection: "auto"
  agent_count_by_complexity:
    simple: 2      # ≤20 files
    moderate: 3    # 21-50 files or --external
    complex: 4     # 51-100 files
    very_complex: 5  # >100 files
  synchronization_strategy: "barrier"
  aggregation_strategy: "merge"
  research_areas:
    - codebase_patterns
    - integration_points
    - risk_assessment
    - external_resources
  description: |
    Deploy multiple Research Agents in parallel for comprehensive analysis.
    Agent count scales with detected complexity (file count).
    All agents run Phase 1 simultaneously, then results are aggregated.

# =============================================================================
# P3: General-Purpose Synthesis Configuration
# =============================================================================
synthesis_config:
  phase_3a_l2_horizontal:
    enabled: true
    description: "Cross-validate research areas for consistency"
    validation_criteria:
      - cross_area_consistency
      - pattern_alignment
      - risk_coverage_completeness
  phase_3b_l3_vertical:
    enabled: true
    description: "Verify findings against codebase"
    validation_criteria:
      - file_existence_verification
      - pattern_accuracy
      - dependency_correctness
  phase_3_5_review_gate:
    enabled: true
    description: "Main Agent holistic verification"
    criteria:
      - requirement_alignment
      - design_flow_consistency
      - gap_detection
      - conclusion_clarity

# =============================================================================
# P4: Selective Feedback Loop
# =============================================================================
selective_feedback:
  enabled: true
  severity_filter: "warning"
  feedback_targets:
    - gate: "RESEARCH"
      severity: ["error", "warning"]
      action: "block_on_error"
    - gate: "SCOPE"
      severity: ["error"]
      action: "block"
  description: |
    Severity-based filtering for Gate 2 validation warnings.
    Errors block research. Warnings are logged but allow continuation.

# =============================================================================
# P5: Repeat Until Approval
# =============================================================================
repeat_until_approval:
  enabled: true
  max_rounds: 5
  approval_criteria:
    - "Research covers all required areas"
    - "Risk assessment complete"
    - "Integration points identified"
  description: |
    Research continues until all areas adequately covered.
    User can request additional research or approve.

# =============================================================================
# P6: Agent Internal Feedback Loop
# =============================================================================
agent_internal_feedback_loop:
  enabled: true
  max_iterations: 3
  validation_criteria:
    - "All findings have code references"
    - "Risks are properly categorized"
    - "Integration points are specific"
    - "Recommendations are actionable"
  refinement_triggers:
    - "Missing code references detected"
    - "Vague risk description found"
    - "Unspecific integration point"
  description: |
    Local research refinement loop before aggregation.
    Self-validates finding quality and iterates until threshold met.
---

### Auto-Delegation Trigger (CRITICAL)

> **Reference:** `.claude/skills/shared/auto-delegation.md`
> **Behavior:** When `agent_delegation.enabled: true` AND `default_mode: true`, skill automatically operates as Sub-Orchestrator.

```javascript
// AUTO-DELEGATION CHECK - Execute at skill invocation
// If complex task detected, triggers: analyze → delegate → collect
const delegationDecision = checkAutoDelegation(SKILL_CONFIG, userRequest)
if (delegationDecision.shouldDelegate) {
  const complexity = analyzeTaskComplexity(taskDescription, SKILL_CONFIG)
  return executeDelegation(taskDescription, complexity, SKILL_CONFIG)
}
// Simple tasks execute directly without delegation overhead
```


# /research - Deep Codebase & External Analysis (EFL V3.0.0)

> **Version:** 3.0.0 (EFL Pattern)
> **Role:** Deep Codebase Analysis with Full EFL Implementation
> **Pipeline Position:** After /clarify, Before /planning
> **EFL Template:** `.claude/skills/shared/efl-template.md`


---

## 0. EFL Execution Overview

This skill implements the Enhanced Feedback Loop (EFL) pattern:

1. **Phase 1**: Deploy parallel Research Agents for different analysis areas (P2)
2. **Phase 2**: Aggregate L1 summaries from all agents
3. **Phase 3-A**: L2 Horizontal Synthesis (cross-area consistency) (P3)
4. **Phase 3-B**: L3 Vertical Verification (code-level accuracy) (P3)
5. **Phase 3.5**: Main Agent Review Gate (holistic verification) (P1)
6. **Phase 4**: Selective Feedback Loop (if issues found) (P4)
7. **Phase 5**: User Final Approval (P5)

### Pipeline Integration

```
/clarify → [/research] → /planning → /orchestrate → Workers → /synthesis
               │
               ├── Phase 1: Parallel Research Agents (P2)
               ├── Phase 2: L1 Aggregation
               ├── Phase 3-A: L2 Horizontal Synthesis (P3)
               ├── Phase 3-B: L3 Vertical Verification (P3)
               ├── Phase 3.5: Main Agent Review Gate (P1)
               ├── Phase 4: Selective Feedback Loop (P4)
               └── Output: .agent/prompts/{slug}/research.md + L2/L3
```


---


---

## 1. Purpose

The `/research` skill performs comprehensive analysis to inform implementation planning:

1. **Codebase Pattern Analysis** - Identify existing patterns, conventions, and dependencies
2. **External Resource Gathering** - Search documentation, best practices, and similar implementations
3. **Risk Assessment** - Identify potential blockers, breaking changes, and edge cases
4. **Integration Points** - Map where new code should connect with existing systems


---

## 2. Execution Protocol

### 2.1 Argument Parsing (V2.2.0 Enhanced)

```bash
# $ARGUMENTS parsing with error recovery and validation
SCOPE=""
EXTERNAL=false
CLARIFY_SLUG=""
QUERY=""
SHOW_HELP=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            SHOW_HELP=true
            shift
            ;;
        --scope)
            if [[ -z "$2" || "$2" == --* ]]; then
                echo "❌ Error: --scope requires a path argument" >&2
                SHOW_HELP=true
                shift
            else
                SCOPE="$2"
                shift 2
            fi
            ;;
        --external)
            EXTERNAL=true
            shift
            ;;
        --clarify-slug)
            if [[ -z "$2" || "$2" == --* ]]; then
                echo "❌ Error: --clarify-slug requires a slug argument" >&2
                SHOW_HELP=true
                shift
            else
                CLARIFY_SLUG="$2"
                shift 2
            fi
            ;;
        --*)
            echo "❌ Error: Unknown option: $1" >&2
            echo "Available options: --scope, --external, --clarify-slug, --help" >&2
            SHOW_HELP=true
            shift
            ;;
        *)
            QUERY="$1"
            shift
            ;;
    esac
done

# Show help if requested or on error
if [[ "$SHOW_HELP" == "true" ]]; then
    cat << 'EOF'
Usage: /research [OPTIONS] <query>

Arguments:
  <query>                Research topic or question (required)

Options:
  --scope <path>         Limit research to specific directory
  --external             Include external resource gathering (WebSearch)
  --clarify-slug <slug>  Link to upstream /clarify workload
  --help, -h             Show this help message

Examples:
  /research "authentication patterns"
  /research --scope src/auth/ "OAuth2 implementation"
  /research --external --clarify-slug user-auth-20260129 "JWT refresh"

Pipeline Position:
  /clarify → /research → /planning

Standalone Mode:
  Can run without /clarify (auto-generates workload slug)
EOF
    exit 1
fi

# Validate: Query is required
if [[ -z "$QUERY" ]]; then
    echo "❌ Error: Research query is required" >&2
    echo "Usage: /research [--scope <path>] [--external] [--clarify-slug <slug>] <query>" >&2
    echo "Run '/research --help' for more information" >&2
    exit 1
fi

# Active workload fallback (if no clarify-slug provided)
if [[ -z "$CLARIFY_SLUG" ]]; then
    ACTIVE_WORKLOAD=".agent/prompts/_active_workload.yaml"
    if [[ -f "$ACTIVE_WORKLOAD" ]]; then
        # Extract active slug from workload file
        CLARIFY_SLUG=$(grep -oP 'slug:\s*["\x27]?\K[^"\x27\s]+' "$ACTIVE_WORKLOAD" | head -1 || echo "")
        if [[ -n "$CLARIFY_SLUG" ]]; then
            echo "ℹ️  Using active workload: $CLARIFY_SLUG" >&2
        fi
    fi
fi

# Scope validation (Shift-Left: validate early)
if [[ -n "$SCOPE" && ! -d "$SCOPE" ]]; then
    echo "❌ Error: Scope path does not exist: $SCOPE" >&2
    echo "Available directories:" >&2
    ls -d */ 2>/dev/null | head -10 >&2
    exit 1
fi
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

## 3. Research Phases (3-Tier Progressive-Deep-Dive)

> **Architecture:** Custom subagents (NOT system Explore Agent) for code-level analysis
> → general-purpose agent for output review → L1/L2/L3 generation

### Tier 1: Code-Level Deep Dive (Custom Subagents)

**Important:** These are CUSTOM subagents spawned via Task tool, NOT the built-in Explore Agent.
Custom subagents have Write permission for intermediate outputs.

```python
# 3.1 Spawn Custom Research Subagents
def tier1_deep_dive(query, scope, complexity):
    """
    Tier 1: Code-level exploration using custom subagents.

    NOT using built-in Explore Agent because:
    - Custom subagents have Write permission (required for L1/L2/L3)
    - Can be configured with specific tool sets
    - Support permissionMode: acceptEdits
    """
    agent_count = get_agent_count_by_complexity(complexity)
    research_scopes = decompose_research_scope(scope, agent_count)

    tier1_outputs = []

    for i, sub_scope in enumerate(research_scopes):
        # Spawn CUSTOM subagent (not Explore Agent)
        agent_id = Task(
            subagent_type="general-purpose",  # Custom subagent with Write
            description=f"Tier1 Research: {sub_scope}",
            prompt=f"""
            ## Code-Level Deep Dive Research

            **Query:** {query}
            **Scope:** {sub_scope}
            **Output Path:** .agent/prompts/{{slug}}/research/tier1_agent{i}.md

            ### Instructions
            1. Use Glob to find all relevant files in scope
            2. Use Grep to search for patterns, implementations, keywords
            3. Use Read to examine code structure and logic
            4. Write findings to output path (intermediate L2)

            ### Required Analysis
            - File structure and organization
            - Naming conventions and patterns
            - Import/export relationships
            - Error handling patterns
            - Integration points

            ### Output Format
            Write a detailed markdown report with code snippets.
            """,
            model="sonnet",
            run_in_background=True
        )
        tier1_outputs.append(agent_id)

    # Wait for all Tier 1 agents (barrier synchronization)
    return wait_for_agents(tier1_outputs)

# 3.1.1 External Resource Gathering (if --external)
def tier1_external_research(query, framework_detected):
    """External research runs in parallel with codebase analysis."""
    if not EXTERNAL:
        return None

    return Task(
        subagent_type="general-purpose",
        description="Tier1 External Research",
        prompt=f"""
        ## External Resource Research

        **Query:** {query}
        **Framework:** {framework_detected or "auto-detect"}
        **Output Path:** .agent/prompts/{{slug}}/research/tier1_external.md

        ### Instructions
        1. WebSearch for documentation and best practices (2026)
        2. WebSearch for similar implementations on GitHub
        3. WebFetch top 3 results for detailed analysis
        4. Write comprehensive findings to output path

        ### Search Queries
        - "{query} documentation best practices 2026"
        - "{query} implementation guide"
        - "{query} example github"
        """,
        model="sonnet",
        run_in_background=True
    )
```

### Tier 2: Output Review & Risk Assessment (general-purpose Agent)

```python
# 3.2 Review and Synthesize Tier 1 Outputs
def tier2_review_and_assess(tier1_outputs, query, scope):
    """
    Tier 2: general-purpose agent reviews all Tier 1 outputs.

    Responsibilities:
    - Validate completeness of Tier 1 research
    - Identify gaps requiring additional investigation
    - Perform risk assessment
    - Prepare structured data for L1/L2/L3 generation
    """
    return Task(
        subagent_type="general-purpose",
        description="Tier2 Review & Risk Assessment",
        prompt=f"""
        ## Tier 2: Output Review & Risk Assessment

        **Query:** {query}
        **Tier 1 Outputs:** .agent/prompts/{{slug}}/research/tier1_*.md
        **Output Path:** .agent/prompts/{{slug}}/research/tier2_review.md

        ### Phase 2-A: Review Tier 1 Outputs
        1. Read all tier1_*.md files
        2. Verify coverage completeness
        3. Identify contradictions or gaps
        4. Flag areas needing clarification

        ### Phase 2-B: Risk Assessment
        Analyze for:
        - Breaking changes in existing code
        - Dependency conflicts
        - Security concerns (OWASP Top 10)
        - Complexity level (SIMPLE/MODERATE/COMPLEX/CRITICAL)

        ### Phase 2-C: Prepare Synthesis Data
        Structure findings for L1/L2/L3:
        ```yaml
        patterns_found: [list]
        integration_points: [list]
        risks:
          breaking_changes: [list]
          security_concerns: [list]
          complexity: "LEVEL"
        recommendations: [list]
        gaps_identified: [list]
        ```

        Write structured review to output path.
        """,
        model="opus"  # Use opus for comprehensive review
    )
```

### Tier 3: L1/L2/L3 Generation (Final Output)

```python
# 3.3 Generate Progressive Disclosure Outputs
def tier3_generate_outputs(tier2_review, query, slug):
    """
    Tier 3: Generate L1/L2/L3 outputs from Tier 2 review.

    Output Structure:
    - L1: Executive summary (< 500 tokens) in research.md
    - L2: Detailed analysis in research/l2_detailed.md
    - L3: Full synthesis with code evidence in research/l3_synthesis.md
    """

    # Read Tier 2 review
    tier2_data = Read(f".agent/prompts/{slug}/research/tier2_review.md")

    # Generate L1 Summary (inline in research.md)
    l1_summary = generate_l1_summary(tier2_data)

    # Write L2 Detailed Report
    Write(
        path=f".agent/prompts/{slug}/research/l2_detailed.md",
        content=generate_l2_detailed(tier2_data)
    )

    # Write L3 Full Synthesis
    Write(
        path=f".agent/prompts/{slug}/research/l3_synthesis.md",
        content=generate_l3_synthesis(tier2_data)
    )

    # Write main research.md with L1 and references
    Write(
        path=f".agent/prompts/{slug}/research.md",
        content=f"""
# Research Report: {query}

> Generated: {timestamp}
> Workload: {slug}
> Tier: 3-Tier Progressive-Deep-Dive Complete


---

## L1 Summary

{l1_summary}


---

## References

- **L2 Detailed:** [research/l2_detailed.md](research/l2_detailed.md)
- **L3 Synthesis:** [research/l3_synthesis.md](research/l3_synthesis.md)
- **Tier 1 Raw:** research/tier1_*.md
- **Tier 2 Review:** research/tier2_review.md


---

## Next Step

`/planning --research-slug {slug}`
"""
    )

    return {
        "status": "completed",
        "l1_path": f".agent/prompts/{slug}/research.md",
        "l2_path": f".agent/prompts/{slug}/research/l2_detailed.md",
        "l3_path": f".agent/prompts/{slug}/research/l3_synthesis.md"
    }
```

### Tier Execution Flow

```
┌─────────────────────────────────────────────────────────────┐
│ TIER 1: Code-Level Deep Dive (Parallel Custom Subagents)    │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ Agent 1  │  │ Agent 2  │  │ Agent 3  │  │ External │    │
│  │ scope-A  │  │ scope-B  │  │ scope-C  │  │ (if flag)│    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘    │
│       │             │             │             │           │
│       ▼             ▼             ▼             ▼           │
│  tier1_agent1.md  tier1_agent2.md tier1_agent3.md tier1_ext │
└─────────────────────────┬───────────────────────────────────┘
                          │ barrier sync
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ TIER 2: Review & Risk Assessment (general-purpose Agent)    │
├─────────────────────────────────────────────────────────────┤
│  Read all Tier 1 outputs → Validate → Assess Risks          │
│  → Prepare structured synthesis data                        │
│                          │                                  │
│                          ▼                                  │
│                   tier2_review.md                           │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ TIER 3: L1/L2/L3 Generation (Main Agent)                    │
├─────────────────────────────────────────────────────────────┤
│  Generate progressive disclosure outputs:                    │
│  - research.md (L1 Summary + References)                    │
│  - research/l2_detailed.md (Developer-level)                │
│  - research/l3_synthesis.md (Architect-level)               │
└─────────────────────────────────────────────────────────────┘
```


---

## 3.5 P1/P2 Integration Reference

> **Note:** P1/P2 agent delegation is now integrated into the 3-Tier Progressive-Deep-Dive system.
> See Section 3.1-3.3 for implementation details.

### 3.5.1 Quick Reference

| P1/P2 Concept | 3-Tier Implementation |
|---------------|----------------------|
| Complexity Detection | `get_agent_count_by_complexity()` in Tier 1 |
| Parallel Agent Spawn | Tier 1 custom subagents (general-purpose with Write) |
| Scope Decomposition | `decompose_research_scope()` in Tier 1 |
| Barrier Synchronization | `wait_for_agents()` between Tier 1 and Tier 2 |
| Result Merging | Tier 2 review agent aggregates all Tier 1 outputs |

### 3.5.2 Complexity → Agent Count Mapping

```python
def get_agent_count_by_complexity(complexity):
    """Map complexity level to number of parallel agents."""
    mapping = {
        "simple": 2,      # ≤20 files
        "moderate": 3,    # 21-50 files or --external
        "complex": 4,     # 51-100 files
        "very_complex": 5 # >100 files
    }
    return mapping.get(complexity, 2)
```

### 3.5.3 Scope Decomposition Strategies

| Strategy | When Used | Description |
|----------|-----------|-------------|
| scope-based | `--scope` provided | Split by subdirectories |
| topic-based | Global scope | Split by research aspect |
| complexity-based | Auto-detect | Agent count based on file count |


---

## 4. Output Format (L1/L2/L3) - 3-Tier Integration

> **Output Architecture:** Integrated with 3-Tier Progressive-Deep-Dive system
> See Section 3.3 (Tier 3) for generation logic

### 4.1 Output File Structure

```
.agent/prompts/{slug}/
├── research.md                    # L1 Summary + References (main entry)
└── research/
    ├── tier1_agent1.md            # Tier 1: Raw findings (Agent 1)
    ├── tier1_agent2.md            # Tier 1: Raw findings (Agent 2)
    ├── tier1_agent3.md            # Tier 1: Raw findings (Agent 3)
    ├── tier1_external.md          # Tier 1: External research (if --external)
    ├── tier2_review.md            # Tier 2: Review + Risk Assessment
    ├── l2_detailed.md             # L2: Developer-level analysis
    └── l3_synthesis.md            # L3: Architect-level synthesis
```

### 4.2 L1 Summary Schema (research.md)

```markdown
# Research Report: {query}

> Generated: {timestamp}
> Workload: {slug}
> Scope: {scope}
> Tier: 3-Tier Progressive-Deep-Dive Complete


---

## L1 Summary

### Key Findings
- **Codebase Patterns:** {pattern_count} patterns identified
- **External Resources:** {resource_count} relevant sources (if --external)
- **Risk Level:** {LOW|MEDIUM|HIGH|CRITICAL}
- **Complexity:** {SIMPLE|MODERATE|COMPLEX}

### Top Recommendations
1. {primary_recommendation}
2. {secondary_recommendation}
3. {tertiary_recommendation}

### Risks Requiring Attention
| Risk | Severity | Mitigation |
|------|----------|------------|
| {risk_1} | {severity} | {mitigation} |


---

## References

| Level | Path | Description |
|-------|------|-------------|
| L2 | [l2_detailed.md](research/l2_detailed.md) | Developer-level analysis |
| L3 | [l3_synthesis.md](research/l3_synthesis.md) | Architect-level synthesis |
| Tier 1 | research/tier1_*.md | Raw code analysis |
| Tier 2 | research/tier2_review.md | Review + Risk assessment |


---

## Next Step

`/planning --research-slug {slug}`
```

### 4.3 L2 Detailed Schema (research/l2_detailed.md)

```markdown
# L2 Detailed Analysis: {query}

> For: Developers implementing the solution
> Source: Tier 1 + Tier 2 synthesis


---

## 1. Codebase Pattern Analysis

### 1.1 Existing Implementations
| File | Pattern | Relevance | Code Reference |
|------|---------|-----------|----------------|
| {file_path} | {pattern_name} | {HIGH/MEDIUM/LOW} | Line {n} |

### 1.2 Conventions Identified
- **Naming:** {convention_with_examples}
- **Structure:** {directory_organization}
- **Imports:** {import_patterns}
- **Error Handling:** {error_patterns}

## 2. Integration Points

```
{integration_diagram_ascii}
```

### 2.1 Entry Points
{list_of_entry_points_with_file_references}

### 2.2 Dependencies
{dependency_graph_or_list}

## 3. Risk Assessment (Developer View)

| Risk | Severity | Affected Files | Mitigation |
|------|----------|----------------|------------|
| {risk} | {severity} | {files} | {mitigation} |

## 4. Implementation Guidance

### 4.1 Recommended Approach
{step_by_step_guidance}

### 4.2 Code Patterns to Follow
{existing_patterns_to_reference}

### 4.3 Anti-Patterns to Avoid
{patterns_to_avoid}
```

### 4.4 L3 Synthesis Schema (research/l3_synthesis.md)

```markdown
# L3 Architectural Synthesis: {query}

> For: Architects and technical leads
> Source: Full Tier 1-2 analysis + cross-cutting concerns


---

## 1. Executive Architecture Summary

### 1.1 System Context
{how_this_fits_in_overall_system}

### 1.2 Key Decisions Required
| Decision | Options | Recommendation | Rationale |
|----------|---------|----------------|-----------|
| {decision} | {options} | {recommendation} | {rationale} |

## 2. Cross-Cutting Concerns

### 2.1 Security Implications
{security_analysis}

### 2.2 Performance Considerations
{performance_analysis}

### 2.3 Scalability Impact
{scalability_analysis}

### 2.4 Maintainability
{maintainability_analysis}

## 3. Full Code Evidence

### 3.1 Pattern Examples
{code_snippets_with_analysis}

### 3.2 Integration Code References
{integration_code_examples}

## 4. Risk Matrix (Full)

| Risk | Probability | Impact | Severity | Owner | Mitigation Plan |
|------|-------------|--------|----------|-------|-----------------|
| {risk} | {prob} | {impact} | {severity} | {owner} | {plan} |

## 5. Dependencies & Constraints

### 5.1 Hard Dependencies
{must_have_dependencies}

### 5.2 Soft Dependencies
{nice_to_have}

### 5.3 Constraints
{technical_constraints}

## 6. Traceability

### 6.1 Source Artifacts
| Tier | File | Key Findings |
|------|------|--------------|
| Tier 1 | tier1_agent1.md | {summary} |
| Tier 1 | tier1_agent2.md | {summary} |
| Tier 2 | tier2_review.md | {summary} |

### 6.2 Downstream Impact
- `/planning`: Will use recommendations for task breakdown
- `/orchestrate`: Will use risk assessment for dependency ordering
```

### 4.5 L1 Return to Main Agent (YAML)

```yaml
taskId: research-{slug}
agentType: research
status: success
tier_system: "3-Tier Progressive-Deep-Dive"

summary: |
  Analyzed {file_count} files across {agent_count} agents.
  Found {pattern_count} patterns, {risk_count} risks.
  Risk level: {LEVEL}, Complexity: {LEVEL}

outputs:
  l1_summary: ".agent/prompts/{slug}/research.md"
  l2_detailed: ".agent/prompts/{slug}/research/l2_detailed.md"
  l3_synthesis: ".agent/prompts/{slug}/research/l3_synthesis.md"
  tier1_raw: ".agent/prompts/{slug}/research/tier1_*.md"
  tier2_review: ".agent/prompts/{slug}/research/tier2_review.md"

findings:
  patterns_found: {count}
  integration_points: {count}
  risks_identified: {count}
  external_resources: {count}  # if --external
  risk_level: "{LEVEL}"
  complexity: "{LEVEL}"

recommendations:
  - "{recommendation_1}"
  - "{recommendation_2}"
  - "{recommendation_3}"

nextActionHint: "/planning --research-slug {slug}"
workloadSlug: "{slug}"
```


---

## 5. Integration Points (3-Tier Aware)

### 5.1 Pipeline Position

```
                    ┌─────────────────────────────────────┐
                    │         STANDALONE MODE             │
                    │  (No upstream /clarify required)    │
                    │                                     │
                    │  /research "query"                  │
                    │      │                              │
                    │      ▼                              │
                    │  Auto-generate workload slug        │
                    └──────────────┬──────────────────────┘
                                   │
┌──────────────────────────────────┴──────────────────────────────────┐
│                      PIPELINE MODE                                   │
│                                                                      │
│  /clarify                     Requirements + Design Intent (YAML)    │
│      │                                                               │
│      │ --clarify-slug OR _active_workload.yaml                      │
│      ▼                                                               │
│  /research  ◄── THIS SKILL (3-Tier Progressive-Deep-Dive)           │
│      │                                                               │
│      │ workload_slug + L1/L2/L3 outputs                             │
│      ▼                                                               │
│  /planning                    Implementation planning (YAML)         │
│      │                                                               │
│      ▼                                                               │
│  /orchestrate                 Task decomposition + dependencies      │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2 Input/Output Contract (3-Tier)

#### Inputs

| Source | Data Format | Key Fields | Required |
|--------|-------------|------------|----------|
| `/clarify` | YAML | `final_output.approved_prompt`, `design_intent`, `pipeline.workload_slug` | Optional |
| `_active_workload.yaml` | YAML | `slug`, `status` | Fallback |
| CLI Arguments | String | `--scope`, `--external`, `--clarify-slug`, `<query>` | query required |

#### Outputs (3-Tier Structure)

| Level | Path | Format | Consumer |
|-------|------|--------|----------|
| **L1** | `.agent/prompts/{slug}/research.md` | Markdown | `/planning` (primary), Main Agent |
| **L2** | `.agent/prompts/{slug}/research/l2_detailed.md` | Markdown | `/planning` (if deep analysis needed) |
| **L3** | `.agent/prompts/{slug}/research/l3_synthesis.md` | Markdown | `/orchestrate` (risk-based ordering) |
| **Tier 1** | `.agent/prompts/{slug}/research/tier1_*.md` | Markdown | Audit trail |
| **Tier 2** | `.agent/prompts/{slug}/research/tier2_review.md` | Markdown | Audit trail |

### 5.3 Cross-Reference (3-Tier Pattern)

```python
# In /planning skill - Reading 3-Tier research outputs
def load_research_context(research_slug):
    """
    Load research findings with 3-Tier progressive disclosure.

    Strategy:
    - Always read L1 for summary
    - Read L2 if detailed patterns needed
    - Read L3 if architectural decisions required
    """
    base_path = f".agent/prompts/{research_slug}"

    # L1: Always read (summary + references)
    l1_content = Read(f"{base_path}/research.md")
    context = {
        "summary": extract_l1_summary(l1_content),
        "recommendations": extract_recommendations(l1_content),
        "risk_level": extract_risk_level(l1_content)
    }

    # L2: Read if planning requires detailed patterns
    if needs_detailed_patterns(context):
        l2_content = Read(f"{base_path}/research/l2_detailed.md")
        context["patterns"] = extract_patterns(l2_content)
        context["integration_points"] = extract_integration_points(l2_content)
        context["implementation_guidance"] = extract_guidance(l2_content)

    # L3: Read if architectural decisions required
    if context["risk_level"] in ["HIGH", "CRITICAL"]:
        l3_content = Read(f"{base_path}/research/l3_synthesis.md")
        context["risk_matrix"] = extract_risk_matrix(l3_content)
        context["dependencies"] = extract_dependencies(l3_content)
        context["cross_cutting_concerns"] = extract_concerns(l3_content)

    return context

# In /orchestrate skill - Using L3 for dependency ordering
def order_tasks_by_risk(tasks, research_slug):
    """Use L3 risk matrix to order task dependencies."""
    l3_path = f".agent/prompts/{research_slug}/research/l3_synthesis.md"

    if file_exists(l3_path):
        l3_content = Read(l3_path)
        risk_matrix = extract_risk_matrix(l3_content)

        # High-risk items should be addressed first
        for task in tasks:
            task_risk = find_task_risk(task, risk_matrix)
            task["priority"] = risk_to_priority(task_risk)

        return sorted(tasks, key=lambda t: t["priority"], reverse=True)

    return tasks
```


---

## 6. Error Handling (3-Tier + All-or-Nothing)

> **Policy:** All-or-Nothing - Any Tier failure blocks entire research
> **Rationale:** Partial results may lead to incorrect planning decisions

### 6.1 Error Types

| Category | Error | Detection | Recovery |
|----------|-------|-----------|----------|
| **Input** | Query not provided | Argument parsing | Block execution, show usage |
| **Input** | Invalid scope path | Gate 2-B validation | Block execution, suggest paths |
| **Input** | Clarify slug not found | File not exists | Proceed in standalone mode |
| **Tier 1** | Agent spawn failure | Task tool error | ❌ **FAIL** - Block entire research |
| **Tier 1** | Agent timeout | >10min per agent | ❌ **FAIL** - Block entire research |
| **Tier 1** | External API failure | WebSearch error | ❌ **FAIL** if --external, else skip |
| **Tier 2** | Review agent failure | Task tool error | ❌ **FAIL** - Block entire research |
| **Tier 2** | Tier 1 outputs missing | Files not found | ❌ **FAIL** - Block entire research |
| **Tier 3** | L1/L2/L3 write failure | I/O error | ❌ **FAIL** - Block entire research |
| **System** | Large codebase | >5min complexity detection | Reduce scope, re-run |

### 6.2 All-or-Nothing Policy

```python
def execute_research_with_all_or_nothing(query, scope, external):
    """
    Execute 3-Tier research with strict All-or-Nothing error handling.

    If ANY tier fails → entire research fails.
    No partial outputs are generated.
    """
    try:
        # Tier 1
        tier1_results = tier1_deep_dive(query, scope, complexity)
        if not all_agents_succeeded(tier1_results):
            raise ResearchError("Tier 1 failed: Not all agents completed")

        # Tier 2
        tier2_result = tier2_review_and_assess(tier1_results, query, scope)
        if not tier2_result.success:
            raise ResearchError(f"Tier 2 failed: {tier2_result.error}")

        # Tier 3
        outputs = tier3_generate_outputs(tier2_result, query, slug)
        if not outputs.all_written:
            raise ResearchError(f"Tier 3 failed: {outputs.error}")

        return {"status": "success", "outputs": outputs}

    except ResearchError as e:
        # Clean up any partial outputs
        cleanup_partial_outputs(slug)
        return {"status": "error", "error": str(e)}
```

### 6.3 Post-Compact Recovery Integration

> **CRITICAL:** See [Post-Compact Recovery Module](../shared/post-compact-recovery.md)

```python
# At research skill start
if is_post_compact_session():
    slug = get_active_workload()
    if not slug:
        error("No active workload. Cannot continue after compact.")
        exit(1)

    # Restore full context from L1/L2/L3 files
    context = restore_skill_context(slug, "research")

    # Validate recovery before proceeding
    if not validate_recovery(context, "research"):
        error("Context recovery failed. Required files missing.")
        exit(1)

    print("✅ Post-Compact Recovery: Context restored from files")
```

### 6.4 Error Exit Codes

| Code | Meaning | User Action |
|------|---------|-------------|
| 0 | Success | Proceed to `/planning` |
| 1 | Input validation failed | Fix arguments, retry |
| 2 | Tier 1 failure | Check scope, reduce complexity, retry |
| 3 | Tier 2 failure | Check Tier 1 outputs, retry |
| 4 | Tier 3 failure | Check disk space, permissions, retry |
| 5 | Post-Compact recovery failed | Re-run research from scratch |


---

## 7. Shift-Left Validation (Gate 2-A + Gate 2-B)

> **Shift-Left Principle:** Validate inputs BEFORE starting any research work
> See [CLAUDE.md Section 1 - Shift Left Philosophy](../../CLAUDE.md)

### 7.1 Gate Architecture

```
/research invoked
       │
       ▼
┌──────────────────────────────────┐
│ GATE 2-A: Argument Validation    │
│ - Query required?                │
│ - --help requested?              │
│ - Unknown options?               │
└──────────────┬───────────────────┘
               │ PASS
               ▼
┌──────────────────────────────────┐
│ GATE 2-B: Scope Validation       │
│ - Path exists?                   │
│ - Path readable?                 │
│ - Scope too broad?               │
└──────────────┬───────────────────┘
               │ PASS
               ▼
        Start 3-Tier Research
```

### 7.2 Gate 2-A: Argument Validation

| Check | Detection | Result |
|-------|-----------|--------|
| Query missing | `$QUERY` empty | ❌ FAIL - Show usage |
| --help flag | `--help` or `-h` in args | ❌ FAIL - Show help |
| Unknown option | `--unknown` | ❌ FAIL - Show available options |
| Invalid --scope arg | `--scope` without path | ❌ FAIL - Show usage |

**Hook Implementation:** `research-validate.sh` Gate 2-A section

### 7.3 Gate 2-B: Scope Validation

| Check | Detection | Result |
|-------|-----------|--------|
| Path not found | `! -d "$SCOPE"` | ❌ FAIL - Show available directories |
| Path not readable | `! -r "$SCOPE"` | ❌ FAIL - Permission error |
| Scope too broad | `$SCOPE == "."` | ⚠️ WARN - Suggest narrowing |
| Large file count | `>1000 files` | ⚠️ WARN - Complexity warning |

### 7.5 Validation Results

| Result | Gate | Behavior | User Action |
|--------|------|----------|-------------|
| `passed` | Both | ✅ Start research | None |
| `passed_with_warnings` | 2-B | ⚠️ Warn, proceed | Consider narrowing scope |
| `failed_2a` | 2-A | ❌ Block, show usage | Fix arguments |
| `failed_2b` | 2-B | ❌ Block, show error | Fix scope path |

### 7.6 Examples

```bash
# ✅ Valid - passes both gates
/research --scope src/auth/ "authentication patterns"

# ❌ Gate 2-A fail - no query
/research --scope src/auth/
# Error: Research query is required

# ❌ Gate 2-B fail - path not found
/research --scope nonexistent/ "query"
# Error: Scope path does not exist: nonexistent/

# ⚠️ Gate 2-B warning - broad scope
/research --scope . "query"
# Warning: Scope very broad (1500 files). Consider narrowing.
```


---

## 8. Exit Conditions (3-Tier Aware)

### 8.1 Normal Exit (Success)

```yaml
status: "success"
exit_code: 0
trigger: "All 3 Tiers completed successfully"
outputs:
  - ".agent/prompts/{slug}/research.md"        # L1
  - ".agent/prompts/{slug}/research/l2_detailed.md"  # L2
  - ".agent/prompts/{slug}/research/l3_synthesis.md" # L3
hook: "research-finalize.sh triggered"
next_action: "/planning --research-slug {slug}"
```

### 8.2 Error Exit (All-or-Nothing)

> **No Partial Exit:** Per All-or-Nothing policy, any Tier failure = full error exit

```yaml
status: "error"
exit_code: 2-5  # See Error Handling section 6.4
trigger: "Any Tier failure"
outputs: []  # No partial outputs generated
cleanup: "Partial files removed"
user_action: "Fix issue and retry /research"
```

### 8.3 Exit Code Reference

| Code | Status | Cause | Recovery |
|------|--------|-------|----------|
| 0 | success | All Tiers complete | Proceed to /planning |
| 1 | input_error | Gate 2-A/2-B failed | Fix arguments |
| 2 | tier1_error | Agent spawn/timeout | Reduce scope |
| 3 | tier2_error | Review failed | Check Tier 1 outputs |
| 4 | tier3_error | Write failed | Check permissions |
| 5 | compact_recovery_error | Context lost | Re-run from scratch |


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

| Version | Date | Change |
|---------|------|--------|
| 3.0.0 | 2026-01-29 | **Full EFL Implementation** |
| | | P1-P6 complete with frontmatter configuration |
| | | Phase 3-A: L2 Horizontal Synthesis |
| | | Phase 3-B: L3 Vertical Verification |
| | | Phase 3.5: Main Agent Review Gate |
| | | Phase 4: Selective Feedback Loop |
| | | Phase 5: User Approval Loop |
| | | Agent prompts include P6 self-validation |
| | | synthesis_config section added |
| | | selective_feedback section added |
| | | repeat_until_approval section added |
| 2.2.0 | 2026-01-29 | 3-Tier Progressive-Deep-Dive + All-or-Nothing |
| 2.1.0 | 2026-01-28 | Standalone Execution + Handoff Contract |
| 2.0.0 | 2026-01-27 | P1 Agent Delegation and P2 Parallel Agent integration |
| 1.0.0 | 2026-01-24 | Initial /research skill implementation |


---

## 10. Standalone Execution (V2.2.0)

> **Capability:** /research can run independently without upstream /clarify
> **3-Tier:** Full 3-Tier Progressive-Deep-Dive runs in both modes

### 10.1 Execution Modes

| Mode | Trigger | Workload Source | Use Case |
|------|---------|-----------------|----------|
| **Pipeline** | `--clarify-slug` provided | Reuse existing slug | Standard workflow |
| **Active** | No args, active workload exists | `_active_workload.yaml` | Continue session |
| **Standalone** | No args, no active workload | Auto-generate new slug | Quick research |

### 10.2 Mode Detection Flow

```
/research invoked
       │
       ▼
┌─────────────────────────────────┐
│ --clarify-slug provided?        │
└──────────┬──────────────────────┘
           │
     YES   │   NO
     ↓     │   ↓
  PIPELINE │   ┌─────────────────────────────────┐
   MODE    │   │ _active_workload.yaml exists?   │
           │   └──────────┬──────────────────────┘
           │              │
           │        YES   │   NO
           │        ↓     │   ↓
           │     ACTIVE   │  STANDALONE
           │      MODE    │    MODE
           │              │
           └──────────────┴──────────────────────┐
                                                 │
                          All modes execute      │
                          full 3-Tier system     │
                                                 ▼
                                        Tier 1 → Tier 2 → Tier 3
                                              ↓
                                        L1/L2/L3 Outputs
```

### 10.3 Examples

```bash
# PIPELINE MODE: Use existing clarify workload
/research --clarify-slug user-auth-20260128-143022 "OAuth2 patterns"
# Output: .agent/prompts/user-auth-20260128-143022/research.md

# ACTIVE MODE: Continue current workload (auto-detected)
/research "JWT refresh implementation"
# Reads _active_workload.yaml → uses that slug
# Output: .agent/prompts/{active-slug}/research.md

# STANDALONE MODE: New independent research
/research "GraphQL best practices"
# Auto-generates: graphql-best-practices-20260129
# Output: .agent/prompts/graphql-best-practices-20260129/research.md
```

### 10.4 Workload Context Resolution

```python
def resolve_workload_context(clarify_slug, query):
    """
    Resolve workload context with priority:
    1. --clarify-slug argument (PIPELINE MODE)
    2. _active_workload.yaml (ACTIVE MODE)
    3. Generate new slug (STANDALONE MODE)
    """
    # Priority 1: Explicit clarify-slug
    if clarify_slug:
        return {
            "mode": "pipeline",
            "slug": clarify_slug,
            "source": "clarify_slug_argument"
        }

    # Priority 2: Active workload
    active_file = ".agent/prompts/_active_workload.yaml"
    if file_exists(active_file):
        active_slug = Read(active_file).get("slug")
        if active_slug:
            return {
                "mode": "active",
                "slug": active_slug,
                "source": "_active_workload.yaml"
            }

    # Priority 3: Generate new (standalone)
    new_slug = generate_slug_from_query(query)
    return {
        "mode": "standalone",
        "slug": new_slug,
        "source": "auto_generated"
    }
```


---

## 11. Handoff Contract (V2.2.0)

> **Handoff:** Structured data passed to downstream skills
> **All-or-Nothing:** Only successful completion triggers handoff

### 11.1 Handoff Mapping

| Exit Status | Next Skill | Arguments | Trigger |
|-------------|------------|-----------|---------|
| `success` (0) | `/planning` | `--research-slug {slug}` | All 3 Tiers complete |
| `error` (1-5) | None | - | Any Tier failure |

**Note:** No `partial` status per All-or-Nothing policy.

### 11.2 Handoff YAML Output

Generated by `research-finalize.sh` hook on successful exit:

```yaml
# Appended to research.md footer

---

handoff:
  skill: "research"
  version: "2.2.0"
  workload_slug: "{slug}"
  status: "success"
  timestamp: "{ISO8601}"

  # 3-Tier outputs for downstream consumption
  outputs:
    l1: ".agent/prompts/{slug}/research.md"
    l2: ".agent/prompts/{slug}/research/l2_detailed.md"
    l3: ".agent/prompts/{slug}/research/l3_synthesis.md"

  # Summary for /planning quick reference
  summary:
    patterns_found: {count}
    risks_identified: {count}
    risk_level: "{LEVEL}"
    complexity: "{LEVEL}"

  # Next action guidance
  next_action:
    skill: "/planning"
    command: "/planning --research-slug {slug}"
    required: true
    reason: "Research complete, ready for planning phase"
    recommended_reads:
      - "L1 for summary"
      - "L2 for implementation patterns"
      - "L3 if risk_level is HIGH or CRITICAL"
```

### 11.3 Upstream/Downstream Integration

```
UPSTREAM                    THIS SKILL                 DOWNSTREAM
─────────                   ──────────                 ──────────

/clarify                                               /planning
    │                                                      ▲
    │ --clarify-slug                                       │
    ▼                                                      │
┌─────────────────────────────────────────────────────────┐
│                      /research                          │
│                                                         │
│  Input:                         Output:                 │
│  - clarify.yaml (if pipeline)   - research.md (L1)     │
│  - query (always)               - l2_detailed.md       │
│  - scope (optional)             - l3_synthesis.md      │
│                                 - handoff YAML         │
└─────────────────────────────────────────────────────────┘
                                                      │
                                                      │ --research-slug
                                                      ▼
                                                 /planning
```

### 11.4 Handoff Verification

```python
# In /planning skill - verify research handoff
def verify_research_handoff(research_slug):
    """Verify research completed successfully before planning."""
    research_md = f".agent/prompts/{research_slug}/research.md"

    if not file_exists(research_md):
        error(f"Research output not found: {research_md}")
        return False

    content = Read(research_md)

    # Check for handoff section
    if "handoff:" not in content:
        error("Research handoff section missing - may be incomplete")
        return False

    # Check status
    if 'status: "success"' not in content:
        error("Research did not complete successfully")
        return False

    return True
```


---

*Created by Terminal-B Worker | 2026-01-24*

