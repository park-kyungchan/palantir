# L1/L2/L3 Progressive Disclosure Standard Template

> **Version:** 1.0.0 | **Mandatory for all Skills**
> **Principle:** Main Context receives L1 only; L2/L3 always saved to files

---

## Core Principle

```
┌──────────────────────────────────────────────────────────────┐
│ Sub-Orchestrator Skill                                        │
│                                                              │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐    │
│  │  Agent 1    │     │  Agent 2    │     │  Agent N    │    │
│  │  (Explore)  │     │  (Explore)  │     │  (General)  │    │
│  └──────┬──────┘     └──────┬──────┘     └──────┬──────┘    │
│         │                   │                   │            │
│         ▼                   ▼                   ▼            │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              L2/L3 Files (Always Saved)              │    │
│  │  .agent/prompts/{slug}/{skill}/                      │    │
│  │    ├── l2_index.md      (anchor/token/priority)     │    │
│  │    └── l3_details/      (full analysis)             │    │
│  └─────────────────────────────────────────────────────┘    │
│                            │                                 │
│                            ▼                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │           L1 Summary (≤500 tokens)                   │    │
│  │           → Returns to Main Context                  │    │
│  └─────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
```

---

## Required Frontmatter Sections

### 1. agent_delegation (P1)

```yaml
agent_delegation:
  enabled: true
  mode: "sub_orchestrator"
  description: "[Skill-specific description]"
  agents:
    - type: "explore"
      role: "Phase 3-A L2 Horizontal - [specific role]"
      output_format: "L2 structured data"
    - type: "explore"
      role: "Phase 3-B L3 Vertical - [specific role]"
      output_format: "L3 detailed analysis"
  return_format:
    l1: "[What returns to main context - ≤500 tokens]"
    l2_path: ".agent/prompts/{slug}/{skill-name}/l2_index.md"
    l3_path: ".agent/prompts/{slug}/{skill-name}/l3_details/"
    requires_l2_read: false
```

### 2. parallel_agent_config (P2)

```yaml
parallel_agent_config:
  enabled: true
  complexity_detection: "auto"
  agent_count_by_complexity:
    simple: 1
    moderate: 2
    complex: 3
  synchronization_strategy: "barrier"
  aggregation_strategy: "merge"
```

### 3. agent_internal_feedback_loop (P6)

```yaml
agent_internal_feedback_loop:
  enabled: true
  max_iterations: 3
  validation_criteria:
    completeness:
      - "[Skill-specific completeness criteria]"
    quality:
      - "[Skill-specific quality criteria]"
    internal_consistency:
      - "L1/L2/L3 hierarchy maintained"
      - "Metadata matches actual outputs"
```

### 4. review_gate (P5)

```yaml
review_gate:
  enabled: true
  phase: "3.5"
  criteria:
    - "requirement_alignment: [Skill-specific]"
    - "design_flow_consistency: L2/L3 structure properly separated"
    - "gap_detection: Missing outputs identified"
    - "conclusion_clarity: Next action recommendations clear"
  auto_approve: false
```

### 5. selective_feedback (P4)

```yaml
selective_feedback:
  enabled: true
  threshold: "MEDIUM"
  action_on_low: "log_only"
  action_on_medium_plus: "trigger_review_gate"
```

---

## Required Body Section: Output Format

Every SKILL.md MUST include this section in the body:

```markdown
## Output Format (L1/L2/L3 Progressive Disclosure)

### L1: Main Context Return (≤500 tokens)

Returns to orchestrating skill/user as YAML:

\`\`\`yaml
taskId: {generated-id}
agentType: {skill-name}
status: success|partial|failed
priority: CRITICAL|HIGH|MEDIUM|LOW

summary: "[1-2 sentence summary of results]"

recommendedRead:
  - anchor: "#[most-important-section]"
    reason: "[Why this section matters]"

l2Index:
  - anchor: "#[section-id]"
    tokens: [estimated]
    priority: HIGH|MEDIUM|LOW
    description: "[What this section contains]"

l2Path: ".agent/prompts/{slug}/{skill-name}/l2_index.md"
l3Path: ".agent/prompts/{slug}/{skill-name}/l3_details/"
requiresL2Read: false
nextActionHint: "[Suggested next skill or action]"
\`\`\`

### L2: Indexed Detail File

Saved to: `.agent/prompts/{slug}/{skill-name}/l2_index.md`

\`\`\`markdown
# {Skill Name} L2 Analysis

## Summary {#summary}
<!-- ~150 tokens, Priority: CRITICAL -->
[Executive summary]

## Key Findings {#findings}
<!-- ~300 tokens, Priority: HIGH -->
[Main discoveries with evidence]

## Recommendations {#recommendations}
<!-- ~200 tokens, Priority: MEDIUM -->
[Action items]

## Details Index {#details-index}
<!-- ~100 tokens, Priority: LOW -->
| Item | L3 File | Priority |
|------|---------|----------|
| [Item 1] | l3_details/item1.md | HIGH |
| [Item 2] | l3_details/item2.md | MEDIUM |
\`\`\`

### L3: Full Detail Files

Saved to: `.agent/prompts/{slug}/{skill-name}/l3_details/`

- One file per major analysis area
- Complete data, code snippets, full logs
- Referenced from L2 index
- No token limit (comprehensive)
```

---

## P3: Priority-Based Reading Strategy

Every SKILL.md MUST document when downstream consumers should read each level:

```markdown
## Reading Strategy (P3)

| Consumer | Read L1 | Read L2 | Read L3 | Use Case |
|----------|---------|---------|---------|----------|
| Main Orchestrator | ✅ Always | ❌ Never | ❌ Never | Status check, routing |
| Downstream Skill | ✅ Always | ⚠️ If HIGH priority | ⚠️ If CRITICAL | Decision making |
| /synthesis | ✅ Always | ✅ Always | ⚠️ If gaps | Final validation |
| Human Review | ✅ Quick check | ✅ Analysis | ✅ Deep dive | Full understanding |

### Reading Decision Flow

\`\`\`
L1 Summary received
    │
    ├─▶ status == "failed" → Read L2 for diagnostics
    │
    ├─▶ priority == "CRITICAL" → Read L2 immediately
    │
    ├─▶ priority == "HIGH" && hasGaps → Read L2 #findings section
    │
    ├─▶ priority == "MEDIUM" → L1 sufficient, skip L2
    │
    └─▶ priority == "LOW" → L1 sufficient, skip L2
\`\`\`
```

---

## File Path Convention

All skills MUST use workload-scoped paths:

```
.agent/prompts/{slug}/
├── {skill-name}/
│   ├── l1_summary.yaml      # L1 backup (optional)
│   ├── l2_index.md          # L2 indexed overview
│   └── l3_details/          # L3 comprehensive files
│       ├── analysis-1.md
│       ├── analysis-2.md
│       └── raw-data.json
```

### Path Variables

| Variable | Source | Example |
|----------|--------|---------|
| `{slug}` | Active workload slug | `efl-integration-20260129` |
| `{skill-name}` | Skill name from frontmatter | `collect`, `research` |

---

## Compliance Checklist

Every skill MUST have:

- [ ] `agent_delegation.return_format` with l1/l2_path/l3_path
- [ ] `agent_internal_feedback_loop` with L1/L2/L3 consistency check
- [ ] `review_gate` with L2/L3 separation criteria
- [ ] Body section "Output Format (L1/L2/L3 Progressive Disclosure)"
- [ ] Body section "Reading Strategy (P3)"
- [ ] All output paths under `.agent/prompts/{slug}/{skill-name}/`

---

*Standard defined: 2026-01-29 | Mandatory for all 17 skills*
