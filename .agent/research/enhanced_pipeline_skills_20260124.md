# Research Report: Enhanced Pipeline Skills Implementation

> **Created:** 2026-01-24T20:45:00Z
> **Status:** Complete
> **Source:** /clarify results + codebase analysis
> **Scope:** /research, /planning, /rsil-plan skills

---

## Executive Summary

### L1 - Quick Summary

Three new skills required to enhance the orchestration pipeline:

| Skill | Position | Purpose | Owner |
|-------|----------|---------|-------|
| `/research` | After `/clarify` | Deep codebase + external analysis | Terminal-B |
| `/planning` | After `/research` | YAML planning with Plan Agent review | Terminal-C |
| `/rsil-plan` | After `/synthesis` (2nd+ Loop) | Gap analysis and remediation planning | Terminal-B |

**Key Finding:** Current pipeline lacks structured research phase and iterative gap remediation mechanism.

---

## 1. Current Pipeline Analysis

### 1.1 Existing Skills Structure

```
.claude/skills/
├── clarify/SKILL.md        # V2.1.0 - Requirements clarification
├── orchestrate/SKILL.md    # V2.1.0 - Task decomposition
├── assign/SKILL.md         # Worker assignment
├── worker/SKILL.md         # Worker execution
├── collect/SKILL.md        # Result aggregation
├── synthesis/SKILL.md      # V2.1.0 - Quality validation
├── commit-push-pr/SKILL.md # Git operations
├── build/SKILL.md          # V2.2.0 - Component builder
├── build-research/SKILL.md # Concept research
└── docx-automation/SKILL.md # Document generation
```

### 1.2 Current Pipeline Flow

```
/clarify → /orchestrate → /assign → Workers → /collect → /synthesis
                                                             │
                                                    ┌────────┴────────┐
                                                    │                 │
                                                COMPLETE          ITERATE
                                                    │                 │
                                                    ▼                 ▼
                                          /commit-push-pr      Back to /clarify
```

### 1.3 Identified Gaps

| Gap | Impact | Solution |
|-----|--------|----------|
| No research phase after clarify | Requirements may miss existing patterns | `/research` skill |
| No structured planning document | Workers lack detailed blueprints | `/planning` skill |
| No iterative gap tracking | ITERATE loops restart from scratch | `/rsil-plan` skill |
| No code-level verification in ITERATE | Gaps not verified at implementation level | RSIL code analysis |

---

## 2. External Resource Analysis

### 2.1 Claude Code Native Capabilities (V2.1.19)

**Relevant for new skills:**

| Capability | Usage |
|------------|-------|
| `context: fork` | Isolated execution for `/research` |
| `model: opus` | Complex analysis requiring high capability |
| Skill-level hooks | Stop hooks for finalization |
| Task delegation | Plan Agent review via Task tool |
| Progressive Disclosure | L1/L2/L3 output format |

### 2.2 Existing Pattern References

**From `/build-research`:**
- External resource gathering with WebSearch
- L1 summary generation
- Build state management

**From `/synthesis`:**
- Traceability matrix generation
- Quality validation (consistency, completeness, coherence)
- COMPLETE/ITERATE decision logic

**From `/clarify`:**
- Multi-round Q&A
- YAML output schema
- Hook integration

---

## 3. Skill Specifications

### 3.1 `/research` Skill

**Purpose:** Deep codebase analysis + external resource gathering after `/clarify`

**Position:** `/clarify` → **`/research`** → `/planning`

**Core Responsibilities:**

1. **Code Pattern Analysis**
   - Grep/Glob for similar implementations
   - Identify existing patterns, utilities, components
   - Map dependencies and imports

2. **External Resource Gathering**
   - WebSearch for best practices
   - Documentation lookup
   - Similar implementation examples

3. **Risk Assessment**
   - Compatibility issues
   - Breaking changes potential
   - Missing dependencies

**Inputs:**
```yaml
inputs:
  - path: ".agent/clarify/{slug}.yaml"
    type: requirements
  - args: "--scope <path>"
    type: focus_directory
  - args: "--external"
    type: enable_web_search
```

