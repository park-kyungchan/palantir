---
name: rsil-review
description: "Meta-Cognition quality review — applies 8 universal research lenses and integration audit to any target. Layer 1/2 boundary analysis with AD-15 filter. Lead-only, no teammates spawned directly."
argument-hint: "[target skill/component/scope + specific concerns]"
---

# RSIL Review

Meta-Cognition-Level quality review skill with ultrathink deep reasoning. Applies
universal research lenses and integration auditing to any target within .claude/
infrastructure. Identifies Layer 1 (NL-achievable) improvements and Layer 2
(Ontology Framework) deferrals.

**Announce at start:** "I'm using rsil-review to run Meta-Cognition quality review
for: $ARGUMENTS"

**Core flow:** PT Check → R-0 Lead Synthesis → R-1 Parallel Research → R-2 Classification → R-3 Application → R-4 Record

## When to Use

```
Have a completed pipeline phase or INFRA component to review?
├── Want structured quality improvement? ─── no ──→ Manual review
├── yes
├── Target is within .claude/ INFRA or pipeline skills? ── no ──→ Not applicable
├── yes
└── Use /rsil-review {target + scope + concerns}
```

**What this skill does:** Combines CC-native capability research with cross-file
integration auditing. Produces actionable NL improvements (Category B) and documents
Layer 2 gaps (Category C). Never proposes new hooks (AD-15 8→3 inviolable).

**What this skill does NOT do:** Modify application code, run tests, spawn long-lived
teammates, or auto-chain to other skills.

## Dynamic Context

!`ls /home/palantir/.claude/hooks/*.sh 2>/dev/null`

!`jq -r '.hooks | keys[]' /home/palantir/.claude/settings.json 2>/dev/null`

!`ls /home/palantir/.claude/agents/*.md 2>/dev/null | xargs -I{} basename {}`

!`ls /home/palantir/.claude/skills/*/SKILL.md 2>/dev/null | sed 's|.*/skills/||;s|/SKILL.md||'`

!`head -3 /home/palantir/.claude/CLAUDE.md 2>/dev/null`

!`cd /home/palantir && git diff --name-only HEAD~1 2>/dev/null | head -20`

!`wc -l /home/palantir/.claude/references/agent-common-protocol.md 2>/dev/null`

!`wc -l $ARGUMENTS 2>/dev/null`

!`cat ~/.claude/agent-memory/rsil/MEMORY.md 2>/dev/null | head -50`

**Feature Input:** $ARGUMENTS

---

## Phase 0: PERMANENT Task Check

Call `TaskList` and search for a task with `[PERMANENT]` in its subject.

```
TaskList result
     │
┌────┴────┐
found      not found
│           │
▼           ▼
TaskGet →   AskUser: "No PERMANENT Task found.
read PT     Create one for this feature?"
│           │
▼         ┌─┴─┐
Continue  Yes   No
to R-0    │     │
          ▼     ▼
        /permanent-tasks    Continue to R-0
        creates PT-v1       without PT
        → then R-0
```

---

## Static Layer: Layer Definitions

These definitions are permanent. They define what Layer 1 can do and what requires Layer 2.
Embed the relevant portions in agent directives during Phase R-0.

### Layer 1 — Claude Code CLI + Opus 4.6 + Agent Teams

Everything achievable through these native mechanisms:

- **NL Instructions:** CLAUDE.md, agent .md (6 types), skill .md, references .md.
  Opus 4.6 follows nuanced multi-paragraph NL with high fidelity, infers intent
  from context without rigid formatting.
- **Configuration:** settings.json (hooks, permissions, env, plugins, language,
  teammateMode). Agent frontmatter (disallowedTools). Skill frontmatter (name,
  description, argument-hint).
- **3 Lifecycle Hooks:** SubagentStart (context injection), PreCompact (state
  preservation), SessionStart (recovery context). Handler types: command, prompt.
  No additions allowed (AD-15).
