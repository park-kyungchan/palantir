## Summary

GC serves three distinct roles across 5 downstream skills: (1) phase completion gating, (2) session/artifact discovery, and (3) rich context carrier. PT can fully substitute for roles 1 and 2, but NOT role 3 — the rich Phase 1-3 outputs (Scope Statement, Research Findings, Architecture Summary, Interface Contracts) currently live in GC and have no PT equivalent. The hook is already PT-first and needs no modification. `/permanent-tasks` can be invoked at Gate 1 without code changes.

---

## D1: GC Downstream Dependencies

### Skill-by-Skill Analysis

#### 1. agent-teams-write-plan/SKILL.md

**GC references (11 locations):**
- Line 21: Precondition check `GC-v3 with Phase 3 COMPLETE?`
- Line 33: Dynamic Context `ls -d .agent/teams/*/global-context.md` (session discovery)
- Line 91: Input Discovery looks for GC files with `Phase 3: COMPLETE`
- Line 106: V-1 validation: `global-context.md exists with Phase 3: COMPLETE`
- Line 108: V-3 validation: `GC-v3 contains Scope, Component Map, Interface Contracts sections`
- Line 123: Phase 4.2 Team Setup: `copy GC-v3 to new session directory`
- Line 166: Directive construction: `GC-v3 full embedding` (entire global-context.md)
- Line 236: Gate 4 criterion G4-8: `Plan satisfies GC-v3 Phase 4 Entry Requirements`
- Line 259: Gate auditor receives GC as evidence
- Lines 263-266: GC-v3 → GC-v4 update (adds Implementation Plan Reference, Task Decomposition, File Ownership Map, Phase 6 Entry Conditions, Phase 5 Validation Targets, Commit Strategy)

**GC fields consumed:** Scope, Component Map, Interface Contracts, Phase Pipeline Status, Phase 4 Entry Requirements, Research Findings, Constraints, Architecture Summary, Architecture Decisions (all via GC-v3 full embedding)

**PT substitutability:** PARTIAL — PT has User Intent, Impact Map, Decisions, Constraints, Phase Status. Missing: Scope Statement, Component Map, Interface Contracts, Research Findings, Phase 4 Entry Requirements. These are Phase 1-3 outputs.

#### 2. plan-validation-pipeline/SKILL.md

**GC references (7 locations):**
- Line 22: Precondition check `GC-v4 with Phase 4 COMPLETE?`
- Line 33: Dynamic Context `ls -d .agent/teams/*/global-context.md`
- Line 91: Input Discovery looks for GC with `Phase 4: COMPLETE`
- Line 110: V-1 validation: `global-context.md exists with Phase 4: COMPLETE`
- Line 113: V-4 validation: `GC-v4 contains Scope, Phase 4 decisions, and implementation task breakdown`
- Line 128: `copy GC-v4 to new session directory`
- Lines 264, 312-315: GC update with Phase 5 status + mitigations

**GC fields consumed:** Scope, Phase 4 decisions, Implementation task breakdown, Phase Pipeline Status

**PT substitutability:** PARTIAL — PT has Architecture Decisions and Phase Status. Missing: Scope Statement, Implementation task breakdown (added to GC-v4 by write-plan).

#### 3. agent-teams-execution-plan/SKILL.md

**GC references (6 locations):**
- Line 39: Dynamic Context `ls -d .agent/teams/*/global-context.md`
- Line 97: Input Discovery looks for GC with `Phase 4: COMPLETE` or `Phase 5: COMPLETE`
- Line 119: V-1 validation: `global-context.md exists with Phase 4 or 5 COMPLETE`
- Line 135: `copy GC-v4 to new session directory`
- Line 354: Code-reviewer template: `See global-context for project-level constraints`
- Lines 553-580: GC-v4 → GC-v5 update (Implementation Results, Interface Changes, Gate 6 Record, Phase 7 Entry Conditions)

**GC fields consumed:** Phase Pipeline Status, project-level constraints (code-reviewer)

**PT substitutability:** HIGH — Execution plan reads primarily from docs/plans/ for implementation details. GC is used for phase status and constraints, both available in PT.

