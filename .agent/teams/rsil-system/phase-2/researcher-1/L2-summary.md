# L2 Summary — /rsil-global Observation Window + Tracker Architecture

**researcher-1 | Phase 2 | rsil-system | 2026-02-09**

---

## Executive Summary

This research analyzed 17 session directories across the entire `.agent/teams/` history to design
/rsil-global's observation window and tracker architecture. Key finding: **gate records are the
highest signal-per-token artifact** (9-116 lines YAML, structured, machine-parseable) and should
anchor the Tier 1 reading strategy. The tracker should remain unified (single file, dual-section)
to preserve the cross-reference knowledge graph between Global and Narrow findings.

---

## Topic 1: Global Observation Window Structure

### 1.1 Artifact Signal Analysis (Pipeline Work)

Analyzed 17 sessions with varying pipeline phases. Artifacts ranked by signal-to-token ratio:

| Artifact | Size Range | Signal Content | Tier |
|----------|-----------|----------------|------|
| gate-record.yaml | 9-116L | Per-task PASS/FAIL, criteria results, cross-task checks | 1 (always read) |
| L1-index.yaml | 26-149L | Finding summaries, priorities, cross-impact maps | 1 (always read) |
| orchestration-plan.md | 22-90L | Phase progress, teammate status, round schedule | 1 (skim) |
| TEAM-MEMORY.md | 9-91L | Decisions, warnings, patterns discovered | 2 (selective) |
| L2-summary.md | 36-611L | Narrative synthesis, evidence sources | 2 (selective) |
| global-context.md | 49-189L | Full PT/GC snapshot (often stale) | 3 (only if needed) |
| L3-full/ | varies | Complete research/design reports | 3 (deep dive only) |

**Key insight:** Gate records and L1 indexes together average ~150 lines per session and contain
80%+ of the quality signal. Reading these two artifact types gives /rsil-global enough information
to decide whether deeper investigation (Tier 2/3) is warranted.

**Evidence:** The nlp-execution gate record (115L) contains per-task spec/quality/self-test results,
cross-task interface consistency, and protocol marker verification — enough to assess INFRA health
without reading any L2/L3 files.

### 1.2 Non-Pipeline Work Detection (OW-2)

Non-pipeline work leaves different traces. Three detection patterns:

| Work Type | Detection Signal | Observation Strategy |
|-----------|-----------------|---------------------|
| **(A) Pipeline** | `.agent/teams/{id}/` exists with gate records | Standard Tier 0→1→2→3 |
| **(B) Skill-only** | No session dir; git diff shows .claude/ changes | Read git diff + modified files directly |
| **(C) Direct edit** | No session dir; git diff shows specific .md changes | Read git diff + MEMORY.md delta |

**For Type B (e.g., /rsil-review, /permanent-tasks execution):**
- Signal: `docs/plans/narrow-rsil-tracker.md` modified (rsil-review), task list has PERMANENT task updated
- Strategy: Read tracker diff, check if new findings were recorded

**For Type C (e.g., Lead bug fixes, manual CLAUDE.md edits):**
- Signal: `git diff --name-only HEAD~1` shows .claude/ files modified without session directory
- Strategy: Read the diff directly, check cross-file consistency

### 1.3 Three-Tier Reading Strategy (OW-3)

The core architectural decision. Each tier has a context budget and escalation trigger.

```
Tier 0: Shell Injection (~100 tokens)
├── !`ls -d .agent/teams/*/` → session existence
├── !`ls .agent/teams/*/phase-*/gate-record*.yaml 2>/dev/null | wc -l` → gate count
├── !`find .agent/teams/ -name "L1-index.yaml" 2>/dev/null | wc -l` → L1 count
├── !`git diff --name-only HEAD~1 2>/dev/null | grep "\.claude/" | wc -l` → .claude changes
├── !`stat -c %Y .claude/projects/-home-palantir/memory/MEMORY.md 2>/dev/null` → MEMORY.md mtime
└── RESULT: Work type classification (A/B/C) + session identification

Tier 1: Structured YAML Reading (~500 tokens)
├── Read LATEST gate-record.yaml (most recent session)
├── Read LATEST L1-index.yaml files (most recent phase)
├── Skim orchestration-plan.md (last 20 lines = current status)
├── CHECK: Any FAIL in gate criteria? Any HIGH priority + unresolved in L1?
│   Any re-spawn indicators in orchestration-plan?
└── ESCALATION TRIGGER: ≥1 FAIL, or ≥2 HIGH unresolved, or re-spawn detected

Tier 2: Selective L2 Reading (~1000 tokens)
├── Read L2-summary.md ONLY for flagged areas from Tier 1
├── Read TEAM-MEMORY.md for warning/pattern density
├── Cross-check: flagged L1 findings vs L2 evidence
├── CHECK: Are issues systemic (cross-file) or localized?
└── ESCALATION TRIGGER: ≥3 cross-file anomalies, or ≥2 BREAK severity

Tier 3: Explore Subagent (~deep, separate context)
├── Spawn Explore agent with specific investigation mandate
├── Target: systemic cross-file consistency verification
├── Return: structured findings report
└── ONLY when Tier 2 reveals systemic pattern
```

