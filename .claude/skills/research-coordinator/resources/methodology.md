# Research Coordinator — Methodology Reference (L3)

## L3 Output File Format Templates

### p2-coordinator-index.md (L1 — always read by Lead)

```yaml
domain: research
skill: coordinator
status: PASS|PARTIAL|FAIL
dimensions_received: 4
dimensions_complete: 0
compound_patterns: 0
overall_risk: HIGH|MEDIUM|LOW
critical_findings: 0
audit_summary:
  static:
    status: PASS|PARTIAL|MISSING
    hotspots: 0
    cycles: 0
  behavioral:
    status: PASS|PARTIAL|MISSING
    high_risks: 0
    conflicts: 0
  relational:
    status: PASS|PARTIAL|MISSING
    broken: 0
    integrity_pct: 100
  impact:
    status: PASS|PARTIAL|MISSING
    critical_paths: 0
    maintenance_risk: LOW
routing_recommendation: ""
cc_native_claims: 0
pt_signal: "metadata.phase_signals.p2_research"
signal_format: "PASS|dims:4|claims:{N}|ref:tasks/{work_dir}/p2-coordinator-index.md"
```

### p2-coordinator-summary.md (L2 — read by Lead when routing needs detail)

Sections (keep under 200 lines):
1. Executive summary — 3-5 sentences covering overall research health
2. Compound pattern highlights — top 3 compound patterns with brief descriptions
3. Risk distribution — HIGH/MEDIUM/LOW counts across all dimensions
4. Gap report — missing or partial audit dimensions with expected locations
5. Routing guidance — which plan-* skills need which L3 files and why
6. CC-native claims — aggregated list with types, sources, and routing recommendation

### p2-coordinator-{dim}.md (L3 — consumed by plan-phase skills via $ARGUMENTS)

**p2-coordinator-static.md** (for plan-static):
- Full dependency DAG from audit-static
- Hotspot analysis with all connected files
- Compound patterns involving static dimension
- Recommended decomposition constraints (e.g., "do not split hotspot X across tasks")

**p2-coordinator-behavioral.md** (for plan-behavioral):
- Full behavior prediction table from audit-behavioral
- Risk classification with all evidence
- Compound patterns involving behavioral dimension
- Recommended strategy constraints (e.g., "sequence task Y before Z to manage regression risk")

**p2-coordinator-relational.md** (for plan-relational):
- Full relationship graph from audit-relational
- Integrity issues with all evidence
- Compound patterns involving relational dimension
- Recommended interface constraints (e.g., "verify A->B contract before implementing C")

**p2-coordinator-impact.md** (for plan-impact and execution-impact):
- Full propagation path table from audit-impact
- Shift-Left data for execution-impact (P6)
- Compound patterns involving impact dimension
- Recommended sequencing constraints based on propagation paths

**Preservation rule**: Do NOT filter out low-severity findings in L3 files. A low-severity finding in one dimension may become high-severity when combined with another dimension in plan-phase analysis.

---

## Claim Deduplication Protocol

Process all `[CC-CLAIM]` tagged items collected from research-codebase and research-external:

1. **Scan** both research outputs for `[CC-CLAIM]` markers. Extract claim text + source dimension.
2. **Deduplicate**: Identify claims asserting the same behavioral fact. Merge into one entry; tag all source dimensions (e.g., `sources: [codebase, external]`). Keep the strongest evidence citation.
3. **Categorize** by type:
   - `FILESYSTEM` — claims about file paths, directory structure, file existence
   - `PERSISTENCE` — claims about how data survives across sessions (highest cost if wrong)
   - `STRUCTURE` — claims about code structure, module boundaries, class hierarchy
   - `CONFIG` — claims about configuration values, environment variables, defaults
   - `BEHAVIORAL` — claims about runtime behavior, API contracts, side effects
4. **Priority rank** for verification routing:
   - `PERSISTENCE` → highest priority (hardest to verify, most costly if wrong)
   - `CONFIG`/`STRUCTURE` → medium priority (file-based verification straightforward)
   - `BEHAVIORAL` → lowest priority (may require deeper investigation beyond file inspection)

Include aggregated claim list in L2 summary. Add routing recommendation: "Route to research-cc-verify before ref cache update if cc_native_claims > 0."

---

## Cross-Dimensional Pattern Discovery Heuristics

Four compound intersection types. For each pattern, document: intersecting dimensions, affected files/components, compound severity (typically higher than individual finding), evidence citations from both dimensions.

### Dependency + Behavior Intersection
**Trigger**: Hotspot files from audit-static that also appear in audit-behavioral HIGH risk list.
**Meaning**: Structurally central AND behaviorally fragile — modifications have wide propagation AND high regression risk.
**Action**: Mark as critical nodes. Escalate compound severity to CRITICAL regardless of individual ratings.

### Relationship + Impact Intersection
**Trigger**: Broken or missing relationships from audit-relational that fall on high-severity propagation paths from audit-impact.
**Meaning**: Integrity risks — the system's declared relationships are unreliable exactly where changes will propagate furthest.
**Action**: Flag for interface contract verification before any implementation work begins.

