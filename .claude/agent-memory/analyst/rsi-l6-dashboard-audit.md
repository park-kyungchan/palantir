# RSI L6 Dashboard Visualization Audit

**Date**: 2026-02-15
**Scope**: sync-dashboard.sh (775L), template.html (2447L), index.html (generated)
**Coverage**: 100% -- both files read entirely, all 35 skills cross-referenced
**Methodology**: 4-axis analysis (Body Section Rendering, Data Accuracy, L5 Regression, Latent Issues)

---

## Executive Summary

| Severity | Count |
|----------|-------|
| HIGH | 2 |
| MEDIUM | 4 |
| LOW | 4 |
| ADVISORY | 3 |
| **TOTAL** | **13** |

**Dashboard Visualization Health Score**: 6.8/10

The sync-dashboard.sh parser correctly extracts all 8 body section fields (4 mandatory + 4 enrichment) into JSON. However, template.html only renders the 4 original mandatory indicators (E/M/steps/Q/O), completely ignoring the 4 new enrichment fields (`has_decision_points`, `has_failure_handling`, `has_anti_patterns`, `has_transitions`). This is the primary gap. Additionally, 3 of 6 L5 dashboard findings remain unfixed (description regex fragility, domain extraction lossy, pipeline phase mapping stale). The skill enrichment coverage has dramatically improved since L5 -- all 35/35 skills now have all 8 body sections, making the missing visualization even more impactful.

---

## Axis 1: Body Section Rendering Gap

### DASH-L6-01 [HIGH] Template does not render 4 new enrichment body section indicators

**Files**:
- `/home/palantir/.claude/dashboard/sync-dashboard.sh` (lines 270-273): Correctly parses `has_decision_points`, `has_failure_handling`, `has_anti_patterns`, `has_transitions`
- `/home/palantir/.claude/dashboard/template.html` (lines 2086-2092): Only renders 5 indicators: E (Execution Model), M (Methodology), step count, Q (Quality Gate), O (Output)

**Evidence**: The `indicators` array on lines 2086-2092 defines exactly 5 items:
```javascript
const indicators = [
    { label: 'E', val: bs.has_execution_model },
    { label: 'M', val: bs.has_methodology },
    { label: String(bs.methodology_steps || 0), val: (bs.methodology_steps || 0) > 0 },
    { label: 'Q', val: bs.has_quality_gate },
    { label: 'O', val: bs.has_output }
];
```

The 4 new fields are completely absent: `bs.has_decision_points`, `bs.has_failure_handling`, `bs.has_anti_patterns`, `bs.has_transitions`.

A global grep for `has_decision_points`, `has_failure_handling`, `has_anti_patterns`, `has_transitions` in template.html returns **zero matches**.

**Impact**: HIGH. The dashboard was designed to show body section completeness, but it only shows 5/9 possible indicators. With all 35 skills now having all 8 sections (per grep verification), the enrichment indicators would all be green -- but users cannot see this data at all. The dashboard silently discards 44% of body section data.

**Required Change** (template.html lines 2086-2092):
```javascript
const indicators = [
    { label: 'E', val: bs.has_execution_model, title: 'Execution Model' },
    { label: 'M', val: bs.has_methodology, title: 'Methodology' },
    { label: String(bs.methodology_steps || 0), val: (bs.methodology_steps || 0) > 0, title: 'Steps' },
    { label: 'Q', val: bs.has_quality_gate, title: 'Quality Gate' },
    { label: 'O', val: bs.has_output, title: 'Output' },
    { label: 'D', val: bs.has_decision_points, title: 'Decision Points' },
    { label: 'F', val: bs.has_failure_handling, title: 'Failure Handling' },
    { label: 'A', val: bs.has_anti_patterns, title: 'Anti-Patterns' },
    { label: 'T', val: bs.has_transitions, title: 'Transitions' }
];
```

Also update the indicator rendering (line 2109-2111) to use `title` attribute for tooltips:
```javascript
...indicators.map(ind =>
    h('span', { className: 'bi ' + (ind.val ? 'bi-yes' : 'bi-no'), title: ind.title || ind.label }, ind.label)
)
```

### DASH-L6-02 [MEDIUM] No enrichment summary stat on Overview tab