- **Task API:** TaskCreate (subject, description, activeForm, metadata),
  TaskUpdate (status, owner, blocks, blockedBy, metadata merge), TaskList, TaskGet.
  PERMANENT Task pattern: [PERMANENT] subject, versioned PT-v{N}.
- **Agent Teams:** TeamCreate, TeamDelete, SendMessage (message, broadcast,
  shutdown_request/response, plan_approval_response). Team config with member list.
- **Task Tool:** subagent_type (researcher, architect, implementer, tester,
  integrator, devils-advocate, general-purpose, Explore, Plan, Bash,
  claude-code-guide, superpowers:code-reviewer). Parameters: team_name, name,
  mode, model, max_turns, run_in_background, resume.
- **Skills:** YAML frontmatter, dynamic context injection (bang-backtick pattern), $ARGUMENTS.
- **MCP Tools:** sequential-thinking, tavily (search/extract/crawl/map/research),
  context7 (resolve-library-id, query-docs), github (repos, issues, PRs, files).
- **Opus 4.6:** 200K context (1M beta), 128K output, adaptive thinking, measured
  language (responds best to natural instructions, not excessive markers).
- **Agent Memory:** .claude/agent-memory/{role}/MEMORY.md (cross-conversation).
  Session-scoped: .agent/teams/{session-id}/TEAM-MEMORY.md.
- **Context Management:** Auto-compact with SessionStart recovery hook, PreCompact
  state snapshot, L1/L2/L3 artifact system for work preservation.

### Layer 2 — Ontology Framework (NOT available)

Things that cannot be achieved through Layer 1 alone:

- Structured entity definitions with schema validation and type systems
- Persistent state machines with formal transitions, guards, and rollback
- Cross-session knowledge graphs with structured queries
- Artifact registries with versioned schemas and integrity validation
- Structured audit trails with query capabilities
- Domain abstraction layers between orchestration and domain logic
- Parameterized gate criteria derived from domain models
- Formal interface contract verification beyond NL assertions
- Constraint propagation engines for dependency analysis
- Real-time monitoring dashboards with structured metrics

### Boundary Test

Apply to every finding:

```
"Can this be achieved through NL .md instructions + 3 existing hooks
 + Task API + MCP tools + Agent Teams messaging + Skill features?"

YES     → Layer 1, Category B — propose exact NL text change
NO      → Layer 2, Category C — document why L1 insufficient
PARTIAL → Split: L1 portion as B + L2 remainder as C
Hook    → REJECT unconditionally (AD-15: 8→3 inviolable)
```

---

## Static Layer: 8 Meta-Research Lenses

Universal quality principles. Apply to any target — the specific research questions
are generated by Lead in Phase R-0 based on which lenses are relevant to $ARGUMENTS.

| # | Lens | Core Question |
|---|------|---------------|
| L1 | TRANSITION INTEGRITY | Are state transitions explicit and verifiable? Could implicit transitions allow steps to be skipped? |
| L2 | EVALUATION GRANULARITY | Are multi-criteria evaluations individually evidenced? Or bundled into single pass-through judgments? |
| L3 | EVIDENCE OBLIGATION | Do output artifacts require proof of process (sources, tools used)? Or only final results? |
| L4 | ESCALATION PATHS | Do critical findings trigger appropriate multi-step responses? Or only single-shot accept/reject? |
| L5 | SCOPE BOUNDARIES | Are shared resources accessible across scope boundaries? Are cross-scope access patterns handled? |
| L6 | CLEANUP ORDERING | Are teardown/cleanup prerequisites explicitly sequenced? Or assumed to "just work"? |
| L7 | INTERRUPTION RESILIENCE | Is intermediate state preserved against unexpected termination? Or does the process assume completion? |
| L8 | NAMING CLARITY | Are identifiers unambiguous across all contexts where they appear? Or could the same name mean different things? |

Lenses evolve: if new universal patterns are discovered, add L9, L10, etc. Update this
table and MEMORY.md accordingly.

---

## Static Layer: AD-15 Filter

