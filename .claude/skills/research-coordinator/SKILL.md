---
name: research-coordinator
description: >-
  Consolidates four audit dimensions into tiered output with
  cross-dimensional pattern analysis. Aggregates CC-native behavioral
  claims from research dimensions and flags for verification routing.
  Terminal research skill that merges parallel audit results into
  unified intelligence. Use after all four audit skills complete
  (audit-static, audit-behavioral, audit-relational, audit-impact).
  Reads from audit-static dependency graph, audit-behavioral behavior
  predictions, audit-relational relationship graph, and audit-impact
  propagation paths. Produces L1 index and L2 summary for Lead,
  L3 per-dimension files for plan skills, plus CC-native claim
  aggregation for research-cc-verify.
user-invocable: false
disable-model-invocation: false
allowed-tools: "Read Glob Grep Write"
metadata:
  category: research
  tags: [audit-consolidation, cross-dimensional-analysis, pattern-synthesis]
  version: 2.0.0
---

# Research — Coordinator (Cross-Audit Consolidation)

## Execution Model
- **TRIVIAL**: Lead-direct. Inline consolidation of minimal audit outputs (≤2 dimensions with ≤5 findings each). No agent spawn. maxTurns: 0.
- **STANDARD**: Spawn analyst (maxTurns:30). Read all 4 audit outputs, cross-reference, produce tiered output.
- **COMPLEX**: Spawn analyst (maxTurns:35). Larger audit outputs require more turns for cross-referencing. Single analyst to maintain cross-dimensional coherence.

Note: Always single analyst regardless of tier. Cross-dimensional pattern discovery requires one agent seeing all four dimensions simultaneously. Splitting across agents loses the consolidation benefit.

## Phase-Aware Execution
- **P2+ (active Team)**: Spawn agent with `team_name` parameter. Agent delivers via SendMessage.
- **Delivery**: Agent writes results to `/tmp/pipeline/p2-coordinator/` directory (6 files), sends micro-signal: `PASS|dimensions:4|patterns:{N}|ref:/tmp/pipeline/p2-coordinator/index.md`.

## Tiered Output Architecture
The coordinator produces three tiers of output with different consumers:

| Tier | File | Consumer | When Read |
|------|------|----------|-----------|
| L1 | `index.md` | Lead | Always (routing decisions) |
| L2 | `summary.md` | Lead | When routing needs detail |
| L3 | `audit-static.md` | plan-decomposition | Via $ARGUMENTS, Lead never reads |
| L3 | `audit-behavioral.md` | plan-strategy | Via $ARGUMENTS, Lead never reads |
| L3 | `audit-relational.md` | plan-interface | Via $ARGUMENTS, Lead never reads |
| L3 | `audit-impact.md` | plan-strategy, execution-impact | Via $ARGUMENTS, Lead never reads |

This tiered design prevents Lead context bloat: Lead only reads L1 (compact index) and L2 (summary) while plan-phase skills receive detailed L3 data directly via `$ARGUMENTS` injection.

## Decision Points

### Consolidation Depth
Based on audit dimension count and total findings.
- **≤2 dimensions, ≤5 findings each**: Lead-direct inline consolidation (TRIVIAL). No agent spawn.
- **3-4 dimensions, ≤20 total findings**: Single analyst, standard cross-reference. maxTurns: 30.
- **4 dimensions, >20 total findings**: Single analyst, extended cross-reference. maxTurns: 35.
- **Default**: Single analyst, maxTurns: 30 (STANDARD tier).

### Partial Dimension Handling
- **1-2 dimensions missing**: Proceed with available data. Mark gaps in L1 index. Compound patterns limited.
- **3-4 dimensions missing**: FAIL. Insufficient data for meaningful consolidation. Route to Lead.

## Methodology

### 1. Read All Audit Outputs
Read the 4 audit output files from `/tmp/pipeline/`:
- `p2-audit-static.md` -- dependency graph, hotspots, cycles
- `p2-audit-behavioral.md` -- behavior predictions, risk classifications
- `p2-audit-relational.md` -- relationship graph, integrity issues
- `p2-audit-impact.md` -- propagation paths, maintenance/scalability risk

For each audit, extract:
- Key metrics (counts, percentages, risk levels)
- Primary findings (top findings by severity)
- Coverage status (complete, partial, empty)

If any audit output is missing or marked partial, note it as a gap. Do not block on partial inputs -- consolidate what is available.

### 2. Cross-Reference Dimensions
Discover compound patterns that individual audits cannot detect:

**Dependency + Behavior Intersection**:
- Hotspot files (audit-static) that also have HIGH behavioral risk (audit-behavioral)
- These are critical nodes: structurally central AND behaviorally fragile