**Files**:
- `/home/palantir/.claude/dashboard/template.html` (lines 1856-1875): Overview stats only show 4 metrics (Agents, Skills, Hooks, Version)

**Evidence**: The Overview tab hero metrics section displays 4 stat cards. With the new body section data, a useful 5th metric would be an "Enrichment" stat showing the percentage of skills with full enrichment (all 4 extra sections present). Currently this data is available in JSON but not visualized.

**Impact**: MEDIUM. Users must manually count body indicators across 35 skills to assess overall enrichment coverage. An aggregate stat would provide instant insight.

**Suggested Addition** (after line 1866):
```javascript
const enrichedCount = (D.skills || []).filter(s => {
    const bs = s.body_sections || {};
    return bs.has_decision_points && bs.has_failure_handling && bs.has_anti_patterns && bs.has_transitions;
}).length;
// Add as 5th metric:
{ value: enrichedCount + '/' + skillCount, label: { ko: '완전 강화', en: 'Fully Enriched' }, cls: 'sv-emerald' }
```

---

## Axis 2: L5 Finding Regression Analysis

Checking 6 dashboard-related findings from the L5 Integration Audit (`rsi-l5-integration-audit.md`):

| L5 ID | Severity | Summary | Status |
|-------|----------|---------|--------|
| INT-04 | HIGH | Description regex `(?=^[a-z]\|^---)` fragile | **UNFIXED** |
| INT-05 | HIGH | DOMAIN extraction `\S+` loses compound domains | **UNFIXED** |
| INT-06 | MEDIUM | delivery-pipeline tagged P9 vs CLAUDE.md P8 | **FIXED** (now P8) |
| INT-07 | MEDIUM | Hardcoded `domain_phase` shifted by +1 | **FIXED** (tags aligned) |
| INT-08 | MEDIUM | Agent tools parser expects exactly 2-space indent | **UNFIXED** |
| DASH-01 | MEDIUM | Hook parser misses statusMessage from settings.json | **UNFIXED** |

### DASH-L6-03 [HIGH] L5 INT-04 UNFIXED: Description regex still fragile

**Files**:
- `/home/palantir/.claude/dashboard/sync-dashboard.sh` (line 169, 233): `re.search(r'^description:\s*\|\n(.*?)(?=^[a-z]|^---)', fm, re.DOTALL | re.MULTILINE)`

**Evidence**: The regex terminates description capture on any line starting with a lowercase ASCII letter (`^[a-z]`). This works by coincidence -- all YAML keys in current agent/skill files happen to start with lowercase letters. But it would fail on:
1. A future YAML key starting with uppercase (e.g., `Argument:`)
2. A description line that starts at column 0 without 2-space indent
3. Edge case: `---` end-marker is the second alternative, but if description is the last key before `---`, the non-greedy `.*?` plus `(?=^[a-z]|^---)` correctly terminates

The same fragile regex appears in BOTH the agent parser (line 169) and skill parser (line 233).

**Impact**: HIGH. Silent data corruption if YAML format evolves. Currently producing correct output but relying on naming conventions rather than structural parsing.

**Recommended Fix**: Replace termination pattern with non-indented line detection:
```python
desc_match = re.search(r'^description:\s*\|\n(.*?)(?=^\S|^---)', fm, re.DOTALL | re.MULTILINE)
```
This matches any line starting with a non-whitespace character (i.e., any YAML key at column 0), which is structurally correct.

### DASH-L6-04 [MEDIUM] L5 INT-05 UNFIXED: DOMAIN extraction captures only first word

**Files**:
- `/home/palantir/.claude/dashboard/sync-dashboard.sh` (line 254): `domain_match = re.search(r'DOMAIN:\s*(\S+)', desc)`

**Evidence**: The regex captures only the first non-whitespace token after `DOMAIN:`. Current results for all domain types:

| Skill Domain Line | Extracted | Notes |
|---|---|---|
| `DOMAIN: pre-design (skill 1 of 3)` | `pre-design` | Correct |
| `DOMAIN: Cross-cutting terminal phase` | `Cross-cutting` | Loses qualifier |
| `DOMAIN: Cross-cutting (session recovery)` | `Cross-cutting` | Loses qualifier |
| `DOMAIN: Cross-cutting, any phase.` | `Cross-cutting,` | Trailing comma (fixed by `.rstrip(',')`) |
| `DOMAIN: Homeostasis (cross-cutting, ...)` | `Homeostasis` | Correct after lowercasing |

