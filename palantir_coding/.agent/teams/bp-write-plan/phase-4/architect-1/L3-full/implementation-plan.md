# brainstorming-pipeline P0/P1 Flow Redesign — Implementation Plan

> **For Lead:** Single infra-implementer execution plan.
> Single file: `.claude/skills/brainstorming-pipeline/SKILL.md`
> Architecture source: `.agent/teams/bp-skill-enhance/phase-3/architect-1/L3-full/architecture-design.md`

**Goal:** Implement 8 Architecture Decisions (AD-1 through AD-8) + 4 compression options to redesign P0/P1 flow. 672L → ~575L.

---

## 1. Orchestration Overview

### Pipeline Structure

Single-file infrastructure modification:

```
Phase 1: Discovery       — Lead reads this plan (YOU ARE HERE)
Phase 6: Implementation  — Single infra-implementer executes all edits
Phase 6.V: Verification  — Lead validates line count, AD coverage, downstream compatibility
Phase 9: Delivery        — Lead commits
```

### Teammate Allocation

| Role | Count | Agent Type | File Ownership | Phase |
|------|-------|-----------|----------------|-------|
| Implementer | 1 | `infra-implementer` | `.claude/skills/brainstorming-pipeline/SKILL.md` | Phase 6 |

**WHY single infra-implementer:** Single .md file, no source code, no Bash needed. Section-ordered edits within one file have zero parallelization opportunity. infra-implementer has Edit + Write tools, exactly what's needed.

### Execution Sequence

```
Lead:   Spawn infra-implementer
Lead:   Send [DIRECTIVE] with this plan + architecture design path
Lead:   Verify understanding (1-2 probing questions)
        Implementer: Execute Task A → B → C → D → E (sequential)
        Implementer: Write L1/L2/L3
        Implementer: Report completion
Lead:   Gate Review (line count + AD coverage + downstream check)
Lead:   Commit
Lead:   Shutdown → cleanup
```

---

## 2. global-context.md Template

Not applicable — GC-v3 already exists from Phase 1-3 at `.agent/teams/bp-skill-enhance/global-context.md`.

---

## 3. File Ownership Assignment

| File | Ownership | Operation |
|------|-----------|-----------|
| `.claude/skills/brainstorming-pipeline/SKILL.md` | infra-implementer-1 | MODIFY (25 edit specs across 5 tasks) |

All edits are within this single file. No other files are created, modified, or deleted.

---

## 4. Task Decomposition

5 tasks, executed sequentially top-to-bottom through the file. Each task groups contiguous sections. All AD-6 inline removals are handled within their containing section's task.

### Task A: Header + Phase 0 + Phase 1.1

**Scope:** Lines 1-123. Specs S-1 through S-5.
**ADs:** AD-1, AD-4, AD-6, AD-7

**Acceptance Criteria:**
- AC-0: Read lines 1-123 of SKILL.md. Verify current content matches this plan's "old content" descriptions.
- AC-1: Core flow description (line 13) no longer mentions "Tier Classification"
- AC-2: Git branch command includes `| head -10`
- AC-3: Phase 0 reduced to ~20L PT existence check only (no PT creation, no Tier Routing)
- AC-4: Phase 1.1 has 0 sequential-thinking inline mentions

### Task B: Phase 1.2 through Phase 1.3.5

**Scope:** Lines 125-192. Specs S-6 through S-10.
**ADs:** AD-2, AD-3, AD-6

**Acceptance Criteria:**
- AC-0: Read lines 125-192 of SKILL.md. Verify current content matches this plan.
- AC-1: Phase 1.2 includes Feasibility Check subsection after category table
- AC-2: Phase 1.2.5 Checkpoint section exists between 1.2 and 1.3
- AC-3: Phase 1.3 has 0 sequential-thinking inline mentions
- AC-4: Phase 1.3.5 section completely deleted

### Task C: Phase 1.4 + Phase 1.5 Gate 1

**Scope:** Lines 194-306. Specs S-11 through S-17.
**ADs:** AD-4, AD-5, AD-6, Compression Options A-hybrid/B-hybrid/C/G