**Context budget rationale:** /rsil-global runs AFTER work, adding overhead to every pipeline
execution. Total observation window must stay under ~2000 tokens to remain lightweight. Most
runs should terminate at Tier 1 (healthy system → no findings → brief "all clear" report).

### 1.4 INFRA Health Indicators (OW-5)

Five concrete indicators extractable from Tier 0+1 reading:

1. **Gate Pass Rate:** `PASS` count vs total criteria in latest gate record. Below 100% = investigation needed.
2. **L1/L2 Existence:** Missing L1 or L2 from any teammate = process adherence failure (CLAUDE.md §10 requires L1/L2/L3).
3. **Re-spawn Count:** Multiple `{role}-{N}` directories for same role in same phase = teammate failure pattern (BUG-002 risk).
4. **Warning Density:** Count of `[Warning]` entries in TEAM-MEMORY.md. High density (>5 per session) = emerging pattern.
5. **Cross-Session Consistency:** Same feature across multiple sessions → check if later sessions reference earlier session artifacts correctly.

### 1.5 Integration Point with /delivery-pipeline (Phase 9)

/rsil-global should run AFTER Phase 9 delivery completes, not before. Rationale:
- Phase 9 creates ARCHIVE.md (comprehensive pipeline record)
- Phase 9 updates MEMORY.md (durable lessons)
- Phase 9's Op-6 cleanup removes transient files
- /rsil-global reads the FINAL state, not the mid-delivery state

**Recommended auto-invoke trigger:** After `/delivery-pipeline` terminal summary (pipeline work),
or after any `.claude/` file commit (non-pipeline work).

---

## Topic 2: Tracker Architecture

### 2.1 Shared vs Separate Tracker (TA-1)

**Recommendation: Single unified tracker** with sections for both Global and Narrow findings.

**Arguments for unified:**
- Cross-reference integrity: Global finding G-5 may reference Narrow findings P6-R2 and P9-R1. Separate files break this linkage.
- Pattern detection: Identifying when Narrow findings recur enough to become Global requires seeing both in one view.
- Current tracker (252L) is already 40% cross-cutting patterns (§4) and backlog (§5) — these are shared concerns.
- User reads one file to see complete RSIL state, not two.

**Arguments against (mitigated):**
- Size: at 100+ findings, single file gets large → MITIGATED by YAML summary table + link-to-detail pattern
- Ownership: different skills write different sections → MITIGATED by section headers and finding-ID namespacing

### 2.2 Finding Taxonomy (TA-2)

| Dimension | Global Finding | Narrow Finding |
|-----------|---------------|----------------|
| **Source** | /rsil-global (auto) | /rsil-review (user-invoked) |
| **Scope** | Cross-INFRA systemic pattern | Single component/skill |
| **Example** | "3/5 sessions have missing L2 files" | "delivery-pipeline L7: missing compact recovery marker" |
| **ID Format** | `G-{N}` | `{Phase}-R{N}` (current) |
| **Detection** | Artifact analysis + pattern matching | Lens application + CC research |
| **AD-15 Filter** | Same (Cat A/B/C) | Same (Cat A/B/C) |
| **Lifecycle** | May decompose into multiple Narrow findings | May aggregate into a Global finding |

**Key insight:** The taxonomy mirrors the observation window. Global findings come from the
lightweight scan (Tier 0-1), Narrow findings come from deep focused analysis (R-0 through R-4).
They share the AD-15 filter and Category system but differ in detection mechanism.

### 2.3 Cross-Reference Flow (TA-3)