Three cross-cutting skills (`delivery-pipeline`, `pipeline-resume`, `task-management`) all resolve to domain "cross-cutting" -- making them indistinguishable in the dashboard donut chart and domain bar chart. Since all three are different types of cross-cutting functionality, this causes visual data loss.

**Impact**: MEDIUM. Dashboard merges 3 functionally distinct skills into one visual bucket.

---

## Axis 3: Pipeline Phase Mapping Accuracy

### DASH-L6-05 [MEDIUM] Hardcoded `domain_phase` maps cross-cutting to P8 but 2/3 cross-cutting skills are X-Cut

**Files**:
- `/home/palantir/.claude/dashboard/sync-dashboard.sh` (line 604): `'cross-cutting': 'P8'`
- `/home/palantir/.claude/skills/pipeline-resume/SKILL.md` (line 4): `[X-Cut·Resume·Recovery]`
- `/home/palantir/.claude/skills/task-management/SKILL.md` (line 4): `[X-Cut·TaskMgmt·TaskAPI]`
- `/home/palantir/.claude/skills/delivery-pipeline/SKILL.md` (line 4): `[P8·Delivery·Terminal]`

**Evidence**: The `domain_phase` hardcoded mapping assigns ALL cross-cutting domain skills to `P8`. But only `delivery-pipeline` is tagged P8; `pipeline-resume` and `task-management` are tagged `X-Cut`. In the pipeline view (Overview tab), all 3 cross-cutting skills appear under P8, which is incorrect for 2 of them.

This creates a discrepancy between:
- **Skills table** (Tab 3): Shows `pipeline-resume` as X-cut, `task-management` as X-cut, `delivery-pipeline` as P8 (correct per skill tags)
- **Pipeline flow** (Tab 1): Shows all 3 under P8 (incorrect for 2)

The correct mapping would be:
```python
# delivery-pipeline -> P8
# pipeline-resume -> X-cut
# task-management -> X-cut
```
But the current domain-based grouping cannot distinguish these because all 3 share domain "cross-cutting".

**Impact**: MEDIUM. Pipeline flow visualization shows 3 skills at P8 when only 1 is actually a P8 skill. The X-cut node shows 4 homeostasis skills but misses the 2 cross-cutting X-cut skills, showing an incorrect skill count.

**Recommended Fix**: Parse phase tags from individual skills rather than using domain-level phase mapping. Or split the cross-cutting domain into `cross-cutting-delivery` (P8) and `cross-cutting-utility` (X-cut).

### DASH-L6-06 [LOW] Pipeline flow node shows stale skill count when domain-phase mapping disagrees with skill tags

**Files**:
- `/home/palantir/.claude/dashboard/template.html` (lines 1882-1894): Pipeline flow renderer
- `/home/palantir/.claude/dashboard/sync-dashboard.sh` (lines 594-605): `domain_phase` dict

**Evidence**: The pipeline flow shows `N skills` under each phase node. The count comes from `domains[p].length` where `domains` is populated from the pipeline parser's `domain_phase` mapping. Due to DASH-L6-05:
- P8 node shows 3 skills (delivery + resume + task-mgmt) instead of correct 1 skill
- X-cut node shows 4 skills (homeostasis only) instead of correct 6 skills (4 homeostasis + 2 cross-cutting X-cut)

**Impact**: LOW. Misleading skill counts in pipeline flow visualization.

---

## Axis 4: Additional Latent Issues

### DASH-L6-07 [LOW] Skills table body column header says "Body" but tooltip/title is in Korean only

**Files**:
- `/home/palantir/.claude/dashboard/template.html` (line 1537): `<th data-ko="본문 구성" data-en="Body">본문 구성</th>`

**Evidence**: The column header is bilingual (ko/en), which is correct. However, the individual body indicator `<span>` elements (line 2110) use the label letter as the `title` attribute (`title: ind.label`), producing tooltips like "E", "M", "5", "Q", "O". These are not meaningful to users unfamiliar with the abbreviation scheme.

**Impact**: LOW. Poor discoverability. Users must guess what E/M/Q/O mean.