**Outputs:**
```yaml
outputs:
  - path: ".agent/research/{slug}.md"
    format: L1/L2/L3
    sections:
      - executive_summary (L1)
      - codebase_analysis (L2)
      - external_resources (L2)
      - risk_assessment (L2)
      - recommendations (L2)
      - detailed_findings (L3)
```

**Frontmatter:**
```yaml
---
name: research
description: |
  Deep codebase analysis and external resource gathering.
  Post-/clarify research phase for informed planning.
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
```

---

### 3.2 `/planning` Skill

**Purpose:** Generate YAML planning documents with Plan Agent review

**Position:** `/research` → **`/planning`** → `/orchestrate`

**Core Responsibilities:**

1. **Parse Research Results**
   - Extract key findings from `/research` report
   - Map to actionable phases

2. **Generate Planning Document**
   - Structured YAML with phases, dependencies, criteria
   - Target files specification
   - Verification steps

3. **Plan Agent Review**
   - Delegate to Plan Agent via Task tool
   - Validate dependency graph
   - Iterate until approval

**Inputs:**
```yaml
inputs:
  - path: ".agent/research/{slug}.md"
    type: research_report
  - path: ".agent/clarify/{slug}.yaml"
    type: requirements
```

**Outputs:**
```yaml
outputs:
  - path: ".agent/plans/{slug}.yaml"
    format: planning_schema_v1
    sections:
      - metadata
      - project
      - phases
      - dependencies
      - planAgentReview
```

**Planning Document Schema:**
```yaml
metadata:
  id: "{slug}"
  version: "1.0.0"
  status: "approved"  # draft | under_review | approved
  research_source: ".agent/research/{slug}.md"
  clarify_source: ".agent/clarify/{slug}.yaml"

phases:
  - id: "phase1"
    name: "Phase Name"
    description: "What this phase accomplishes"
    priority: "P0"  # P0 | P1 | P2
    dependencies: []
    targetFiles:
      - path: "/path/to/file"
        action: "create | modify"
    completionCriteria:
      - "Criterion 1"
    verificationSteps:
      - command: "npm test"
        expected: "Pass"

planAgentReview:
  reviewedAt: "timestamp"
  status: "approved"
  comments: []
```

**Frontmatter:**
```yaml
---
name: planning
description: |
  Generate YAML planning documents from research results.
  Includes Plan Agent review loop for quality assurance.
user-invocable: true
disable-model-invocation: false
context: standard
model: opus
version: "1.0.0"
argument-hint: "[--research-slug <slug>] [--auto-approve]"
allowed-tools:
  - Read
  - Write
  - Task
  - AskUserQuestion
hooks:
  Stop:
    - type: command
      command: "/home/palantir/.claude/hooks/planning-finalize.sh"
      timeout: 150000
---
```

---

### 3.3 `/rsil-plan` Skill

**Purpose:** Requirements-Synthesis Integration Loop for 2nd+ iterations

**Position:** `/synthesis` (ITERATE) → **`/rsil-plan`** → `/clarify` or auto-remediate

**Core Responsibilities:**

1. **Load All Sources**
   - Original `/clarify` requirements
   - `/research` findings
   - `/planning` document
   - `/synthesis` report

2. **Code-Level Gap Analysis**
   - Grep for expected patterns
   - Verify file modifications match plan
   - Check completion criteria

3. **Remediation Planning**
   - Generate remediation tasks
   - Estimate complexity
   - Auto-remediate or escalate

**Gap Analysis Process:**
```
1. Load requirements from /clarify
2. Load planning phases from /planning
3. Load deliverables from /synthesis
4. For each requirement:
   - Grep codebase for implementation evidence
   - Compare with planning expectations
   - Mark as: COVERED | PARTIAL | MISSING
5. For MISSING/PARTIAL:
   - Generate remediation task
   - Set severity and complexity
6. Decision:
   - If gaps < 3 AND complexity low → auto-remediate
   - Otherwise → present to user for approval
```