**Acceptance Criteria:**
- AC-0: Read lines 194-306 of SKILL.md. Verify current content matches this plan.
- AC-1: Scope Statement template includes Pipeline Tier + Tier Rationale fields
- AC-2: Gate 1 criteria replaced with gate-evaluation-standard.md reference
- AC-3: /permanent-tasks invocation appears as Step 1 before GC-v1 creation
- AC-4: GC-v1 template uses hybrid format (YAML code block + field list)
- AC-5: GC-v1 frontmatter includes `pt_version` and `tier` (not `complexity`)
- AC-6: Orchestration-plan template uses hybrid format
- AC-7: Gate-record template compressed to reference format

### Task D: Phase 2/3 + Cross-Cutting

**Scope:** Lines 309-672. Specs S-18 through S-25.
**ADs:** AD-6, AD-8, AD-2 (adjustments)

**Acceptance Criteria:**
- AC-0: Read lines 309-672 of SKILL.md. Verify current content matches this plan.
- AC-1: Phase 2 has 0 sequential-thinking inline mentions (2 removed)
- AC-2: Phase 3 has 0 sequential-thinking inline mentions (2 removed)
- AC-3: RTD Decision Points reduced to 3 (DP-1, DP-2, DP-3)
- AC-4: Sequential Thinking section is 3 lines (consolidated)
- AC-5: Key Principles includes "Feasibility first" and removes "Sequential thinking always"
- AC-6: Never list includes "Skip the feasibility check" and removes seq-thinking bullet

### Task E: Verification + Line Count

**Scope:** Entire file.
**Depends on:** Tasks A-D complete.

**Acceptance Criteria:**
- AC-0: Read entire SKILL.md from line 1 to end.
- AC-1: Total line count ≤ 578L
- AC-2: All 8 ADs covered (checklist in §6)
- AC-3: No broken markdown formatting (headers, code blocks, tables balanced)
- AC-4: Phase 2/3 logic unchanged (only sequential-thinking lines removed)
- AC-5: Clean Termination section unchanged
- AC-6: GC body structure preserved (Scope, Pipeline Status, Constraints, Decisions Log)

---

## 5. Detailed Specifications

**Read-First-Write-Second:** Each spec includes the current content (verified by reading SKILL.md) and the replacement content. The implementer MUST read the target lines before editing to confirm the old content matches.

**Notation:**
- `VL-1 (Exact)`: Character-perfect replacement. No flexibility.
- `VL-2 (Semantic)`: Meaning-preserving. Minor formatting flexibility allowed.
- `VL-3 (Intent)`: Goal-preserving. Implementation flexibility.

---

### Task A Specs: Header + Phase 0 + Phase 1.1

#### S-1: Core Flow Description [AD-1] — VL-1

**Location:** Line 13
**Operation:** MODIFY

**Old:**
```
**Core flow:** PT Check (Lead) → Tier Classification → Discovery (Lead) → Deep Research (research-coordinator or direct researcher) → Architecture (architect or architecture-coordinator) → Clean Termination
```

**New:**
```
**Core flow:** PT Check (Lead) → Discovery (Lead) → Deep Research (research-coordinator or direct researcher) → Architecture (architect or architecture-coordinator) → Clean Termination
```

**Change:** Remove "Tier Classification → " (tier now determined at 1.4, not P0).

---

#### S-2: Git Branch Cap [AD-7] — VL-1

**Location:** Line 46
**Operation:** MODIFY

**Old:**
```
!`cd /home/palantir && git branch 2>/dev/null`
```

**New:**
```
!`cd /home/palantir && git branch 2>/dev/null | head -10`
```

---

#### S-3: Phase 0 Complete Rewrite [AD-1, AD-4] — VL-2

**Location:** Lines 52-106 (Phase 0 header through Tier Routing subsection including trailing separator)
**Operation:** REPLACE entire section

**Old content (55L):** Current Phase 0 section including:
- PT Check decision tree with PT creation branches (lines 52-89)
- Separator (lines 90-91)
- Pipeline Tier Routing subsection (lines 92-106)

**New content (~20L):**

````markdown
## Phase 0: PERMANENT Task Check

Lightweight step (~500 tokens). No teammates spawned, no verification required.

Call `TaskList` and search for tasks with `[PERMANENT]` in their subject.