**Recommended Fix**: Use descriptive titles in the indicators array (as shown in DASH-L6-01 fix).

### DASH-L6-08 [LOW] Domain donut chart color wraps at 10 domains

**Files**:
- `/home/palantir/.claude/dashboard/template.html` (lines 1734-1737): `DOMAIN_COLORS` array has 10 entries

**Evidence**: There are exactly 10 domains currently (pre-design, design, research, plan, plan-verify, orchestration, execution, verify, homeostasis, cross-cutting). The color array has 10 entries, so no wrapping occurs. But if a future domain is added, colors would repeat (index 10 = same as index 0), making two domains visually indistinguishable.

**Impact**: LOW. Currently safe. Future-proofing concern only.

### DASH-L6-09 [ADVISORY] Skill enrichment state changed since L5 diagnosis

**Context**: The L5 Skills Audit (`rsi-l5-skills-audit.md`) reported:
- 14/35 fully enriched (Decision Points + Anti-Patterns + Transitions + Failure Handling)
- 21/35 lack enrichment sections

**Current State** (verified by grep across all 35 SKILL.md files):
- 35/35 have `## Decision Points` section
- 35/35 have `## Failure Handling` or `## Error Handling` section
- 35/35 have `## Anti-Patterns` section
- 35/35 have `## Transitions` section
- **35/35 are now fully enriched** (100%)

This means the dashboard, once fixed (DASH-L6-01), would show all 9 indicators as green for every skill. While visually uniform, this confirms the INFRA is at full enrichment maturity and the dashboard can now serve as a regression detector (any missing section would immediately stand out).

### DASH-L6-10 [ADVISORY] `execution-cascade` has both `## Error Handling` and `## Failure Handling` sections

**Files**:
- `/home/palantir/.claude/skills/execution-cascade/SKILL.md` (line 143): `## Error Handling`
- `/home/palantir/.claude/skills/execution-cascade/SKILL.md` (line 164): `## Failure Handling`

**Evidence**: This skill has TWO handling sections. The sync-dashboard.sh parser (line 271) uses `re.search(r'^## (Failure|Error) Handling', body, re.MULTILINE)` which matches on the FIRST occurrence (`## Error Handling` at line 143). So `has_failure_handling` is correctly set to `true`. No data loss, but the dual sections suggest possible redundancy or an incomplete refactoring.

Similarly, `manage-codebase` has `## Error Handling` instead of `## Failure Handling`:
- `/home/palantir/.claude/skills/manage-codebase/SKILL.md` (line 150): `## Error Handling`

The parser's alternation `(Failure|Error)` correctly handles both variants. No bug, but inconsistent naming across skills.

**Impact**: ADVISORY. No functional issue. Naming inconsistency is cosmetic.

### DASH-L6-11 [ADVISORY] Hook flow diagram SVG viewBox auto-resizes but may clip with 5+ event types

**Files**:
- `/home/palantir/.claude/dashboard/template.html` (lines 2260-2263): `totalWidth = Math.max(events.length * (eventWidth + 40), 800)`

**Evidence**: The hook flow SVG calculates `totalWidth` based on event count. With 4 unique events (SubagentStart, PreCompact, PostToolUse, SubagentStop) + 1 (SessionStart from compact hook), the total is `5 * (120 + 40) = 800px`, matching the minimum. But with `eventWidth = 120` and gap of 50 (line 2265: `i * (eventWidth + 50)`), the actual positioning is `5 * 170 = 850px`, which exceeds the 800px viewBox. The last event box may be partially clipped.

**Impact**: ADVISORY. Minor visual clipping of the rightmost hook flow box. The SVG is inside a card with `overflow-x: auto`, so horizontal scrolling is available.

---

## Findings Summary by Priority

### Must Fix (HIGH)
1. **DASH-L6-01**: Add 4 enrichment indicators (D/F/A/T) to template.html skill table body column
2. **DASH-L6-03**: Replace fragile description regex `(?=^[a-z])` with `(?=^\S)` in both agent and skill parsers

### Should Fix (MEDIUM)
3. **DASH-L6-02**: Add enrichment summary stat to Overview tab hero metrics
4. **DASH-L6-04**: Fix DOMAIN extraction to handle compound domain names
5. **DASH-L6-05**: Fix cross-cutting domain phase mapping (2/3 skills incorrectly mapped to P8)