**Relationship + Impact Intersection**:
- Broken relationships (audit-relational) along high-severity propagation paths (audit-impact)
- These are integrity risks: the system's declared relationships are unreliable exactly where changes will propagate

**Static + Relational Consistency**:
- Files with high fan-in (audit-static) but missing from relationship declarations (audit-relational)
- These are undeclared dependencies: structurally coupled but not semantically acknowledged

**Behavioral + Impact Compound Risk**:
- Components with predicted regressions (audit-behavioral) on TRANSITIVE propagation paths (audit-impact)
- These are cascading regression risks: a behavioral change that ripples through multiple hops

For each compound pattern, document:
- Which dimensions intersect and how
- Which files/components are involved
- Compound severity (typically higher than either individual finding)
- Evidence from both dimensions (file:line references)

### 2.5. Aggregate CC-Native Claims

Collect all `[CC-CLAIM]` tagged items from research-codebase and research-external outputs:

1. **Scan** both research outputs for `[CC-CLAIM]` markers
2. **Deduplicate** claims that appear in both sources (same behavioral assertion, different evidence)
3. **Categorize** by type: FILESYSTEM, PERSISTENCE, STRUCTURE, CONFIG, BEHAVIORAL
4. **Priority rank** by verification importance:
   - PERSISTENCE claims → highest priority (hardest to verify, most costly if wrong)
   - CONFIG/STRUCTURE → medium priority (file-based verification straightforward)
   - BEHAVIORAL → lowest priority (may require deeper investigation beyond file inspection)

Include aggregated claims in L2 summary with routing recommendation: "Route to research-cc-verify before ref cache update if cc_native_claims > 0."

### 3. Produce L1 Index
The L1 index is what Lead always reads. Keep it compact and routing-focused.

Content:
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
  static: {status, hotspots, cycles}
  behavioral: {status, high_risks, conflicts}
  relational: {status, broken, integrity_pct}
  impact: {status, critical_paths, maintenance_risk}
