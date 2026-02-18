# Self-Diagnose — Detailed Methodology

> On-demand reference. Contains category-specific diagnostic steps, constraint-implication table, unverified-claim detection tables, and DPS delegation template.

---

## Category 9 — Constraint-Implication Alignment (Full Detail)

Traces each CC native constraint to its design implications and verifies current INFRA respects them.

| CC Native Constraint | Design Implication | Verification Check |
|---------------------|-------------------|-------------------|
| No shared memory between agents | Information must be explicitly communicated; external file refs are phantom dependencies | Verify no skill/agent assumes implicit context sharing. Check all cross-agent data has explicit delivery mechanism (DPS inline, SendMessage, or disk+path). |
| Agent ≠ skill context | Agent does not see skill L2 body; DPS must fully convey execution instructions | Verify DPS templates include all execution-critical info from skill L2 (Phase-Aware, error handling, output format). |
| Lead compaction risk | Inter-phase routing state may be lost during auto-compaction | Verify PT metadata captures enough state for phase resumption. Check pipeline-resume can reconstruct from PT alone. |
| SendMessage = text only | Cannot inject structured data into agent context; summary must be self-contained | Verify micro-signal formats contain enough context for Lead routing decisions without loading full disk output. |
| Inbox = poll per API turn | No real-time coordination; teammate sees messages only on next turn | Verify no skill assumes synchronous teammate response. Check all coordination is async-compatible. |
| Subagent 30K char limit | Background agent output truncated beyond 30K chars | Verify agents prioritize critical info first in output. Check large outputs use disk+path pattern. |

**Procedure:** For each row, Read the relevant ref_*.md for the constraint, then Grep/Read INFRA files to verify the check. Flag violations as HIGH severity.

---

## Category 10 — Unverified CC-Native Claims (Full Detail)

Detects behavioral claims in ref_*.md files that were codified without empirical verification.

| Check | Method | What It Detects |
|-------|--------|-----------------|
| Behavioral verb scan | Grep ref_*.md for "persist", "survive", "trigger", "inject", "deliver", "auto-", "ephemeral", "transient" | Claims about CC runtime behavior |
| Evidence presence | For each claim: check for file:line evidence or "Verified:" annotation | Unverified assertions presented as facts |
| Cross-reference | Compare claim against actual filesystem state | Claims contradicted by current system state |

**For each unverified claim found:** flag as HIGH severity with the claim text, source file:line, and suggested verification method (Glob/Read test to run via research-cc-verify).

**Origin:** SendMessage "ephemeral" error (2026-02-17). Lead's reasoning-only judgment produced incorrect CC-native claim → propagated to 4 ref files before user caught it. Cost: full correction cycle. Prevention: this category + research-cc-verify Shift-Left gate.

---

## DPS Delegation Template

For STANDARD/COMPLEX tiers, construct the analyst delegation prompt using these fields:

### Context (D11 priority: cognitive focus > token efficiency)
- **INCLUDE:** CC native field reference from cache (ref_*.md files). Diagnostic checklist with 10 categories. All .claude/ file paths within scan scope.
- **EXCLUDE:** Agent-memory runtime data, pipeline history, other homeostasis skills' findings.
- **Budget:** Context ≤ 30% of analyst context window.

### Task
For each diagnostic category, scan all relevant files. Record findings with file:line evidence. Classify severity per the checklist.

### Constraints
- Read-only analyst agent. No modifications.
- Grep scope limited to .claude/. Exclude agent-memory/ (historical, not active config).
- maxTurns: 20 (STANDARD), 15 each (COMPLEX parallel pair).

### Expected Output
L1 YAML with `findings_total`, `findings_by_severity`, `findings[]`. L2 markdown with per-category analysis.

### Delivery
Write full result to `tasks/{team}/homeostasis-self-diagnose.md`. Send micro-signal to Lead via SendMessage:
```
{STATUS}|findings:{N}|severity_high:{N}|ref:tasks/{team}/homeostasis-self-diagnose.md
```
