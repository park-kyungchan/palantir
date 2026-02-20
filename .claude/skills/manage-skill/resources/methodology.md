# Manage Skill — Methodology Reference

## L1 Signal Priority Table

| Priority | Signal | Purpose | Example |
|----------|--------|---------|---------|
| P0 | **Core verb** | What this skill does | "Verifies CC native implementability" |
| P1 | **Method** | How it does it | "via cc-reference cache or claude-code-guide" |
| P2 | **Pipeline position** | When + prerequisites | "Terminal pre-design skill. Use after validate PASS" |
| P3 | **Input source** | Reads FROM (with skill name) | "Reads from pre-design-validate validated requirements" |
| P4 | **Output target** | Produces FOR (with skill name + condition) | "Produces feasibility verdict for design-architecture on PASS" |
| P5 | **Failure route** | Where on FAIL (with skill name) | "routes back to brainstorm on FAIL" |
| P6 | **Context hint** | What Lead must prepare for DPS | "DPS needs architecture L1 components + L2 ADRs" |

**Budget allocation:** P0-P2: ~400 chars | P3-P5: ~400 chars | P6: ~200 chars | Total: ≤1024 chars

## L1 Quality Scoring Rubric

| Dimension | Weight | 0 (Missing) | 1 (Partial) | 2 (Complete) |
|-----------|--------|-------------|-------------|--------------|
| Core verb + method | 15% | No action verb | Verb but vague method | Clear verb + specific method |
| Pipeline position | 15% | No position info | Phase but no prerequisites | Phase + prerequisite skills + trigger |
| Input source | 15% | No input mentioned | "Reads from X" no skill name | "Reads from {skill} {data-type}" |
| Output target | 15% | No output mentioned | "Produces X" no target skill | "Produces {data} for {skill} on {condition}" |
| Failure route | 15% | No failure info | "FAIL" but no route | "Routes to {skill} on FAIL with {data}" |
| Context hint | 15% | No DPS guidance | Partial ("needs architecture") | "DPS needs {skill} L1 {fields} + L2 {sections}" |
| Char efficiency | 10% | >1024 or <500 | 500-700 (underutilized) | 700-1024 (well-utilized) |

**D11 Cognitive Focus Check (P6):** Good hint specifies what to EXCLUDE, not just include. BAD: "Needs all architecture data." GOOD: "DPS needs architecture L1 components only. Exclude L2 ADR rationale — subagent needs structure not reasoning."

## Audit Steps

### Step 1: Discover Skills
```
Glob: .claude/skills/*/SKILL.md
```
Parse each: frontmatter (`name`, `description`, flags) + body section headers.

### Step 2: Audit L1 Descriptions

**2a. Character Count**: Flag >1024 as CRITICAL. Flag <500 as UNDERUTILIZED.

**2b. Signal Extraction**: Parse description for each P0-P6 signal. Score per rubric above.

**2c. D11 Cognitive Focus Check**: When P6 hint exists, verify it specifies exclusions (noise filter), not just inclusions.

### Step 3: Audit L2 Methodology

**3a. DPS Completeness Check:**

| Check | PASS Condition |
|-------|---------------|
| Tier-specific DPS | TRIVIAL, STANDARD, COMPLEX each addressed |
| DPS 5 fields | Context, Task, Constraints, Expected Output, Delivery |
| Context field cognitive focus | Specifies inclusions AND exclusions per D11 |
| Delivery field 2-channel | Matches D17 protocol (see 3b) |
| Output location physical | `~/.claude/tasks/{work_dir}/{phase}-{skill}.md` |

**3b. D17 Two-Channel Compliance:**

| Channel | Location | Content | Check |
|---------|----------|---------|-------|
| Ch1: PT metadata | `metadata.phase_signals.{phase}` | `"PASS\|key:value"` | Output section mentions PT update? |
| Ch2: Full output file | `~/.claude/tasks/{work_dir}/{phase}-{skill}.md` | L1 YAML + L2 detail | File path pattern specified? |
| Ch3: Micro-signal | Lead inbox | `"PASS\|ref:tasks/{work_dir}/{file}"` | DPS Delivery field matches? Lead not receiving full data? |
| File-based READY signal | Downstream output file | `"READY\|path:...\|fields:{list}"` | file-based handoff spec specifies NOTIFY targets? |