| Category | Test | Action |
|----------|------|--------|
| A (Hook) | Would require adding a new hook | REJECT unconditionally |
| B (NL) | Achievable through .md file changes | ACCEPT — propose exact text |
| C (Layer 2) | Requires structured systems | DEFER — document why L1 insufficient |

---

## Static Layer: Integration Audit Methodology

Universal procedure for cross-file consistency verification. The specific axes are
derived by Lead in Phase R-0 based on the target's file references.

```
1. Identify affected files (what TARGET references + what references TARGET)
2. For each file pair (A, B) with a reference relationship:
   a. Does A's reference to B match B's actual content?
   b. Does B's reference to A match A's actual content?
   c. Are shared terms/identifiers used consistently?
   d. Are there orphan references (pointing to deleted/moved content)?
   e. Are there stale protocol markers (should be 0)?
3. Classify inconsistencies by severity:
   BREAK — runtime failure or incorrect agent behavior
   FIX   — quality degradation or stale reference
   WARN  — cosmetic or minor deviation
```

---

## Static Layer: Output Format

Both agents produce structured findings reports.

**[A] claude-code-guide output should include:**
- Findings Table: ID, Finding, Layer, Category, Lens, CC Evidence
- Category B Detail: What, Where (file:section), CC Capability, Why suboptimal, Proposed NL text
- Category C Detail: What, Why L1 cannot, What L2 provides, Current best NL workaround
- L1 Optimality Score (X/10)
- Top 3 Recommendations

**[B] Explore output should include:**
- Axis Results Table: Axis, File A, File B, Status, Findings
- Findings Detail: Axis, Severity, File A (path:line + content), File B (path:line + content), Inconsistency, Specific fix
- Integration Score (X/N axes passing)

---

## Phase R-0: Lead Synthesis

The core phase. Lead transforms the universal framework into target-specific
agent directives. Use sequential-thinking for every step.

No agents spawned in this phase. Lead-only.

### Step 0: Parse $ARGUMENTS

Extract from $ARGUMENTS:

- **TARGET:** The review subject (skill name, hook file, agent file, component, "all INFRA", etc.)
- **SCOPE:** Boundary of the review (specific phase, specific function, full coverage, etc.)
- **CONCERN:** User's specific worries or focus areas (if stated)

If $ARGUMENTS is empty or ambiguous, use AskUserQuestion to clarify before proceeding.

### Step 1: Target Reading

Read the TARGET file(s) to understand structure:

- What sections/phases does the target contain?
- What external files does it reference (paths, imports, cross-references)?
- What agent types, hooks, or APIs does it use?
- What workflows, gates, or checkpoints does it define?

For INFRA-wide targets, read the key files: CLAUDE.md, settings.json,
agent-common-protocol.md, and sample representative files.

### Step 2: Lens Application → Research Questions

Apply each of the 8 Lenses to TARGET using sequential-thinking:

```
FOR EACH Lens (L1 through L8):
  │
  ├── Is this Lens relevant to TARGET?
  │   │
  │   ├── YES → Which specific part of TARGET does it apply to?
  │   │         → Generate a concrete Research Question (RQ)
  │   │         Example: L1 × execution-plan §6.3 →
  │   │         "Is Understanding Verification's Step1→Wait→Step2
  │   │          transition explicitly enforced in the directive?"
  │   │
  │   └── NO / LOW RELEVANCE → Skip this Lens for this target
  │
  Result: 3~10 target-specific Research Questions
```

The same Lenses produce different questions for different targets. This is the
mechanism that makes the skill universal without hardcoding.

### Step 3: Affected Files → Integration Axes

Derive integration axes from the target's file relationships:

```
a) Files that TARGET references (paths, imports mentioned in content)
b) Files that reference TARGET (grep: which .claude/ files mention TARGET?)
c) Shared contract files (CLAUDE.md, agent-common-protocol.md, settings.json)
d) Each (A ↔ B) reference pair = one Integration Axis
e) For each Axis: define what "consistent" means for this specific pair

Result: 2~8 target-specific Integration Axes with file pairs
```

### Step 4: Agent Directive Construction

