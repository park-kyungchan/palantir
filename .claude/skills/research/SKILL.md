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
version: "1.0.0"
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
  Stop:
    - type: command
      command: "/home/palantir/.claude/hooks/research-finalize.sh"
      timeout: 180000
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
# Generate research ID
if [[ -n "$CLARIFY_SLUG" ]]; then
    RESEARCH_ID="${CLARIFY_SLUG}"
else
    RESEARCH_ID=$(echo "$QUERY" | tr ' ' '-' | tr '[:upper:]' '[:lower:]' | head -c 20)
fi

OUTPUT_PATH=".agent/research/${RESEARCH_ID}.md"
mkdir -p .agent/research
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

## 8. Exit Conditions

### 8.1 Normal Exit (Success)

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

- [ ] `/research "test query"` basic execution
- [ ] `/research --clarify-slug {slug}` context loading
- [ ] `/research --scope {path}` scoped analysis
- [ ] `/research --external` external resource gathering
- [ ] L1/L2/L3 output format validation
- [ ] Stop hook trigger verification
- [ ] Pipeline integration with `/planning`

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
| 1.0.0 | Initial /research skill implementation |

---

*Created by Terminal-B Worker | 2026-01-24*