Migration flag: any skill referencing `/tmp/pipeline/` needs update to `tasks/{work_dir}/`.

**3c. D15 Iteration Tracking:** For loop skills — does L2 mention iteration count? Is `PT metadata iterations.{skill}: N` the tracking mechanism? Does max iteration reference PT-based count (not Lead memory)?

**3d. D12 Re-planning Completeness:**

| Level | Action | Check |
|-------|--------|-------|
| L0 | Retry same agent | "Retry" or "re-invoke" in failure handling? |
| L1 | Nudge with refined context | "Refined DPS" or "additional context" mentioned? |
| L2 | Kill & respawn fresh agent | "Re-spawn" or "new agent" mentioned? |
| L3 | Restructure task graph | "Task re-decomposition" or "dependency change" mentioned? |
| L4 | Escalate to Human | "AskUserQuestion" or "Human decision" mentioned? |

Skills with Failure Handling sections should cover at least L0, L2, L4.

**3e. Transition Consistency:** Target/source skill exists? Bidirectional reference match? Data format consistent?

### Step 4: Cross-Skill Integrity Audit

**4a. Orphan Detection:** Dead-end targets (Sends To nonexistent), orphan sources (Receives From nonexistent), unreachable skills (not in any pipeline path).

**4b. Domain Compound Failure Gaps:** Per pipeline domain — what if 2+ skills fail simultaneously?

**4c. Handoff Protocol Consistency:** All skills use `tasks/{work_dir}/` (not mixed with `/tmp/pipeline/`). file-based signal micro-signal format consistent. PT signal key naming consistent.

**4d. Context Distribution Pattern:** How many domains use coordinator's L1/L2/L3 tiered output? Which domains should adopt it?

### Step 5: Audit Report Templates

**Per-Skill Score Card:**
```yaml
skill: {name}
l1_score: 0.0  # 0.0-2.0
l1_grade: A|B|C|F
l1_chars: 0
l1_budget_remaining: 0
signals:
  p0_verb: PASS|FAIL
  p1_method: PASS|FAIL
  p2_position: PASS|FAIL
  p3_input: PASS|FAIL
  p4_output: PASS|FAIL
  p5_failure: PASS|FAIL
  p6_context_hint: PASS|FAIL
l2_compliance:
  dps_completeness: PASS|FAIL
  d17_handoff: PASS|FAIL
  d15_iteration: PASS|FAIL|N/A
  d12_replanning: PASS|FAIL
fixes:
  - issue: "P5 failure route missing"
    old: ""
    new: "routes to brainstorm on FAIL with gap report"
    char_delta: +45
```

**Cross-Skill Integrity Report:**
```yaml
transition_graph:
  total_edges: 0
  orphans: []
  dead_ends: []
handoff_compliance:
  d17_compliant: 0
  tmp_pipeline_legacy: 0
  missing_sendmessage: 0
domain_compound_gaps: []
context_distribution:
  l1l2l3_adoption: "1/N domains"
```

### Step 6: Fix Proposal (D16 Mode)

Generate L1 rewrites + L2 patches (D17 handoff, D15 iteration, D12 re-planning) for skills with grade < A. Batch format: `=== Batch N: {grade}-grade ({N} skills) ===` with per-skill OLD/NEW diff + char delta. Group F→C→B, max 5 per batch. AskUserQuestion: "Apply batch? [All / Select / Skip]".

### Steps 7-9: Remaining Actions

**Step 7 — Optimize L1:** Score description → identify missing P0-P6 → rewrite within 1024 chars (remove "This skill", ensure P5+P6) → present old/new with scores → AskUserQuestion.

**Step 8 — Create Skill:** AskUserQuestion (domain, position, connected skills) → generate frontmatter (L1 ≥ A) → generate L2 skeleton (Execution Model, Decision Points, Methodology+DPS, D17 Output, D15 if loop, D12 Failure Handling, Transitions) → validate score ≥ 1.7.

**Step 9 — Retire Skill:** Map transition graph impact → report broken edges → suggest rerouting → AskUserQuestion with rerouting plan → output deletion target + skills needing Transition updates.