Build two agent directives by combining Static Layer + R-0 output:

**[A] claude-code-guide directive:**
```
Static:  Layer 1/2 definitions (from S-A/S-B) + Boundary Test (S-C)
         + Output Format (S-G [A] section)
Dynamic: Research Questions from Step 2
         + TARGET path and structure summary
         + User CONCERN (if any)
Instruction: "Research CC documentation for each RQ.
              Classify each finding as L1 or L2.
              For L1: propose exact NL text change.
              For L2: explain why L1 is insufficient."
```

**[B] Explore directive:**
```
Static:  Integration Audit Methodology (S-E) + Output Format (S-G [B] section)
Dynamic: Integration Axes from Step 3 (file pairs + consistency criteria)
         + Dynamic Context (.claude/ current state)
         + User CONCERN (if any)
Instruction: "Read ALL axis file pairs. Verify each axis bidirectionally.
              Check for stale references, orphans, protocol markers.
              Classify by severity: BREAK / FIX / WARN."
```

Present R-0 synthesis summary to user before spawning:

```
"R-0 synthesis complete:
 - TARGET: {target}
 - Lenses applied: {M}/8 → {N} Research Questions generated
 - Integration Axes: {K} derived from file references
 Spawning [A] and [B] agents."
```

---

## Phase R-1: Parallel Research

Spawn two agents concurrently. Neither is a persistent teammate — both are
one-shot Task tool invocations.

```
[A] Task tool:
  subagent_type: "claude-code-guide"
  prompt: {constructed directive from R-0 Step 4}

[B] Task tool:
  subagent_type: "Explore"
  prompt: {constructed directive from R-0 Step 4}
```

Both run in parallel. Wait for both to complete.

If either agent returns insufficient results (e.g., no findings, empty report),
Lead evaluates whether to proceed with the other agent's results alone or
ask the user whether to re-run with adjusted scope.

---

## Phase R-2: Synthesis + Classification

Lead merges both agents' outputs. Use sequential-thinking.

### Merge

Combine [A] findings (Layer boundary) + [B] findings (integration) into a
unified findings list.

### Classify

For each finding, apply the AD-15 filter and severity assessment:

```
[A] findings (Layer research):
  Apply Boundary Test (S-C):
  ├── L1, Category B → 🔧 FIX (NL change, apply before commit)
  ├── L2, Category C → ⏳ DEFER (record in tracker)
  └── Hook needed    → ❌ REJECT (AD-15 violation, discard)

[B] findings (Integration audit):
  Classify by impact:
  ├── Runtime failure risk    → ❌ BREAK (must fix before commit)
  ├── Quality degradation     → 🔧 FIX (should fix before commit)
  └── Cosmetic/minor          → ⚠️ WARN (note only)
```

### Present to User

```markdown
## RSIL Review Results — {$ARGUMENTS}

**Target:** {TARGET}
**Scope:** {SCOPE}
**Lenses Applied:** {M}/8 → {N} Research Questions
**Integration Axes:** {K} verified

### Layer Boundary Analysis ([A])
| ID | Finding | Layer | Cat | Proposed Change |
|----|---------|-------|-----|-----------------|

L1 Optimality Score: {X}/10

### Integration Audit ([B])
| Axis | Files | Status | Findings |
|------|-------|--------|----------|

Integration Score: {Y}/{K}

### Summary
❌ BREAK: {N} — must fix before commit
🔧 FIX:  {N} — should fix before commit
⏳ DEFER: {N} — Layer 2 (tracker)
⚠️ WARN:  {N} — noted
✅ PASS:  {N}

### Top Recommendations
1. {highest priority}
2. {second}
3. {third}
```

Wait for user decision:

```
User Decision
     │
┌────┼──────────┐
▼    ▼           ▼
Approve  Modify  Skip
│        │       │
▼        │       ▼
R-3      │    R-4 (no changes applied)
      Lead adjusts
      → re-present
```

---

## Phase R-3: Application

Lead-only. Apply user-approved items.