**Inputs:**
```yaml
inputs:
  - path: ".agent/clarify/{slug}.yaml"
  - path: ".agent/research/{slug}.md"
  - path: ".agent/plans/{slug}.yaml"
  - path: ".agent/outputs/synthesis/synthesis_report.md"
```

**Outputs:**
```yaml
outputs:
  - path: ".agent/rsil/iteration_{n}.md"
    format: gap_analysis_report
  - path: ".agent/rsil/iteration_{n}_remediation.yaml"
    format: remediation_plan
```

**Frontmatter:**
```yaml
---
name: rsil-plan
description: |
  Requirements-Synthesis Integration Loop (RSIL).
  Verifies synthesis results against original requirements.
  Performs code-level gap analysis and creates remediation plans.
user-invocable: true
disable-model-invocation: false
context: standard
model: opus
version: "1.0.0"
argument-hint: "[--iteration <n>] [--auto-remediate]"
allowed-tools:
  - Read
  - Grep
  - Glob
  - Task
  - TaskCreate
  - TaskUpdate
  - TaskList
  - AskUserQuestion
---
```

---

## 4. Integration Points

### 4.1 Enhanced Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ENHANCED PIPELINE (1st Loop)                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  /clarify                                                           │
│      │                                                              │
│      ▼                                                              │
│  /research ◄─── NEW: Deep codebase + external analysis              │
│      │                                                              │
│      ▼                                                              │
│  /planning ◄─── NEW: YAML planning + Plan Agent review              │
│      │                                                              │
│      ▼                                                              │
│  /orchestrate                                                       │
│      │                                                              │
│      ▼                                                              │
│  /assign → Workers → /collect → /synthesis                          │
│                                        │                            │
│                         ┌──────────────┴──────────────┐             │
│                         │                             │             │
│                     COMPLETE                      ITERATE           │
│                         │                             │             │
│                         ▼                             ▼             │
│               /commit-push-pr              /rsil-plan ◄─── NEW      │
│                                                  │                  │
│                                    ┌─────────────┴─────────────┐    │
│                                    │                           │    │
│                              Auto-Remediate                Escalate │
│                                    │                           │    │
│                                    ▼                           ▼    │
│                              /orchestrate                 /clarify  │
│                              (remediation)               (2nd Loop) │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 File Flow Diagram

```
.agent/clarify/{slug}.yaml
         │
         ├──────────────────────────────────────────┐
         ▼                                          │
.agent/research/{slug}.md                           │
         │                                          │
         ▼                                          │
.agent/plans/{slug}.yaml                            │
         │                                          │
         ├──────────────────────────────────────────┤
         ▼                                          │
.agent/prompts/ (worker files)                      │
         │                                          │
         ▼                                          │
.agent/outputs/collection_report.md                 │
         │                                          │
         ▼                                          │
.agent/outputs/synthesis/synthesis_report.md        │
         │                                          │
         └─────────────▶ .agent/rsil/iteration_{n}.md
                                   │
                                   ▼
                        .agent/rsil/iteration_{n}_remediation.yaml
```

---

## 5. Multi-Terminal Distribution

### 5.1 Task Assignment Matrix

| Task | Owner | Rationale | Dependencies |
|------|-------|-----------|--------------|
| Implement `/research` skill | Terminal-B | Analysis expertise | None |
| Implement `/planning` skill | Terminal-C | Document generation | None |
| Create research-finalize.sh hook | Terminal-B | Supports /research | Task 1 |
| Create planning-finalize.sh hook | Terminal-C | Supports /planning | Task 2 |
| Implement `/rsil-plan` skill | Terminal-B | Gap analysis (similar to /research) | Task 1, 2 |
| Update `/synthesis` integration | Terminal-C | Add RSIL suggestion | Task 5 |
| Update CLAUDE.md pipeline | Terminal-B | Documentation | Task 1, 2, 5 |
| E2E testing | Both | Parallel verification | All |

### 5.2 Dependency Graph