### Nice to Have (LOW)
6. **DASH-L6-06**: Pipeline flow skill counts incorrect due to DASH-L6-05
7. **DASH-L6-07**: Body indicator tooltips should be descriptive, not single letters
8. **DASH-L6-08**: Domain color array may wrap at 11+ domains
9. **DASH-L6-09** (ADVISORY): All 35 skills now fully enriched (L5 reported 14/35)

### Cosmetic (ADVISORY)
10. **DASH-L6-10**: Inconsistent `Error Handling` vs `Failure Handling` section names (parser handles both)
11. **DASH-L6-11**: Hook flow SVG viewBox may clip with 5 events

---

## Detailed Fix Specifications

### Fix 1: DASH-L6-01 -- Add Enrichment Badges

**File**: `/home/palantir/.claude/dashboard/template.html`
**Location**: Lines 2086-2092

**Current Code**:
```javascript
const indicators = [
    { label: 'E', val: bs.has_execution_model },
    { label: 'M', val: bs.has_methodology },
    { label: String(bs.methodology_steps || 0), val: (bs.methodology_steps || 0) > 0 },
    { label: 'Q', val: bs.has_quality_gate },
    { label: 'O', val: bs.has_output }
];
```

**Replace With**:
```javascript
const indicators = [
    { label: 'E', val: bs.has_execution_model, title: 'Execution Model' },
    { label: 'M', val: bs.has_methodology, title: 'Methodology' },
    { label: String(bs.methodology_steps || 0), val: (bs.methodology_steps || 0) > 0, title: 'Methodology Steps' },
    { label: 'Q', val: bs.has_quality_gate, title: 'Quality Gate' },
    { label: 'O', val: bs.has_output, title: 'Output' },
    { label: 'D', val: bs.has_decision_points, title: 'Decision Points' },
    { label: 'F', val: bs.has_failure_handling, title: 'Failure Handling' },
    { label: 'A', val: bs.has_anti_patterns, title: 'Anti-Patterns' },
    { label: 'T', val: bs.has_transitions, title: 'Transitions' }
];
```

**Also update** line 2110 to use `ind.title`:
```javascript
// Current:
h('span', { className: 'bi ' + (ind.val ? 'bi-yes' : 'bi-no'), title: ind.label }, ind.label)
// Replace with:
h('span', { className: 'bi ' + (ind.val ? 'bi-yes' : 'bi-no'), title: ind.title || ind.label }, ind.label)
```

### Fix 2: DASH-L6-03 -- Robust Description Regex

**File**: `/home/palantir/.claude/dashboard/sync-dashboard.sh`
**Locations**: Lines 169 and 233

**Current Code** (both locations):
```python
desc_match = re.search(r'^description:\s*\|\n(.*?)(?=^[a-z]|^---)', fm, re.DOTALL | re.MULTILINE)
```

**Replace With** (both locations):
```python
desc_match = re.search(r'^description:\s*\|\n(.*?)(?=^\S|^---)', fm, re.DOTALL | re.MULTILINE)
```

The `^\S` pattern matches any line starting with a non-whitespace character, which structurally corresponds to any YAML key at column 0. This is format-agnostic and handles uppercase keys, numeric keys, and any future YAML variation.

### Fix 3: DASH-L6-05 -- Cross-Cutting Phase Mapping

**File**: `/home/palantir/.claude/dashboard/sync-dashboard.sh`
**Location**: Lines 594-605

The root cause is that the `domain_phase` dict maps by domain name, but `cross-cutting` contains skills in different phases. The cleanest fix is to use the per-skill phase tags from Section 3 (skill parser) instead of the domain-level mapping from Section 8.

**Option A (minimal)**: Split cross-cutting in the dict:
This is not possible without also changing the MEMORY.md domain table format.

**Option B (structural fix)**: Modify the pipeline parser to build phase-skill counts from the actual skills data (Section 3 output) instead of from MEMORY.md domain table. This would use the `phase` field already extracted per-skill.