```
TaskList result
     │
┌────┼────────┐
none  1        2+
│     │        │
▼     ▼        ▼
Note  Validate  Match $ARGUMENTS
"no PT" match   against each
→ P1  → P1     │
              ┌──┴──┐
            match  no match
            → P1   → AskUser
```

If a [PERMANENT] task is found and matches `$ARGUMENTS`, its content (user intent,
impact map, prior decisions) provides additional context for Phase 1 discovery.
If no PT exists, one will be created at Gate 1 (1.5).

---
````

**Key changes:** No PT creation at P0. No Tier Routing subsection. Decision tree simplified to 3 terminal states (note/validate/ask). Tier classification deferred to 1.4 (AD-4).

---

#### S-4: Phase 1.1 Sequential-Thinking Removal #1 [AD-6] — VL-1

**Location:** Line 112
**Operation:** DELETE entire line

**Old:**
```
Use `sequential-thinking` before every analysis step, judgment, and decision in this phase.
```

---

#### S-5: Phase 1.1 Sequential-Thinking Removal #2 [AD-6] — VL-1

**Location:** Line 122
**Operation:** DELETE entire line

**Old:**
```
Use `sequential-thinking` to synthesize Recon into an internal assessment before starting Q&A.
```

---

### Task B Specs: Phase 1.2 through Phase 1.3.5

#### S-6: Phase 1.2 Sequential-Thinking Removal [AD-6] — VL-1

**Location:** Lines 146-147
**Operation:** DELETE both lines

**Old:**
```
Use `sequential-thinking` after each user response to analyze the answer and determine
the next question or whether to proceed to Scope Crystallization.
```

---

#### S-7: Feasibility Check Insertion [AD-2] — VL-2

**Location:** After current line 145 (end of category awareness paragraph, after S-6 deletion)
**Operation:** INSERT

**New content (~15L):**

````markdown

**Feasibility Check** — After the user explains PURPOSE, validate before deep-diving:

```
PURPOSE answered
     │
├── Produces a concrete codebase deliverable?
│     ├── NO → "This sounds strategic. What would change in the codebase?"
│     └── YES ↓
├── Overlaps with completed work? (check git log, MEMORY.md)
│     ├── YES → "This overlaps with {X}. Extending it or new?"
│     └── NO ↓
├── Scope estimable? (can you name affected modules/files?)
│     ├── NO → "Too open-ended. What's the specific deliverable?"
│     └── YES ↓
└── FEASIBLE → continue Q&A for remaining categories
```

On failure: user refines (loop to failed criterion) or pivots (restart from PURPOSE).
User can override: "I want to proceed anyway" — log override in checkpoint.
````

---

#### S-8: Phase 1.2.5 Checkpoint Insertion [AD-3] — VL-2

**Location:** After the end of Phase 1.2 section (after S-7 insertion), before Phase 1.3
**Operation:** INSERT new section

**New content (~18L):**

````markdown

### 1.2.5 Phase 1 Checkpoint

After feasibility check passes (or user overrides) AND at least 2 Q&A categories are
covered, create a lightweight checkpoint to protect against auto-compact:

**`.agent/teams/{session-id}/phase-1/qa-checkpoint.md`:**

```markdown
# Phase 1 Q&A Checkpoint — {feature}

## Feasibility
{PASS | OVERRIDE with rationale}

## Categories Covered
{List which of PURPOSE/SCOPE/CONSTRAINTS/APPROACH/RISK/INTEGRATION are resolved}

## Key Decisions So Far
{Decisions locked in from conversation — approach not yet selected}

## Scope Direction (Draft)
{Early boundary draft — what's in, what's obviously out}
```

On recovery: read qa-checkpoint.md, resume Q&A from last covered category.
````

---

#### S-9: Phase 1.3 Sequential-Thinking Removal [AD-6] — VL-1

**Location:** Line 165
**Operation:** DELETE entire line

**Old:**
```
Use `sequential-thinking` to formulate the trade-off analysis before presenting.
```

---

#### S-10: Phase 1.3.5 Full Deletion [AD-3] — VL-1

**Location:** Lines 168-192 (entire "### 1.3.5 Phase 1 Checkpoint" section)
**Operation:** DELETE entire section (25L)

**Old content starts with:**
```
### 1.3.5 Phase 1 Checkpoint
```