```
Task 1: /research skill (Terminal-B) ──────────────────────┐
                                                           │
Task 2: /planning skill (Terminal-C) ──────────────────────┤
                                                           │
Task 3: research-finalize.sh (Terminal-B) ─────────────────┤
        depends on: Task 1                                 │
                                                           │
Task 4: planning-finalize.sh (Terminal-C) ─────────────────┤
        depends on: Task 2                                 │
                                                           ▼
Task 5: /rsil-plan skill (Terminal-B) ─────────────────────┤
        depends on: Task 1, Task 2                         │
                                                           │
Task 6: /synthesis update (Terminal-C) ────────────────────┤
        depends on: Task 5                                 │
                                                           ▼
Task 7: CLAUDE.md update (Terminal-B) ─────────────────────┤
        depends on: Task 1, Task 2, Task 5                 │
                                                           │
Task 8: E2E Testing (Both) ────────────────────────────────┘
        depends on: All
```

---

## 6. Risk Assessment

### 6.1 High Risk

| Risk | Impact | Mitigation |
|------|--------|------------|
| Plan Agent bottleneck | Slow planning iterations | Add --auto-approve for simple plans |
| RSIL false positives | Unnecessary remediation | Improve Grep pattern matching |
| Circular dependency in tasks | Deadlock | Validate DAG in /orchestrate |

### 6.2 Medium Risk

| Risk | Impact | Mitigation |
|------|--------|------------|
| Research scope creep | Long execution time | Limit with --scope parameter |
| Planning schema drift | Incompatible documents | Version schema, validate on load |
| Worker confusion | Wrong file edits | Clear targetFiles specification |

---

## 7. Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Pipeline completeness | 100% requirements in planning | All /clarify items mapped to phases |
| Gap detection rate | >90% | Compare RSIL findings with manual review |
| Iteration reduction | <2 loops average | Track loops to /commit-push-pr |
| Multi-terminal efficiency | >30% time savings | Measure parallel vs sequential |

---

## 8. Error Handling

### 8.1 `/research` Skill Error Handling

| Error | Detection | Recovery |
|-------|-----------|----------|
| Research scope too broad | Timeout (>180s) | Limit with `--scope` parameter |
| External resource unavailable | WebSearch failure/timeout | Fall back to codebase-only analysis |
| Clarify log not found | File not exists | Prompt user to run `/clarify` first |
| Empty search results | Grep/Glob returns 0 | Expand search patterns, report partial results |

### 8.2 `/planning` Skill Error Handling

| Error | Detection | Recovery |
|-------|-----------|----------|
| Research report not found | File not exists | Prompt user to run `/research` first |
| Plan Agent rejection | Review status ≠ approved | Show issues, iterate on planning document |
| YAML schema validation failed | Parse error | Present validation errors, allow retry |
| Circular dependencies detected | DAG validation fails | Highlight cycle, request user fix |

### 8.3 `/rsil-plan` Skill Error Handling

| Error | Detection | Recovery |
|-------|-----------|----------|
| Missing source files | Any input file not exists | Report missing files, suggest prerequisites |
| Grep pattern mismatch | 0 matches for expected patterns | Expand patterns, manual verification option |
| TaskCreate failure | Native API error | Log error, continue with remaining gaps |
| Remediation conflict | Same file in multiple tasks | Merge into single task, warn user |

---

## 9. Testing Checklist

### 9.1 `/research` Skill Testing

- [ ] Basic invocation: `/research --clarify-slug test-feature`
- [ ] Scope parameter: `/research --scope ./src/auth`
- [ ] External resources: `/research --external`
- [ ] Output file generation at `.agent/research/{slug}.md`
- [ ] L1/L2/L3 format compliance
- [ ] Hook trigger verification (`research-finalize.sh`)
- [ ] Integration: Output usable by `/planning`

### 9.2 `/planning` Skill Testing