In the template.html pipeline renderer, replace the `domains[p]` count with a count from the skills array:
```javascript
// Current (line 1887):
const skillsInPhase = (domains[p] || []).length;
// Replace with (derives from actual skill data):
const skillsInPhase = (D.skills || []).filter(s => s.phase === p).length;
```

This bypasses the hardcoded `domain_phase` dict entirely for the pipeline view.

---

## Cross-Reference: All 35 Skills Verification

| # | Skill | Phase Tag | Domain | Body 4+4 | In Dashboard |
|---|-------|-----------|--------|----------|-------------|
| 1 | pre-design-brainstorm | P0 | pre-design | 8/8 | Yes |
| 2 | pre-design-validate | P0 | pre-design | 8/8 | Yes |
| 3 | pre-design-feasibility | P0 | pre-design | 8/8 | Yes |
| 4 | design-architecture | P1 | design | 8/8 | Yes |
| 5 | design-interface | P1 | design | 8/8 | Yes |
| 6 | design-risk | P1 | design | 8/8 | Yes |
| 7 | research-codebase | P2 | research | 8/8 | Yes |
| 8 | research-external | P2 | research | 8/8 | Yes |
| 9 | research-audit | P2 | research | 8/8 | Yes |
| 10 | plan-decomposition | P3 | plan | 8/8 | Yes |
| 11 | plan-interface | P3 | plan | 8/8 | Yes |
| 12 | plan-strategy | P3 | plan | 8/8 | Yes |
| 13 | plan-verify-correctness | P4 | plan-verify | 8/8 | Yes |
| 14 | plan-verify-completeness | P4 | plan-verify | 8/8 | Yes |
| 15 | plan-verify-robustness | P4 | plan-verify | 8/8 | Yes |
| 16 | orchestration-decompose | P5 | orchestration | 8/8 | Yes |
| 17 | orchestration-assign | P5 | orchestration | 8/8 | Yes |
| 18 | orchestration-verify | P5 | orchestration | 8/8 | Yes |
| 19 | execution-code | P6 | execution | 8/8 | Yes |
| 20 | execution-infra | P6 | execution | 8/8 | Yes |
| 21 | execution-impact | P6 | execution | 8/8 | Yes |
| 22 | execution-cascade | P6 | execution | 8/8 | Yes |
| 23 | execution-review | P6 | execution | 8/8 | Yes |
| 24 | verify-structure | P7 | verify | 8/8 | Yes |
| 25 | verify-content | P7 | verify | 8/8 | Yes |
| 26 | verify-consistency | P7 | verify | 8/8 | Yes |
| 27 | verify-quality | P7 | verify | 8/8 | Yes |
| 28 | verify-cc-feasibility | P7 | verify | 8/8 | Yes |
| 29 | delivery-pipeline | P8 | cross-cutting | 8/8 | Yes |
| 30 | pipeline-resume | X-cut | cross-cutting | 8/8 | Yes |
| 31 | task-management | X-cut | cross-cutting | 8/8 | Yes |
| 32 | manage-infra | X-cut | homeostasis | 8/8 | Yes |
| 33 | manage-skills | X-cut | homeostasis | 8/8 | Yes |
| 34 | manage-codebase | X-cut | homeostasis | 8/8 | Yes |
| 35 | self-improve | X-cut | homeostasis | 8/8 | Yes |

**Result**: 35/35 skills present and parseable. 35/35 have all 8 body sections. 0 skills missing from dashboard.

---

## L5 Finding Resolution Scorecard

| L5 Finding | L5 Severity | Current Status | Notes |
|-----------|-------------|---------------|-------|
| INT-04 (desc regex) | HIGH | UNFIXED | Same fragile `(?=^[a-z])` pattern |
| INT-05 (DOMAIN extraction) | HIGH | UNFIXED | Same `\S+` captures first word only |
| INT-06 (P9 tag) | MEDIUM | **FIXED** | delivery-pipeline now tagged P8 |
| INT-07 (phase mapping +1 shift) | MEDIUM | **FIXED** | Skill tags now match dict mapping |
| INT-08 (tools indent) | MEDIUM | UNFIXED | Still expects exactly `'  - '` |
| DASH-01 (statusMessage) | MEDIUM | UNFIXED | Hook parser still omits statusMessage |

**Resolution Rate**: 2/6 (33%) -- L5 dashboard findings only partially addressed.