**Old content ends with:**
```
On recovery, read qa-checkpoint.md and resume Q&A from the last covered category.
```

**Verification:** After deletion, Phase 1.3 (Approach Exploration) should be immediately followed by Phase 1.4 (Scope Crystallization).

---

### Task C Specs: Phase 1.4 + Phase 1.5 Gate 1

#### S-11: Scope Statement Tier Fields [AD-4] — VL-2

**Location:** Lines 198-218 (Scope Statement template code block)
**Operation:** MODIFY — replace complexity field with tier fields

**Old (within the Scope Statement template code block):**
```
**Estimated Complexity:** SIMPLE / MEDIUM / COMPLEX
**Phase 2 Research Needs:**
- {topic}

**Phase 3 Architecture Needs:**
- {decision}
```

**New (replacement for the above lines within the template):**
```
**Pipeline Tier:** TRIVIAL | STANDARD | COMPLEX
**Tier Rationale:**
- File count: ~N
- Module count: ~N
- Cross-boundary impact: YES/NO

**Phase 2 Research Needs:**
- {topic}

**Phase 3 Architecture Needs:**
- {decision}
```

**After the closing ``` of the template, insert:**
```
If tier = TRIVIAL: skip Phases 2-3. Create lightweight scope statement,
route to `/agent-teams-execution-plan`.
```

---

#### S-12: Phase 1.4 Sequential-Thinking Removal [AD-6] — VL-1

**Location:** Line 220
**Operation:** DELETE entire line

**Old:**
```
Use `sequential-thinking` to synthesize all Q&A into the Scope Statement.
```

---

#### S-13: Gate 1 Criteria → Reference [Option G] — VL-2

**Location:** Lines 227-235 (criteria table including "Evaluate before proceeding:" header)
**Operation:** REPLACE

**Old:**
```
Evaluate before proceeding:

| # | Criterion |
|---|-----------|
| G1-1 | Scope Statement approved by user |
| G1-2 | Complexity classification confirmed |
| G1-3 | Phase 2 research scope defined |
| G1-4 | Phase 3 entry conditions clear |
| G1-5 | No unresolved critical ambiguities |
```

**New:**
```
Evaluate per `gate-evaluation-standard.md` §6. Key criteria: Scope approved,
tier determined with rationale, research scope defined, Phase 3 entry clear,
no critical ambiguities.
```

---

#### S-14: PT Creation Step + On APPROVE Modification [AD-5] — VL-2

**Location:** Line 239 ("On APPROVE" line) and insertion after it
**Operation:** MODIFY line + INSERT new step

**Old:**
```
**On APPROVE** — create these files:
```

**New (replace line + insert Step 1):**
```
**On APPROVE** — create artifacts in this sequence:

**Step 1: Create PERMANENT Task**

Invoke `/permanent-tasks` with conversation context (Scope Statement + approach + tier).
Creates PT-v1 with full 5-section template. Note the PT task ID for Step 2.
Control returns to Lead automatically after skill completion.
```

---

#### S-15: GC-v1 Template Compression [AD-5, Option A-hybrid] — VL-2

**Location:** Lines 241-268 (GC-v1 template header + code block)
**Operation:** REPLACE

**Old:** 28L — full GC-v1 markdown code block with header "**`.agent/teams/...` (GC-v1):**"

**New:**

````markdown
**Step 2: Create GC-v1**

`.agent/teams/{session-id}/global-context.md`:

```yaml
---
version: GC-v1
pt_version: PT-v1
created: {YYYY-MM-DD}
feature: {feature-name}
tier: TRIVIAL | STANDARD | COMPLEX
---
```

Body: **## Scope** (verbatim from 1.4) · **## Phase Pipeline Status** (P1 COMPLETE,
P2/P3 PENDING) · **## Constraints** (from Q&A) · **## Decisions Log** (table:
#/Decision/Rationale/Phase)
````

**Changes:** Frontmatter adds `pt_version`, renames `complexity` → `tier`. Body compressed from full markdown template to field list with section names.

---

#### S-16: Orchestration-Plan Template Compression [Option B-hybrid] — VL-2

**Location:** Lines 270-291 (orchestration-plan template header + code block)
**Operation:** REPLACE

**Old:** 22L — full orchestration-plan markdown code block

**New:**

````markdown
**Step 3: Create orchestration-plan.md**

`.agent/teams/{session-id}/orchestration-plan.md`:

```yaml
---
feature: {feature-name}
current_phase: 2
gc_version: GC-v1
pt_version: PT-v1
---
```

Body: **## Gate History** (P1 APPROVED + date) · **## Active Teammates** (none yet) ·
**## Phase 2 Plan** (research domains, count, strategy)
````

**Changes:** Added `pt_version` to frontmatter. Body compressed to field list.

---

#### S-17: Gate-Record Template Compression [Option C] — VL-2

**Location:** Lines 293-305 (gate-record template header + YAML code block)
**Operation:** REPLACE

**Old:** 13L — full gate-record YAML code block with explicit criteria fields

**New:**
```
**Step 4: Create gate-record.yaml**