### Static + Relational Consistency
**Trigger**: Files with high fan-in (audit-static) that are missing from relationship declarations (audit-relational).
**Meaning**: Undeclared dependencies — structurally coupled but not semantically acknowledged. Will cause silent breakage.
**Action**: Recommend explicit dependency declaration before plan-relational proceeds.

### Behavioral + Impact Compound Risk
**Trigger**: Components with predicted regressions (audit-behavioral) that appear on TRANSITIVE propagation paths (audit-impact).
**Meaning**: Cascading regression risk — a behavioral change ripples through multiple hops, amplifying the blast radius.
**Action**: Flag for heightened sequencing discipline in plan-impact. Consider isolation strategies.

---

## Dimensional Conflict Resolution Algorithm

**Trigger**: Two audit dimensions produce conflicting assessments of the same component (e.g., audit-static rates file X as low-risk due to low fan-in; audit-behavioral rates file X as HIGH risk due to complex conditional logic).

**Algorithm**:
1. Extract both assessments with full evidence citations
2. Identify the conflict axis (severity disagreement, scope disagreement, or factual contradiction)
3. Document both perspectives verbatim in L2 summary section "Dimensional Conflicts"
4. Do NOT auto-resolve — conflicting evidence is itself a signal
5. Estimate conflict impact: how many total findings does this contradiction affect?
   - <10% of findings affected → note as gap, proceed
   - 10-20% affected → warn Lead in micro-signal: `PARTIAL|conflict:moderate`
   - >20% affected → L3 Restructure trigger (route to Lead for audit re-execution)
6. In L3 files for the affected dimensions: include conflict note with cross-reference to the other dimension's assessment

**Route**: Lead for disposition (may require re-running one audit with refined scope or different methodology).

---

## DPS Template for Coordinator Subagent

### COMPLEX Tier (single analyst, maxTurns: 35)

```
OBJECTIVE: Consolidate 4 audit dimension outputs into tiered coordinator output.

CONTEXT (D11 — cognitive focus):
  INCLUDE:
    - Paths to audit outputs: tasks/{work_dir}/p2-audit-static.md,
      tasks/{work_dir}/p2-audit-behavioral.md,
      tasks/{work_dir}/p2-audit-relational.md,
      tasks/{work_dir}/p2-audit-impact.md
    - Missing/partial dimension status (if any)
    - Output path prefix: tasks/{work_dir}/p2-coordinator-{file}.md
  EXCLUDE:
    - Individual claim evidence detail from audit L2 bodies
    - Historical rationale for audit findings
    - Full pipeline state beyond P2 audit results

TASK:
  Read all available audit dimension outputs. Extract key metrics and top findings
  from each. Cross-reference dimensions for compound patterns (see methodology.md for
  4 intersection types). Produce 6 files:
    1. tasks/{work_dir}/p2-coordinator-index.md (L1 compact YAML, ≤30 lines)
    2. tasks/{work_dir}/p2-coordinator-summary.md (L2, ≤200 lines)
    3. tasks/{work_dir}/p2-coordinator-static.md (L3)
    4. tasks/{work_dir}/p2-coordinator-behavioral.md (L3)
    5. tasks/{work_dir}/p2-coordinator-relational.md (L3)
    6. tasks/{work_dir}/p2-coordinator-impact.md (L3)

CONSTRAINTS:
  - Read-only consolidation (no new Grep/Glob/Bash research)
  - L1 index ≤30 YAML lines
  - L2 summary ≤200 lines
  - maxTurns: 35

DELIVERY:
  file-based handoff to Lead: "PASS|dimensions:4|patterns:{N}|ref:tasks/{work_dir}/p2-coordinator-index.md"
```

### STANDARD Tier
Same structure as COMPLEX. maxTurns: 30. Fewer compound pattern intersections expected.

### TRIVIAL Tier
Lead-direct inline consolidation. Merge ≤2 dimension summaries into single output file. No tiered output hierarchy. No analyst spawn.

### Partial Dimension Failure
If 1-2 audit dimensions are missing: proceed with available data. L1 marks missing dimensions. L3 files only created for available dimensions. Compound patterns involving missing dimensions noted as gaps in L2. If 3-4 missing: FAIL — insufficient data for meaningful consolidation.

---

## Deferred Spawn Pattern (Heavy Analysis)

**Trigger**: >3 audit files each contain >20 findings — total data volume exceeds single-analyst context budget for cross-referencing.

**Pattern**: Coordinator (spawned as subagent with `coordinator` profile) acts as Sub-Orchestrator:
1. Coordinator spawns analyst subagents (one per audit dimension file group)
2. Each analyst subagent reads its assigned audit file, extracts key metrics + top findings, returns ≤30K summary
3. Coordinator synthesizes across subagent summaries → produces tiered output
4. Coordinator sends Ch3 micro-signal to Lead

This is Teammate→Subagent delegation (NOT nested Teams, which is blocked). The coordinator profile has `Task(analyst, researcher)` tool access for this purpose.

**Constraint**: Only use when total finding count across all 4 dimensions exceeds ~80 findings. For normal loads, single analyst reads all 4 files directly — deferred spawn adds coordination overhead.