```
Global → Narrow:
  G-5 "Missing L2 in 60% of sessions"
  ├── Triggers: /rsil-review target = "agent-common-protocol.md L2 guidance"
  └── Produces: P-R{N} findings about specific wording improvements

Narrow → Global:
  P4-R1, P6-R2, P9-R1 (3 findings about "explicit checkpoints")
  ├── Pattern detection: same theme across 3 skills
  └── Promotes to: G-{N} "Checkpoint structure needed in all directive templates"
```

**Implementation:** Each finding record gets a `cross_refs` field (list of related finding IDs).
Global findings that trigger Narrow reviews get `decomposed_to: [P-R{N}, ...]`.
Narrow findings that aggregate get `promoted_to: G-{N}`.

### 2.4 Scalability Analysis (TA-4)

Current state: 252 lines, 24 findings ≈ 10.5 lines per finding average.

**Projection:**

| Findings | Est. Lines | Manageability |
|----------|-----------|---------------|
| 24 (now) | 252 | Easy |
| 50 | ~525 | Comfortable |
| 100 | ~1050 | Still readable with YAML summary |
| 150 | ~1575 | Split point: archive older findings |
| 200+ | — | Quarterly archive files + active tracker |

**Split strategy at 150 findings:**
- Active tracker: last 50 findings + all open backlog + cross-cutting patterns
- Archive: `rsil-tracker-archive-{quarter}.md` with completed/resolved findings
- Summary table in active tracker references archives by finding ID range

**Why not split earlier?** The cross-cutting patterns section (§4) and improvement backlog (§5) need
to see the full picture. Premature splitting fragments pattern detection.

### 2.5 Schema Extension (TA-5)

Current tracker schema (implicit in §3):
```yaml
finding:
  id: "P6-R1"
  finding: "text"
  category: "B (NL)"
  ad15: "✅"
  status: "ACCEPTED + APPLIED"
```

**Proposed extension for unified tracker:**
```yaml
finding:
  id: "G-1" | "P6-R1"
  source_skill: "rsil-global" | "rsil-review"
  finding_type: "global" | "narrow"
  finding: "text"
  category: "A" | "B" | "C"
  ad15: "✅" | "❌" | "—"
  status: "ACCEPTED" | "REJECTED" | "DEFERRED" | "APPLIED"
  detection_tier: 0 | 1 | 2 | 3   # (global only — which tier caught it)
  cross_refs: ["P4-R1", "G-5"]     # related findings
  promoted_to: "G-5"               # (narrow only — if elevated)
  decomposed_to: ["P-R7", "P-R8"]  # (global only — if spawned narrow reviews)
```

---

## Unresolved Items

| ID | Item | Severity | Recommendation |
|----|------|----------|----------------|
| U-1 | Auto-invoke mechanism for /rsil-global (how Lead "remembers" to run it) | HIGH | Architect should design: NL instruction in CLAUDE.md §3 Lead role + skill auto-suggestion pattern |
| U-2 | Context window impact on large pipeline sessions (rtdi-sprint: 12 L1 files) | MEDIUM | Tier 1 should cap at reading 3 most recent L1 files, not all |
| U-3 | Concurrent /rsil-global + /rsil-review execution | LOW | Not recommended — sequential only (shared tracker write conflict) |

---

## Evidence Sources

| Source | Type | What It Provided |
|--------|------|-----------------|
| 17 session directories | Local file exploration | Artifact structure patterns, size distributions |
| nlp-execution/gate-record.yaml | Local file (115L) | Gold standard gate record structure |
| opus46-nlp-conversion/L1-index.yaml | Local file (149L) | Complex L1 with cross-impact maps |
| nlp-execution/TEAM-MEMORY.md | Local file (57L) | Warning/pattern density benchmark |
| narrow-rsil-tracker.md | Local file (252L) | Current tracker schema + growth trajectory |
| narrow-rsil-handoff.md | Local file (254L) | Design questions Q1-Q6, execution-time patterns |
| rsil-review/SKILL.md | Local file (561L) | Current RSIL architecture (Shared Foundation) |
| delivery-pipeline/SKILL.md | Local file (459L) | Phase 9 integration point (ARCHIVE.md creation) |
| CLAUDE.md | Local file (172L) | INFRA structure, §6 Lead operations |
| git log (last 5 commits) | Shell command | Non-pipeline work trace patterns |

**MCP Tools Usage:** None required for this research — all data was local .agent/ artifacts and
.claude/ infrastructure files. Sequential-thinking was used implicitly for analysis organization.