#### 4. verification-pipeline/SKILL.md

**GC references (5 locations):**
- Line 116: V-1 validation: `global-context.md exists with Phase 6: COMPLETE`
- Line 149: `copy GC-v5 to new session directory`
- Lines 317, 429: GC updates with Phase 7/8 COMPLETE status
- Lines 445-462: Clean termination GC update (Verification Results, Phase 9 Entry Conditions)

**GC fields consumed:** Phase Pipeline Status only

**PT substitutability:** HIGH — GC is used purely as phase status tracker and to record verification results. PT can handle both.

#### 5. delivery-pipeline/SKILL.md

**GC references (2 locations):**
- Line 127: V-1: `PT exists with Phase 7/8 COMPLETE — OR — GC exists with equivalent status. If both exist, PT takes precedence`
- Line 275: GC listed in "Always Preserve" cleanup category

**GC fields consumed:** Phase Pipeline Status (but only as fallback when PT doesn't exist)

**PT substitutability:** FULL — Skill already prefers PT over GC (line 127: "PT takes precedence"). GC is explicit legacy fallback.

### GC Role Classification

| Role | Description | Skills Using | PT Substitutable? |
|------|-------------|-------------|-------------------|
| Phase Gating | Check `Phase N: COMPLETE` | All 5 | YES — PT has Phase Status |
| Session Discovery | `ls .agent/teams/*/global-context.md` in Dynamic Context | write-plan, validation, execution, verification (4/5) | NO — PT is a Task API entity, not a file; new discovery mechanism needed |
| Context Carrier | Full GC content embedding in directives, section validation | write-plan (V-3, directive), validation (V-4) | NO — PT lacks Scope Statement, Research Findings, Architecture Summary, Component Map, Interface Contracts |

### Critical Finding

**GC as context carrier is the primary barrier to full PT substitution.** The write-plan skill embeds the ENTIRE GC-v3 (line 166: `GC-v3 full embedding`) into the architect's directive. This includes rich Phase 1-3 outputs that PT doesn't carry:

1. Scope Statement (from Phase 1)
2. Research Findings + Codebase Constraints (from Phase 2)
3. Architecture Summary + Architecture Decisions + Phase 4 Entry Requirements (from Phase 3)
4. Component Map + Interface Contracts (from Phase 3)

If GC is simplified to an artifact index, this content must live somewhere else — either in PT (making it very large) or in referenced files that GC indexes.

---

## D2: PT Creation Interface

### Input
- `$ARGUMENTS` — requirement description or context (line 6: argument-hint)
- Conversation context — full conversation history (line 78)
- Dynamic Context: infrastructure version, recent git changes, existing plans (lines 34-41)
- Existing TaskList result (line 50)

### Output

**CREATE path (Step 2A, lines 76-97):**
- `TaskCreate` with:
  - subject: `[PERMANENT] {feature/project name}`
  - description: PT Description Template (5 mandatory sections)
  - activeForm: `"Managing PERMANENT Task"`

**PT Description Template sections (lines 199-234):**
1. `### User Intent` — what user wants to achieve
2. `### Codebase Impact Map` — module dependencies, ripple paths, interfaces, risk hotspots
3. `### Architecture Decisions` — confirmed design decisions with rationale
4. `### Phase Status` — pipeline progress per phase
5. `### Constraints` — technical constraints, project rules
6. `### Budget Constraints (Optional)` — spawn limits, iteration limits

**UPDATE path (Step 2B, lines 101-158):**
- `TaskGet` → Read-Merge-Write (deduplicate, resolve contradictions, elevate abstraction) → `TaskUpdate` with version bump
- Teammate notification if CRITICAL impact

### Can It Be Invoked at Gate 1?

**YES — no modification needed.** Evidence:

1. The skill is explicitly designed as standalone (line 11: "The PERMANENT Task is a Task API entity... discovered dynamically via TaskList search")
2. It takes `$ARGUMENTS` and conversation context as input — both available at Gate 1
3. It has no Phase-0-specific dependencies — no references to "must run before Phase 1"
4. Line 27: "This skill is used standalone or auto-invoked from Phase 0 of pipeline skills" — the "auto-invoked from Phase 0" is a usage pattern, not a technical constraint
5. At Gate 1, MORE context is available (Scope Statement, approach selection, complexity) than at Phase 0, resulting in a richer initial PT

**Impact on other skills:** All 5 downstream skills have Phase 0 blocks that handle "PT not found" gracefully (AskUser → create or continue without). Moving PT creation to Gate 1 in brainstorming-pipeline means downstream skills would find the PT already created. No modification needed.

---

## D3: Hook GC References

### File: `.claude/hooks/on-subagent-start.sh` (93 lines)

**GC fields read:**
- Line 55: `version:` frontmatter field ONLY — `grep -m1 '^version:' "$GC_FILE" | awk '{print $2}'`
- No other GC fields are read. The hook does NOT parse Scope, Constraints, Decisions, or any content sections.

**What it does with GC data:**
- Lines 57-63: Constructs `additionalContext` JSON: `"Active team: {team}. Current GC: {version}. Verify your injected context version matches."`
- This is injected into the spawned agent's context via `hookSpecificOutput`

**Three execution paths:**

| Path | Condition | Lines | Action |
|------|-----------|-------|--------|
| 1 (GC) | Team exists + GC file exists | 50-65 | Inject GC version string |
| 2 (PT) | Team exists + no GC file | 67-74 | Inject PT guidance: "Use TaskGet on [PERMANENT]" |
| 3 (Fallback) | No team | 77-90 | Find most recent GC across all teams |

**Key architectural insight:** The hook is already designed with a PT-first, GC-legacy architecture:
- Path 2 (lines 67-74) is the PT path — it only activates when GC doesn't exist
- The message "Context is managed via PERMANENT Task" already guides agents to use TaskGet
- This means the hook anticipates a future where GC doesn't exist

**Impact of GC simplification scenarios:**

| Scenario | Hook Impact | Modification Needed? |
|----------|-------------|---------------------|
| GC simplified to artifact index with `version:` frontmatter | Path 1 still works — reads version field | NO |
| GC removed entirely | Path 2 activates automatically — PT guidance injected | NO |
| GC renamed or restructured without `version:` field | Path 1 fails silently (no version found), falls through to Path 2 | NO (graceful degradation) |

---

## PT Goal Linkage

- **R-1 (GC simplification):** GC CAN be simplified to artifact index IF the rich context (Scope, Research, Architecture) is moved to referenced files. PT handles phase gating and constraints. Session discovery needs a new mechanism (PT is not a file).
- **R-2 (PT creation timing):** Gate 1 is a better creation point — more context available, no code changes to /permanent-tasks needed.
- **R-3 (Hook impact):** Zero impact — hook is already PT-aware with built-in fallback.

---

## Evidence Sources

| Source | Lines Referenced | Domain |
|--------|----------------|--------|
| `.claude/skills/agent-teams-write-plan/SKILL.md` | 21, 33, 91, 106, 108, 123, 166, 236, 259, 263-266 | D1 |
| `.claude/skills/plan-validation-pipeline/SKILL.md` | 22, 33, 91, 110, 113, 128, 264, 312-315 | D1 |
| `.claude/skills/agent-teams-execution-plan/SKILL.md` | 39, 97, 119, 135, 354, 553-580 | D1 |
| `.claude/skills/verification-pipeline/SKILL.md` | 116, 149, 317, 429, 445-462 | D1 |
| `.claude/skills/delivery-pipeline/SKILL.md` | 127, 275 | D1 |
| `.claude/skills/permanent-tasks/SKILL.md` | 6, 11, 27, 50, 76-97, 101-158, 199-234 | D2 |
| `.claude/hooks/on-subagent-start.sh` | 50-74, 55, 67-74, 77-90 | D3 |
| `.claude/skills/brainstorming-pipeline/SKILL.md` | 241-268, 419-429, 546-558 | D1 (GC creation points) |