`.agent/teams/{session-id}/phase-1/gate-record.yaml` per `gate-evaluation-standard.md`
format. Include phase: 1, result: APPROVED, date, and pass/fail for each G1 criterion.
```

---

### Task D Specs: Phase 2/3 + Cross-Cutting

#### S-18: Phase 2 Header Sequential-Thinking Removal [AD-6] — VL-1

**Location:** Line 314
**Operation:** DELETE entire line

**Old:**
```
Use `sequential-thinking` for all Lead decisions in this phase.
```

---

#### S-19: Phase 2.3 Tail Sequential-Thinking Removal [AD-6] — VL-1

**Location:** Line 388
**Operation:** DELETE entire line

**Old:**
```
All agents use `sequential-thinking` throughout.
```

---

#### S-20: Phase 3 Header Sequential-Thinking Removal [AD-6] — VL-1

**Location:** Line 444
**Operation:** DELETE entire line

**Old:**
```
Use `sequential-thinking` for all Lead decisions in this phase.
```

---

#### S-21: Phase 3.2 Tail Sequential-Thinking Removal [AD-6] — VL-1

**Location:** Line 484
**Operation:** DELETE entire line

**Old:**
```
All agents use `sequential-thinking` throughout.
```

---

#### S-22: RTD Decision Points Reduction [AD-8] — VL-1

**Location:** Lines 610-617 (DP list within Cross-Cutting RTD section)
**Operation:** REPLACE

**Old:**
```
Decision Points for this skill:
- DP: Scope crystallization (1.4 approval)
- DP: Approach selection (1.3 user choice)
- DP: Researcher spawn (2.3)
- DP: Gate 1 evaluation
- DP: Gate 2 evaluation
- DP: Architect spawn (3.1)
- DP: Gate 3 evaluation
```

**New:**
```
Decision Points for this skill:
- DP-1: Gate 1 evaluation (P1 → P2 transition)
- DP-2: Gate 2 evaluation (P2 → P3 transition)
- DP-3: Gate 3 evaluation (P3 → termination)
```

---

#### S-23: Sequential Thinking Section Consolidation [AD-6] — VL-1

**Location:** Lines 619-631 (Sequential Thinking subsection with agent table)
**Operation:** REPLACE

**Old (13L):**
```
### Sequential Thinking

All agents (Lead and teammates) use `mcp__sequential-thinking__sequentialthinking` for
analysis, judgment, design, and verification throughout the entire pipeline.

| Agent | When |
|-------|------|
| Lead (P1) | After Recon, after each user response, before Scope Statement, at Gates |
| Lead (P2-3) | Understanding verification, probing questions, Gate evaluation, PT/GC updates |
| research-coordinator (P2) | Research distribution, worker verification, progress monitoring, findings consolidation |
| Researcher (P2) | Research strategy, findings synthesis, L2 writing |
| Architect (P3) | Component design, trade-off analysis, interface definition |
```

**New (3L):**
```
### Sequential Thinking