routing_recommendation: ""
```

The `routing_recommendation` field tells Lead which plan-phase skills need special attention based on findings.

### 4. Produce L2 Summary
The L2 summary is what Lead reads when routing decisions need more context than L1 provides.

Content:
- Executive summary: 3-5 sentences covering overall research health
- Compound pattern highlights: top 3 compound patterns with brief descriptions
- Risk distribution: how many HIGH/MEDIUM/LOW findings across all dimensions
- Gap report: any missing or partial audit dimensions
- Routing guidance: which plan-* skills need which L3 files and why

Keep L2 under 200 lines. It should inform Lead's routing, not replace L3 detail.

### 5. Produce L3 Per-Dimension Files
Four L3 files, each containing the full detail for one audit dimension plus relevant compound patterns:

**`audit-static.md`** (for plan-decomposition):
- Full dependency DAG from audit-static
- Hotspot analysis with all connected files
- Compound patterns involving static dimension
- Recommended decomposition constraints (e.g., "do not split hotspot X across tasks")

**`audit-behavioral.md`** (for plan-strategy):
- Full behavior prediction table from audit-behavioral
- Risk classification with all evidence
- Compound patterns involving behavioral dimension
- Recommended strategy constraints (e.g., "sequence task Y before Z to manage regression risk")

**`audit-relational.md`** (for plan-interface):
- Full relationship graph from audit-relational
- Integrity issues with all evidence
- Compound patterns involving relational dimension
- Recommended interface constraints (e.g., "verify A->B contract before implementing C")

**`audit-impact.md`** (for plan-strategy + execution-impact):
- Full propagation path table from audit-impact
- Shift-Left data for execution-impact (P6)
- Compound patterns involving impact dimension
- Recommended sequencing constraints based on propagation paths

### Delegation Prompt Specification (Coordinator Pattern)

#### COMPLEX Tier (single analyst, extended turns)
- **Context**: Provide paths to all 4 audit outputs: `/tmp/pipeline/p2-audit-static.md`, `p2-audit-behavioral.md`, `p2-audit-relational.md`, `p2-audit-impact.md`. Note any missing/partial dimensions.
- **Task**: "Read all available audit dimension outputs. Extract key metrics and top findings from each. Cross-reference dimensions for compound patterns (dependency+behavior, relationship+impact, static+relational, behavioral+impact intersections). Produce 6 files in `/tmp/pipeline/p2-coordinator/`: L1 index.md (compact YAML routing), L2 summary.md (<200 lines, executive overview + routing guidance), 4x L3 per-dimension files with full data + compound patterns."
- **Constraints**: Read-only consolidation (analyst agent, no Bash). No new Grep/Glob research. L1 index ≤30 YAML lines. L2 ≤200 lines. maxTurns: 35.
- **Expected Output**: 6 files in `/tmp/pipeline/p2-coordinator/`. L1: status, dimensions, compound patterns, overall risk, routing recommendation. L2: executive summary, highlights, risk distribution, gap report. L3: complete per-dimension data with cross-referenced compound patterns.
- **Delivery**: SendMessage to Lead: `PASS|dimensions:4|patterns:{N}|ref:/tmp/pipeline/p2-coordinator/index.md`

#### STANDARD Tier (single analyst, standard turns)
Same structure as COMPLEX. maxTurns: 30. Fewer compound pattern intersections expected.

#### TRIVIAL Tier
Lead-direct inline consolidation. Merge ≤2 dimension summaries into single output file. No tiered output hierarchy.

#### Partial Dimension Failure
If 1-2 audit dimensions are missing: proceed with available data. L1 marks missing dimensions. L3 files only created for available dimensions. Compound patterns involving missing dimensions noted as gaps in L2.

## Failure Handling

### Missing Audit Outputs
- **1-2 audits missing**: Proceed with available dimensions. Mark missing dimensions in L1. Compound patterns involving missing dimensions are not discoverable -- note this as a gap.
- **3-4 audits missing**: FAIL. Insufficient data for meaningful consolidation. Route to Lead for audit re-execution.
- **Route**: Lead with list of missing audits and their expected output locations

### Contradictory Cross-Dimensional Findings
- **Cause**: Two audit dimensions produce conflicting assessments of the same component
- **Action**: Document both perspectives in L2 with evidence from each dimension. Do not auto-resolve.
- **Route**: Lead for disposition (may require re-running one audit with refined scope)

### Output Directory Not Writable
- **Cause**: `/tmp/pipeline/p2-coordinator/` cannot be created
- **Action**: FAIL with filesystem error details
- **Route**: Lead for infrastructure resolution

## Anti-Patterns

### DO NOT: Filter Out Low-Severity Findings in L3
L3 files should contain complete dimension data. Low-severity findings in one dimension may become high-severity when combined with findings from another dimension in plan-phase analysis. Preserve all data.

### DO NOT: Add New Research in Coordinator
Coordinator consolidates existing audit findings. If a gap is discovered during consolidation, note it as a gap recommendation in L2. Do not perform new Grep/Glob/Read analysis to fill the gap.

### DO NOT: Bloat L1 Index
L1 index must stay compact for Lead context budget. Move any detail beyond summary metrics and routing recommendation to L2 or L3. If L1 exceeds 30 lines of YAML, it is too large.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| audit-static | Dependency graph, hotspots, cycles | L2 markdown at `/tmp/pipeline/p2-audit-static.md` |
| audit-behavioral | Behavior predictions, risk classification | L2 markdown at `/tmp/pipeline/p2-audit-behavioral.md` |
| audit-relational | Relationship graph, integrity issues | L2 markdown at `/tmp/pipeline/p2-audit-relational.md` |
| audit-impact | Propagation paths, risk assessment | L2 markdown at `/tmp/pipeline/p2-audit-impact.md` |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| Lead | L1 index.md + L2 summary.md | Always (terminal P2 skill) |
| plan-decomposition | L3 audit-static.md | Via $ARGUMENTS (Lead passes path) |
| plan-strategy | L3 audit-behavioral.md + audit-impact.md | Via $ARGUMENTS (Lead passes paths) |
| plan-interface | L3 audit-relational.md | Via $ARGUMENTS (Lead passes path) |
| execution-impact | L3 audit-impact.md (Shift-Left data) | Via $ARGUMENTS in plan phase |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| 3-4 audits missing | Lead | Missing audit list, expected locations |
| Cross-dimensional contradiction | Lead | Both findings with dimension sources |
| Output directory error | Lead | Filesystem error details |

## Quality Gate
- All available audit dimensions ingested and represented in output
- Compound patterns documented with evidence from both contributing dimensions
- L1 index compact (<30 lines YAML) with routing recommendation
- L2 summary under 200 lines with executive overview and routing guidance
- L3 files contain complete per-dimension data plus relevant compound patterns
- Missing dimensions explicitly noted in L1 and L2
- No new research performed (consolidation only)
- CC-native behavioral claims from research dimensions aggregated and flagged for verification
- All 6 output files written to `/tmp/pipeline/p2-coordinator/`

## Output

### L1 (index.md)
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
```

### L2 (summary.md)
- Executive summary (3-5 sentences)
- Compound pattern highlights (top 3)
- Risk distribution across all dimensions
- Gap report for missing/partial dimensions
- Routing guidance for plan-phase skills
- CC-native claims aggregated from research dimensions (for research-cc-verify routing)

### L3 (4 per-dimension files)
- Complete audit data per dimension
- Relevant compound patterns cross-referenced
- Constraint recommendations for consuming plan-phase skill
- Shift-Left handoff data (audit-impact.md only)