### Step 1: Apply BREAK items (mandatory if any exist)

- Fix INFRA inconsistencies
- Restore bidirectional references
- Remove orphan references

### Step 2: Apply FIX items (user-approved)

- Edit SKILL.md instructions (Category B NL changes)
- Update agent .md Constraints
- Correct CLAUDE.md references
- Align cross-file wording

### Step 3: Verify applied changes

Re-read modified files to confirm changes are correct.

---

## Phase R-4: Record + Terminal Summary

### Tracker Update

Update `docs/plans/2026-02-08-narrow-rsil-tracker.md`:

- Summary Table: add new row
- Detailed Findings: add new section with all findings, categories, and statuses
- Cross-Cutting Patterns: add new patterns if discovered
- Improvement Backlog: add DEFER items

### MEMORY.md Update

If a durable pattern was discovered (applicable beyond this specific target):

- Add to MEMORY.md "Narrow RSIL Process" section
- If a new Lens candidate was found, note it for future SKILL.md update

One-off findings go to tracker only. MEMORY.md receives patterns only.

### Agent Memory Update

Update `~/.claude/agent-memory/rsil/MEMORY.md` using Read-Merge-Write:
- §1 Configuration: increment review count, update last review date
- §2 Lens Performance: update per-lens statistics from this review
- §3 Cross-Cutting Patterns: add new universal pattern (if discovered in this review)
- §4 Lens Evolution: add candidate (if a new universal pattern suggests a new lens)

Only add patterns that apply across ANY target. One-off findings stay in tracker only.

### PT Update

If a PERMANENT Task exists, update Phase Status with RSIL results.

### Terminal Summary

```markdown
## RSIL Review Complete

**Target:** {$ARGUMENTS}
**Lenses Applied:** {M}/8
**Research Questions:** {N}
**Integration Axes:** {K}

**Results:**
├── ❌ BREAK applied: {N}
├── 🔧 FIX applied:  {N}
├── ⏳ DEFER logged:  {N} (Layer 2)
├── ⚠️ WARN noted:   {N}
└── ✅ PASS:          {N}

**L1 Optimality:** {X}/10
**Integration Health:** {Y}/{K} axes

**Artifacts:**
• narrow-rsil-tracker.md — updated
• MEMORY.md — {updated / unchanged}
• {N} files modified

**Cumulative RSIL Data:**
Total findings: {cumulative} | Acceptance rate: {%}

Pipeline complete. No auto-chaining.
```

---

## Error Handling

| Situation | Response |
|-----------|----------|
| $ARGUMENTS empty or unclear | AskUserQuestion: "Specify review target" |
| TARGET file not found | AskUserQuestion: "Verify file path" |
| No Lenses applicable | Warn: "Low Lens coverage. Integration audit only?" |
| [A] finds 0 improvements | Report: "L1 optimal. Integration results only." |
| [B] finds BREAK items | Present BREAKs first: "Must fix before commit." |
| All findings PASS | Report: "Clean review. No changes needed." |
| User cancellation | Preserve partial tracker updates. No file changes. |
| Context compact | Read tracker for last state. Resume from incomplete phase. |

---

## Principles

- Framework is universal, scope is dynamic — generate Research Questions and Integration Axes from Lenses in R-0, never hardcode them
- R-0 synthesis is the core value — the universal→specific bridge is mandatory for every review
- Accumulated context distills into Lenses — individual findings stay in tracker, not SKILL.md
- AD-15 inviolable — Category A REJECT, B ACCEPT, C DEFER. Never propose new hooks.
- Layer 1/2 boundary test is definitive — if Layer 2 is needed, it's DEFER. Never promote C to B.
- Lenses evolve — new universal patterns from future reviews become L9, L10
- Every finding cites CC documentation or file:line references — no unsupported claims
- User confirms all changes — present findings, wait for approval before modifying files
- Use sequential-thinking at every decision point throughout the review
- Terminal skill — user decides next step. No auto-chaining to other skills.
- Never embed raw findings in SKILL.md — only universal Lenses belong here