All agents (Lead and teammates) use `mcp__sequential-thinking__sequentialthinking`
for every analysis, judgment, and decision throughout all phases. No exceptions.
```

---

#### S-24: Key Principles Adjustments [AD-2, AD-6] — VL-2

**Location:** Lines 649-660 (Key Principles bullet list)
**Operation:** MODIFY 2 bullets

**Change 1 — DELETE this bullet:**
```
- **Sequential thinking always** — structured reasoning at every decision point
```
**Reason:** Covered by Cross-Cutting consolidation (S-23).

**Change 2 — INSERT after "Category Awareness" bullet:**
```
- **Feasibility first** — validate topic produces actionable codebase deliverable before deep Q&A
```

---

#### S-25: Never List Adjustments [AD-2, AD-6] — VL-2

**Location:** Lines 663-672 (Never list)
**Operation:** MODIFY 2 bullets

**Change 1 — DELETE this bullet:**
```
- Present the Scope Statement without using sequential-thinking first
```
**Reason:** Covered by Cross-Cutting consolidation (S-23).

**Change 2 — INSERT (after "Proceed past a Gate" bullet):**
```
- Skip the feasibility check (unless user explicitly overrides)
```

---

## 6. Cross-Reference Verification

After all edits are complete, verify:

| # | Check | Method | Expected |
|---|-------|--------|----------|
| V-1 | AD-1 | Grep for `/permanent-tasks` in Phase 0 section | NOT found |
| V-2 | AD-2 | Grep for `Feasibility` in Phase 1.2 | Found |
| V-3 | AD-3 | Grep for `1.2.5` and `1.3.5` | 1.2.5 exists, 1.3.5 absent |
| V-4 | AD-4 | Grep for `Pipeline Tier` in Scope Statement | Found |
| V-5 | AD-5 | Grep for `/permanent-tasks` in Gate 1 section | Found as Step 1 |
| V-6 | AD-6 | Grep for `sequential-thinking` in entire file | Exactly 2 occurrences (Cross-Cutting only) |
| V-7 | AD-7 | Grep for `head -10` | Found in Dynamic Context |
| V-8 | AD-8 | Grep for `DP-` in RTD section | Exactly 3 (DP-1, DP-2, DP-3) |
| V-9 | GC structure | GC-v1 field list mentions | Scope, Pipeline Status, Constraints, Decisions Log |
| V-10 | pt_version | GC-v1 frontmatter | `pt_version` field present |
| V-11 | Tier rename | Grep for `Estimated Complexity` or `complexity:` | NOT found |
| V-12 | P2/P3 logic | Read Phase 2 and Phase 3 sections | Only seq-thinking lines removed |
| V-13 | Clean Term | Read Clean Termination section | Unchanged from original |

---

## 7. Validation Checklist

### V1: Structural Integrity
- [ ] All markdown headers properly nested (##, ###)
- [ ] All code blocks opened and closed (matching ``` pairs)
- [ ] All tables have correct column counts
- [ ] Decision tree ASCII art properly aligned

### V2: AD Coverage
- [ ] AD-1: P0 is existence check only (no PT creation, no tier)
- [ ] AD-2: Feasibility Check exists in Phase 1.2
- [ ] AD-3: Checkpoint at 1.2.5, section 1.3.5 deleted
- [ ] AD-4: Tier fields in Scope Statement, Tier Routing subsection deleted
- [ ] AD-5: /permanent-tasks invocation at Gate 1 Step 1
- [ ] AD-6: 9 inline removals + 1 consolidation in Cross-Cutting
- [ ] AD-7: git branch `| head -10`
- [ ] AD-8: 3 DPs (was 7)

### V3: Compression Options
- [ ] Option A-hybrid: GC-v1 YAML frontmatter code block + body field list
- [ ] Option B-hybrid: Orchestration-plan YAML frontmatter code block + body field list
- [ ] Option C: Gate-record compressed to reference
- [ ] Option G: Gate 1 criteria → gate-evaluation-standard.md reference

### V4: Line Count
- [ ] Total ≤ 578L (target ~575L)
- [ ] If over budget: candidates for further compression are Options D, E from architecture §8

### V5: Downstream Compatibility
- [ ] GC body sections (Scope, Pipeline Status, Constraints, Decisions Log) preserved
- [ ] /permanent-tasks invoked with same interface (no modification needed)
- [ ] Phase 2/3 entry conditions unchanged
- [ ] Clean Termination section unchanged

### V6: Code Plausibility
Since neither architect nor implementer can "run" the skill:
- [ ] P0 decision tree has valid terminal states (all paths reach P1)
- [ ] Feasibility Check has valid terminal states (all paths reach "continue" or "restart")
- [ ] Gate 1 artifact sequence has valid dependency chain (PT → GC → orch → gate-record)
- [ ] No orphaned references (all "see §X" references point to existing sections)
- [ ] The `| head -10` addition doesn't break the backtick command syntax