- [ ] Basic invocation: `/planning --research-slug test-feature`
- [ ] Auto-approve mode: `/planning --auto-approve`
- [ ] Plan Agent review loop (rejection → iteration → approval)
- [ ] Output file generation at `.agent/plans/{slug}.yaml`
- [ ] YAML schema validation pass
- [ ] Hook trigger verification (`planning-finalize.sh`)
- [ ] Integration: Output usable by `/orchestrate`

### 9.3 `/rsil-plan` Skill Testing

- [ ] Basic invocation: `/rsil-plan --iteration 1`
- [ ] Auto-remediate mode: `/rsil-plan --auto-remediate`
- [ ] Gap analysis report generation
- [ ] Remediation task creation via TaskCreate
- [ ] COVERED/PARTIAL/MISSING classification accuracy
- [ ] User escalation flow (>3 gaps or high complexity)
- [ ] Integration: Tasks executable by Workers

---

## 10. Example Usage

### 10.1 `/research` Example

```bash
/research --clarify-slug user-auth-feature
```

**Expected Output:**
```
📊 Research Report generated: .agent/research/user-auth-feature.md

L1 Summary:
  - 3 existing auth patterns found in codebase
  - 2 external resources referenced (JWT docs, OAuth2 guide)
  - 1 medium-risk compatibility issue identified

L2 Sections:
  - codebase_analysis: 15 relevant files scanned
  - external_resources: 2 sources indexed
  - risk_assessment: 1 risk documented
  - recommendations: 3 action items

Next step: /planning --research-slug user-auth-feature
```

### 10.2 `/planning` Example

```bash
/planning --research-slug user-auth-feature
```

**Expected Output:**
```
📋 Planning Document generated: .agent/plans/user-auth-feature.yaml

Phases Created: 4
  - Phase 1: Setup JWT library (P0, no deps)
  - Phase 2: Implement auth middleware (P0, deps: Phase 1)
  - Phase 3: Add protected routes (P1, deps: Phase 2)
  - Phase 4: Integration tests (P1, deps: Phase 3)

Plan Agent Review: ✅ APPROVED
  - Dependency graph: acyclic
  - All phases have completion criteria
  - Target files specified

Next step: /orchestrate
```

### 10.3 `/rsil-plan` Example

```bash
/rsil-plan --iteration 1
```

**Expected Output:**
```
🔍 RSIL Gap Analysis - Iteration 1

Sources Loaded:
  ✅ /clarify: user-auth-feature.yaml
  ✅ /research: user-auth-feature.md
  ✅ /planning: user-auth-feature.yaml
  ✅ /synthesis: synthesis_report.md

Gap Analysis Results:
  ✅ COVERED: 3 requirements
  ⚠️ PARTIAL: 1 requirement (token refresh missing)
  ❌ MISSING: 0 requirements

Decision: AUTO-REMEDIATE (1 gap, low complexity)

Remediation Tasks Created:
  - Task #24: Add token refresh logic (terminal-b)

Next step: /orchestrate (remediation tasks ready)
```

---

## 11. Recommendations

1. **Implement /research and /planning in parallel** (Terminal-B, Terminal-C)
2. **Use existing patterns** from /build-research for /research skill
3. **Leverage /synthesis logic** for /rsil-plan gap analysis
4. **Add --auto-remediate** for low-complexity fixes
5. **Create comprehensive test cases** for each skill
6. **Add model: inherit option** to respect user's CLI choice
7. **Document tool rationale** in allowed-tools section
8. **Consider PreToolUse hooks** for input validation

---

## 12. Validation Summary (Post-Review)

| Category | Status | Notes |
|----------|--------|-------|
| Schema Validation | ✅ PASS | All YAML files valid |
| Consistency Check | ✅ PASS | Task IDs, owners consistent |
| Completeness Check | ✅ PASS | All sections now complete |
| Best Practice Check | ✅ PASS | V2.1.19 compliant |
| Gap Analysis | ✅ RESOLVED | Error handling, testing, examples added |

**Reviewed By:** claude-code-guide + general-purpose agents
**Review Date:** 2026-01-24T21:10:00Z

---

**End of Research Report**