**V6 Recommendation:** First 3 pipeline runs, Lead should manually verify P0 flow and Gate 1 artifact sequence work correctly. Report any issues for hotfix.

---

## 8. Rollback Strategy

Single file, single commit. Rollback is trivial:

```bash
git checkout HEAD~1 -- .claude/skills/brainstorming-pipeline/SKILL.md
```

**Pre-edit safety:** Before Task A begins, the implementer should verify:
```bash
git status .claude/skills/brainstorming-pipeline/SKILL.md
```
If the file has uncommitted changes, alert Lead before proceeding.

---

## 9. Commit Strategy

Single commit after all tasks pass:

```bash
git add .claude/skills/brainstorming-pipeline/SKILL.md
git commit -m "$(cat <<'EOF'
feat(skill): redesign brainstorming-pipeline P0/P1 flow — 8 ADs

Implement 8 Architecture Decisions for brainstorming-pipeline:
- AD-1: P0 → PT existence check only (no creation, no tier)
- AD-2: Feasibility Check (3-criteria soft gate after PURPOSE)
- AD-3: Checkpoint relocated to 1.2.5 (was 1.3.5)
- AD-4: Scope + Tier unified at 1.4
- AD-5: PT creation at Gate 1 via /permanent-tasks
- AD-6: Sequential-thinking consolidated (9 inline → 1 cross-cutting)
- AD-7: Git branch output capped (head -10)
- AD-8: RTD DPs reduced (7 → 3)

Plus compression: GC/orchestration templates (hybrid), gate criteria (reference).
672L → ~575L.

Architecture: .agent/teams/bp-skill-enhance/phase-3/architect-1/L3-full/

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## 10. Known Risks

### Risk Matrix

| ID | Risk | Likelihood | Impact | Severity | Mitigation |
|----|------|-----------|--------|----------|------------|
| R-1 | Template compression reduces Lead clarity | MEDIUM | LOW | LOW | Hybrid: YAML frontmatter preserved as code block, body as field list. Field names explicit. |
| R-2 | Feasibility check false positives | LOW | MEDIUM | MEDIUM | Soft gate with explicit user override. 3 criteria are generous. |
| R-3 | No PT during Phase 1 Q&A | LOW | LOW | LOW | Phase 1 is Lead-only. PT consumed from Phase 2 onward. |
| R-4 | GC-v1 pt_version field breaks downstream | LOW | LOW | LOW | Additive YAML field. No downstream skill parses individual frontmatter fields. |
| R-5 | P2/P3 seq-thinking removal = "logic change" | MEDIUM | LOW | LOW | Cross-cutting edit only. No behavioral change. SKILL.md is Lead-only. |
| R-6 | Line count target missed | MEDIUM | LOW | LOW | Conservative compression. Options D, E available as reserves. |
| R-7 | Edit tool old_string mismatches | LOW | MEDIUM | MEDIUM | Section-ordered execution minimizes cascading shifts. AC-0 catches drift. |
| R-8 | /permanent-tasks at Gate 1 disrupts flow | LOW | MEDIUM | MEDIUM | Same Skill tool mechanism as current P0. [Sub-skill] annotation in spec. |

### Phase 5 Targets (for devils-advocate or validation)

| # | Assumption | Evidence | Risk-if-Wrong |
|---|-----------|----------|---------------|
| T-1 | SKILL.md is Lead-only (teammates don't read it) | Teammates receive [DIRECTIVE], not raw SKILL.md | If wrong: AD-6 removal could reduce compliance. Mitigated by CLAUDE.md §7. |
| T-2 | GC body consumed by section name, not template format | D1: write-plan embeds GC-v3 body by section | If wrong: compressed field-list breaks downstream. Monitor first 3 runs. |
| T-3 | /permanent-tasks returns control to caller | Standard CC Skill tool behavior; current P0 proves this | If wrong: Gate 1 sequence hangs. Low probability. |
| T-4 | Architecture line counts approximately correct | Each section analyzed independently | If wrong: may need options D, E. Low severity. |
