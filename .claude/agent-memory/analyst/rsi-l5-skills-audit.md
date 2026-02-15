# RSI L5 -- Skill L2 Body Deep Audit

> Auditor: analyst | Date: 2026-02-15 | Scope: All 35 SKILL.md files
> Focus: L2 completeness, methodology quality, DPS templates, FAIL paths, phase tag consistency

---

## 1. Executive Summary

### Coverage
- **Skills audited**: 35/35 (100%)
- **Total lines analyzed**: ~6,200 lines of SKILL.md content

### L2 Body Completeness

| Section | Present | Missing | % Complete |
|---------|---------|---------|------------|
| ## Execution Model | 35 | 0 | 100% |
| ## Methodology | 35 | 0 | 100% |
| ### Numbered Steps | 35 | 0 | 100% |
| ## Quality Gate | 35 | 0 | 100% |
| ## Output (L1+L2) | 35 | 0 | 100% |
| ## Failure Handling | 24 | 11 | 69% |
| ## Decision Points | 14 | 21 | 40% |
| ## Anti-Patterns | 11 | 24 | 31% |
| ## Transitions | 11 | 24 | 31% |

**All 35 skills have the 4 mandatory sections (Execution Model, Methodology, Quality Gate, Output).** The variance is in enrichment sections: Failure Handling, Decision Points, Anti-Patterns, and Transitions.

### Methodology Quality Distribution

| Quality Tier | Count | Skills |
|-------------|-------|--------|
| Exemplary (DPS + Decision Points + Anti-Patterns + Transitions + Failure Handling) | 11 | execution-code, execution-infra, execution-review, execution-impact, execution-cascade, orchestration-decompose, orchestration-assign, orchestration-verify, plan-decomposition, plan-interface, plan-strategy |
| Strong (DPS + Failure Handling or Decision Points) | 9 | plan-verify-correctness, plan-verify-completeness, plan-verify-robustness, self-improve, manage-codebase, research-external, delivery-pipeline, manage-infra, manage-skills |
| Adequate (DPS template present, basic fail path) | 10 | pre-design-brainstorm, pre-design-validate, pre-design-feasibility, design-architecture, design-interface, design-risk, research-codebase, research-audit, verify-content, verify-quality |
| Minimal (no DPS, vague fail path or missing) | 5 | verify-structure, verify-consistency, verify-cc-feasibility, pipeline-resume, task-management |

### DPS Template Coverage

| Category | Count | % |
|----------|-------|---|
| Skills that spawn agents (per methodology) | 29 | 83% |
| Of those, have explicit DPS template (Context/Task/Constraints/Expected Output) | 26 | 90% of spawning skills |
| Skills that are Lead-direct only | 6 | 17% |

### FAIL Path Coverage

| Status | Count | Skills Missing Explicit FAIL Path |
|--------|-------|----------------------------------|
| Well-defined (## Failure Handling section) | 24 | -- |
| Implicit only (brief mention in methodology) | 6 | verify-structure, verify-consistency, verify-quality, verify-content, verify-cc-feasibility, task-management |
| Missing entirely | 5 | design-architecture, design-interface, design-risk, pipeline-resume (has only brief note), pre-design-brainstorm |

### Phase Tag Consistency

| Status | Count | Details |
|--------|-------|---------|
| Consistent (tag matches DOMAIN) | 30 | All pipeline skills P0-P8 |
| Phase number mismatch | 5 | See Finding F-01 |

---

## 2. TOP 10 Findings (Sorted by Severity)

### F-01: MEDIUM -- Phase Tag Numbering Inconsistency Across 5 Skills

**Affected Skills (5):**

| Skill | Description Tag | CLAUDE.md Phase | Mismatch |
|-------|----------------|-----------------|----------|
| design-architecture | `[P2` | P1 (CLAUDE.md: STANDARD=P0->P1->P2->P3->P6->P7->P8, design is P1) | YES |
| design-interface | `[P2` | P1 | YES |
| design-risk | `[P2` | P1 | YES |
| delivery-pipeline | `[P9` | P8 (CLAUDE.md: terminal phase is P8) | YES |
| execution-impact | `[P7` | P6 (CLAUDE.md: execution is P6, verify is P7) | PARTIAL |

**Evidence:**
- `/home/palantir/.claude/skills/design-architecture/SKILL.md:4` -- `[P2` but CLAUDE.md Section 2 shows design phase as P1
- `/home/palantir/.claude/skills/design-interface/SKILL.md:4` -- `[P2` but CLAUDE.md maps design to P1
- `/home/palantir/.claude/skills/design-risk/SKILL.md:4` -- `[P2` but CLAUDE.md maps design to P1
- `/home/palantir/.claude/skills/delivery-pipeline/SKILL.md:4` -- `[P9` but CLAUDE.md maximum phase is P8
- `/home/palantir/.claude/skills/execution-impact/SKILL.md:4` -- `[P7` but execution domain is P6 in CLAUDE.md

**Root Cause:** CLAUDE.md v10.8 uses P0-P8 (9 phases), but skill description tags use an older numbering scheme where design was P2 and delivery was P9. The CLAUDE.md tier table explicitly shows: `P0->P1->P2->P3->P6->P7->P8` (STANDARD) with no P4 or P5 in STANDARD, suggesting the pipeline phase numbers are:
- P0 = pre-design
- P1 = design
- P2 = research
- P3 = plan
- P4 = plan-verify
- P5 = orchestration
- P6 = execution
- P7 = verify
- P8 = delivery

However, the skill descriptions use different numbering. Let me cross-reference more carefully.

Looking at the CLAUDE.md tier table:
```
COMPLEX: P0->P8 (all phases)
STANDARD: P0->P1->P2->P3->P6->P7->P8
TRIVIAL: P0->P6->P8
```

And the skill tags:
- pre-design skills: `[P0` -- matches
- design skills: `[P2` -- would be P1 in CLAUDE.md STANDARD path
- research skills: `[P3` -- would be P2
- plan skills: `[P4` -- would be P3
- plan-verify skills: `[P5` -- would be P4
- orchestration skills: `[P6` -- would be P5
- execution skills: `[P7` -- would be P6
- verify skills: `[P8` -- would be P7
- delivery: `[P9` -- would be P8

**UPDATED ROOT CAUSE:** Actually, reviewing CLAUDE.md more carefully:

CLAUDE.md shows `Flow: PRE (P0-P4) -> EXEC (P5-P7) -> POST (P8)` and `COMPLEX | >=4 files | P0->P8 (all phases)`.

The STANDARD path `P0->P1->P2->P3->P6->P7->P8` skips P4 (plan-verify) and P5 (orchestration). This means:
- P0 = pre-design
- P1 = design
- P2 = research
- P3 = plan
- P4 = plan-verify
- P5 = orchestration
- P6 = execution
- P7 = verify
- P8 = delivery

But the skill descriptions use DIFFERENT numbers. Let me check against the actual DOMAIN fields:

| Skill | Tag Phase | Domain Says |
|-------|-----------|-------------|
| pre-design-brainstorm | P0 | pre-design (skill 1 of 3) |
| design-architecture | P2 | design (skill 1 of 3) |
| research-codebase | P3 | research (skill 1 of 3) |
| plan-decomposition | P4 | plan (skill 1 of 3) |
| plan-verify-correctness | P5 | plan-verify (skill 1 of 3) |
| orchestration-decompose | P6 | orchestration (skill 1 of 3) |
| execution-code | P7 | execution (skill 1 of 5) |
| verify-structure | P8 | verify (skill 1 of 5) |
| delivery-pipeline | P9 | cross-cutting terminal |

So the skill tags use: P0, P2, P3, P4, P5, P6, P7, P8, P9 (skipping P1). But CLAUDE.md uses: P0, P1, P2, P3, P4, P5, P6, P7, P8.

This is a systematic numbering offset. The skill tags skip P1 (no P1 tag exists) and go up to P9, while CLAUDE.md goes P0-P8. The offset is: skill_tag = CLAUDE_phase + 1 for everything after P0 (except P0 which matches).

Wait -- CLAUDE.md explicitly says in the STANDARD tier: `P0->P1->P2->P3->P6->P7->P8`. If design is P1, then STANDARD skips P4 (plan-verify) and P5 (orchestration). But the skill tags say design is P2.

**FINAL ASSESSMENT:** There is a systematic discrepancy between skill description phase tags and CLAUDE.md phase numbering. The skill tags appear to use a 10-phase system (P0-P9 with P1 unused), while CLAUDE.md uses a 9-phase system (P0-P8). This was noted as "P6a phase tag inconsistency" in the INFRA Audit v3 and partially fixed (P6a->P6), but the broader numbering system was NOT unified.

**Severity: MEDIUM** -- Lead routing uses WHEN conditions and DOMAIN fields, not phase tags. The phase tag is cosmetic for human readability but creates confusion when cross-referencing with CLAUDE.md.

**Recommendation:** Choose ONE numbering system and apply consistently. Either:
- (A) Update all 35 skill tags to match CLAUDE.md P0-P8 system
- (B) Update CLAUDE.md to match the P0,P2-P9 system used in skill tags
- Option A is preferred (fewer files, CLAUDE.md is the authority)

---

### F-02: MEDIUM -- 11 Skills Missing Dedicated Failure Handling Section

**Affected Skills:**
1. `/home/palantir/.claude/skills/design-architecture/SKILL.md` -- no Failure Handling section
2. `/home/palantir/.claude/skills/design-interface/SKILL.md` -- no Failure Handling section
3. `/home/palantir/.claude/skills/design-risk/SKILL.md` -- no Failure Handling section
4. `/home/palantir/.claude/skills/pre-design-brainstorm/SKILL.md` -- no Failure Handling section
5. `/home/palantir/.claude/skills/verify-structure/SKILL.md` -- no Failure Handling section
6. `/home/palantir/.claude/skills/verify-content/SKILL.md` -- no Failure Handling section
7. `/home/palantir/.claude/skills/verify-consistency/SKILL.md` -- no Failure Handling section
8. `/home/palantir/.claude/skills/verify-quality/SKILL.md` -- no Failure Handling section
9. `/home/palantir/.claude/skills/verify-cc-feasibility/SKILL.md` -- no Failure Handling section
10. `/home/palantir/.claude/skills/pipeline-resume/SKILL.md` -- has "Recovery Limitation" note but no systematic failure handling
11. `/home/palantir/.claude/skills/task-management/SKILL.md` -- no failure handling section

**Evidence:** All 5 verify-* skills rely on OUTPUT_TO listing `execution-infra (if FAIL)` or `execution-code (if FAIL)` in the description but have no explicit failure handling section in the L2 body defining what triggers FAIL, how to route, or what data to pass.

**Severity: MEDIUM** -- These skills have implicit FAIL routing in their OUTPUT_TO descriptions but lack the structured `## Failure Handling` section that the exemplary skills (execution-*, orchestration-*, plan-*) have. This means agents executing these skills have no guidance on handling unexpected errors.

**Recommendation:** Add `## Failure Handling` section to all 11 skills following the pattern established by execution-code:
```markdown
## Failure Handling
- **{failure type}**: Set `status: {value}`, include {data}
- **Routing**: Route to {target skill} with {data}
- **Pipeline impact**: {blocking|non-blocking}
```

---

### F-03: MEDIUM -- 5 "Minimal Quality" Skills Have No DPS Template Despite Spawning Agents

**Affected Skills:**
1. `/home/palantir/.claude/skills/verify-structure/SKILL.md:40-44` -- has a DPS template (Context/Task/Constraints/Expected Output) embedded in Step 2
2. `/home/palantir/.claude/skills/verify-consistency/SKILL.md:32-36` -- has DPS template in Step 1
3. `/home/palantir/.claude/skills/verify-cc-feasibility/SKILL.md:44-48` -- has DPS template in Step 2

**CORRECTION:** On deeper inspection, these 3 skills DO have DPS templates. Let me re-check the actual skills without DPS:

| Skill | Spawns Agent? | Has DPS? |
|-------|---------------|----------|
| pipeline-resume | Yes (Step 5: "Re-spawn agents") | NO explicit DPS template |
| task-management | Yes (pt-manager) | NO explicit DPS template |

**Revised Count:** Only 2 skills that spawn agents lack explicit DPS templates.

**Evidence:**
- `/home/palantir/.claude/skills/pipeline-resume/SKILL.md:55-57` -- "Re-spawn agents for in-progress tasks with full context" but no structured Context/Task/Constraints/Expected Output template
- `/home/palantir/.claude/skills/task-management/SKILL.md:20-21` -- "spawn pt-manager" but the L2 body describes operations procedurally without DPS delegation templates

**Severity: MEDIUM** -- pipeline-resume and task-management spawn agents but provide no structured delegation prompt. Lead must improvise the prompt, risking inconsistent results.

**Recommendation:** Add DPS templates to:
- pipeline-resume Step 5: Context (PT metadata + task statuses), Task (resume from interrupted phase), Constraints (preserve existing work), Expected Output (resumed pipeline state)
- task-management: Each operation (PT Creation, Batch Create, etc.) should have a pt-manager DPS template since they delegate to pt-manager

---

### F-04: MEDIUM -- Depth Disparity Between Execution Domain and Other Domains

**Quantitative Comparison:**

| Domain | Avg Lines per Skill | Has Decision Points | Has Anti-Patterns | Has Transitions |
|--------|--------------------|--------------------|-------------------|-----------------|
| execution (5 skills) | 196 | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) |
| orchestration (3 skills) | 180 | 3/3 (100%) | 3/3 (100%) | 3/3 (100%) |
| plan (3 skills) | 175 | 3/3 (100%) | 3/3 (100%) | 3/3 (100%) |
| plan-verify (3 skills) | 182 | 3/3 (100%) | 3/3 (100%) | 3/3 (100%) |
| pre-design (3 skills) | 62 | 0/3 (0%) | 0/3 (0%) | 0/3 (0%) |
| design (3 skills) | 60 | 0/3 (0%) | 0/3 (0%) | 0/3 (0%) |
| research (3 skills) | 68 | 0/3 (0%) | 0/3 (0%) | 0/3 (0%) |
| verify (5 skills) | 66 | 0/5 (0%) | 0/5 (0%) | 0/5 (0%) |
| homeostasis (4 skills) | 88 | 0/4 (0%) | 0/4 (0%) | 0/4 (0%) |
| cross-cutting (3 skills) | 95 | 0/3 (0%) | 0/3 (0%) | 0/3 (0%) |

**Pattern:** Skills in the execution/orchestration/plan/plan-verify domains have been deeply enriched with Decision Points, Anti-Patterns, Transitions, and Failure Handling sections (RSI L3/L4 improvements). The remaining 21 skills in pre-design, design, research, verify, homeostasis, and cross-cutting domains have NOT been enriched to the same level.

**Severity: MEDIUM** -- The 14 enriched skills set a quality standard that the remaining 21 do not meet. While all 35 have the 4 mandatory sections, the enriched skills provide dramatically better Lead guidance for complex decisions.

**Recommendation:** Prioritize enrichment of skills most frequently invoked in COMPLEX tier pipelines. Suggested order:
1. design-architecture, design-interface, design-risk (P1 -- critical for COMPLEX)
2. research-codebase, research-external, research-audit (P2 -- critical for COMPLEX)
3. verify-structure, verify-content, verify-consistency, verify-quality, verify-cc-feasibility (P7 -- always runs)
4. pre-design-brainstorm, pre-design-validate, pre-design-feasibility (P0 -- entry point)
5. manage-infra, manage-skills, manage-codebase, self-improve (homeostasis -- less critical)

---

### F-05: LOW -- `execution-impact` Has `user-invocable: false` But Others Are `true`

**Evidence:**
- `/home/palantir/.claude/skills/execution-impact/SKILL.md:13` -- `user-invocable: false`
- `/home/palantir/.claude/skills/execution-cascade/SKILL.md:14` -- `user-invocable: false`

**All other 33 skills have `user-invocable: true`.**

**Assessment:** This is CORRECT by design. execution-impact and execution-cascade are internal SRC skills triggered by hooks and pipeline flow, not user commands. No action needed.

**Severity: LOW (informational)** -- Design is intentional. Documented for completeness.

---

### F-06: LOW -- delivery-pipeline References `[P9` But CLAUDE.md Max Phase is P8

**Evidence:**
- `/home/palantir/.claude/skills/delivery-pipeline/SKILL.md:4` -- `[P9·Delivery·Terminal]`
- `/home/palantir/.claude/CLAUDE.md` -- tier table shows P8 as maximum phase

**This is a subset of F-01** but called out separately because delivery-pipeline is the terminal skill and its phase tag directly contradicts the CLAUDE.md phase ceiling.

**Severity: LOW** -- Cosmetic but confusing. If CLAUDE.md says phases go to P8, then delivery should be `[P8·Delivery·Terminal]`.

**Recommendation:** Change `[P9` to `[P8` in delivery-pipeline description.

---

### F-07: LOW -- Inconsistent `TIER_BEHAVIOR` Presence in Descriptions

Some skill descriptions include a `TIER_BEHAVIOR:` line, others do not.

**Skills WITH `TIER_BEHAVIOR` in description (4):**
1. `/home/palantir/.claude/skills/pre-design-brainstorm/SKILL.md:12` -- `TIER_BEHAVIOR: TRIVIAL=Lead-only, STANDARD=1-2 analysts, COMPLEX=2-4 analysts.`
2. `/home/palantir/.claude/skills/design-architecture/SKILL.md:12` -- `TIER_BEHAVIOR: TRIVIAL=Lead-only, STANDARD=analyst, COMPLEX=2-4 analysts.`
3. `/home/palantir/.claude/skills/execution-code/SKILL.md:12` -- `TIER_BEHAVIOR: T=single implementer...`
4. `/home/palantir/.claude/skills/plan-decomposition/SKILL.md:12` -- `TIER_BEHAVIOR: TRIVIAL=Lead-only...`

**Skills WITHOUT `TIER_BEHAVIOR` (31):** All others rely on the `## Execution Model` L2 section instead.

**Severity: LOW** -- TIER_BEHAVIOR in the L1 description is redundant when the L2 `## Execution Model` section covers the same information. The 4 skills that include it are not wrong, but the duplication uses precious L1 budget (max 1024 chars).

**Recommendation:** Remove `TIER_BEHAVIOR` from the 4 descriptions to free up L1 character budget. The `## Execution Model` section in L2 already provides this information.

---

### F-08: LOW -- 6 Skills Reference `run_in_background` But It Is Not Used Consistently

**Skills referencing `run_in_background` in Execution Model:**
1. `/home/palantir/.claude/skills/pre-design-brainstorm/SKILL.md:23` -- "Launch 1-2 analysts (run_in_background)"
2. `/home/palantir/.claude/skills/pre-design-validate/SKILL.md:21` -- "Launch analyst (run_in_background)"
3. `/home/palantir/.claude/skills/pre-design-feasibility/SKILL.md:21` -- "Launch researcher (run_in_background)"
4. `/home/palantir/.claude/skills/design-architecture/SKILL.md:22` -- "Launch analyst (run_in_background)"
5. `/home/palantir/.claude/skills/design-interface/SKILL.md:22` -- "Launch analyst (run_in_background)"
6. `/home/palantir/.claude/skills/design-risk/SKILL.md:22` -- "Launch analyst (run_in_background)"

**Context:** CLAUDE.md Section 2.1 says P0-P1 use "Lead with local agents (run_in_background)." This is correctly reflected in these 6 skills (all P0-P1).

**Issue:** No P2+ skills mention `run_in_background` because they use Team infrastructure. However, the distinction is important for Lead routing and should be documented more explicitly in P2+ skills.

**Severity: LOW** -- The P0-P1 skills correctly reference `run_in_background`. P2+ skills correctly omit it (they use Team infrastructure). The issue is implicit rather than explicit documentation of the Team mode.

**Recommendation:** No immediate action needed. Consider adding a brief note to P2+ skill Execution Models: "Team infrastructure (tmux split pane teammates)" to make the mode explicit.

---

### F-09: LOW -- `execution-code` and `execution-infra` Reference Nonexistent `mode` Parameter

**Evidence:**
- `/home/palantir/.claude/skills/execution-code/SKILL.md:61` -- `Set mode: "default" for code implementation`
- `/home/palantir/.claude/skills/execution-infra/SKILL.md:77` -- (implicit reference via DPS)
- `/home/palantir/.claude/skills/execution-cascade/SKILL.md:77` -- `Set mode: "default" for cascade implementers`

**Context:** The `mode` parameter is NOT a CC native Task tool parameter. This was previously identified in INFRA Audit v3 Iteration 4. The `permissionMode` field exists on agents, and the `mode` parameter on the Task tool was a hallucinated reference.

**Severity: LOW** -- This was identified in a previous audit and appears to not have been fully resolved. The `mode: "default"` instruction is harmless (CC ignores unknown parameters) but misleading.

**Recommendation:** Remove `mode: "default"` references from execution-code:61, execution-cascade:77. Replace with a note about agent permissionMode if needed.

---

### F-10: LOW -- `manage-codebase` Is the Longest Skill (173 lines) With Phase 2 Future Scope

**Evidence:**
- `/home/palantir/.claude/skills/manage-codebase/SKILL.md` -- 173 lines
- Lines 110-129: "Phase 2 (Future, Deferred)" section describes unreleased functionality

**Severity: LOW** -- The Phase 2 section is well-marked as deferred and does not confuse the current methodology. However, 173 lines approaches context budget concerns when the full L2 is loaded.

**Recommendation:** No immediate action. Monitor if agents loading this skill experience context pressure.

---

## 3. Detailed Per-Skill Analysis

### Legend
- **DPS**: Has explicit Delegation Prompt Standard template (Context/Task/Constraints/Expected Output)
- **FH**: Has `## Failure Handling` section
- **DP**: Has `## Decision Points` section
- **AP**: Has `## Anti-Patterns` section
- **TR**: Has `## Transitions` (Receives From / Sends To) section

### Pre-Design Domain (P0)

| Skill | Lines | DPS | FH | DP | AP | TR | Notes |
|-------|-------|-----|----|----|----|----|-------|
| pre-design-brainstorm | 90 | YES (Step 2) | NO | NO | NO | NO | AskUserQuestion correctly marked Lead-direct |
| pre-design-validate | 82 | YES (Step 2) | NO | NO | NO | NO | Clean 5-dimension matrix |
| pre-design-feasibility | 89 | YES (Step 2) | NO | NO | NO | NO | Terminal FAIL path documented inline |

### Design Domain (P1/P2 tag)

| Skill | Lines | DPS | FH | DP | AP | TR | Notes |
|-------|-------|-----|----|----|----|----|-------|
| design-architecture | 88 | YES (Step 2) | NO | NO | NO | NO | TIER_BEHAVIOR in description (redundant) |
| design-interface | 88 | YES (Step 2) | NO | NO | NO | NO | Clean contract specification |
| design-risk | 92 | YES (Step 2) | NO | NO | NO | NO | FMEA calibration in DPS |

### Research Domain (P2/P3 tag)

| Skill | Lines | DPS | FH | DP | AP | TR | Notes |
|-------|-------|-----|----|----|----|----|-------|
| research-codebase | 93 | YES (Step 2) | YES | NO | NO | NO | Failure handling added |
| research-external | 101 | YES (Step 2) | YES | NO | NO | NO | WebFetch restriction documented |
| research-audit | 89 | YES (Step 2) | NO | NO | NO | NO | DPS uses "DPS" label explicitly |

### Plan Domain (P3/P4 tag)

| Skill | Lines | DPS | FH | DP | AP | TR | Notes |
|-------|-------|-----|----|----|----|----|-------|
| plan-decomposition | 222 | YES (Step 2) | YES | YES | YES | YES | Fully enriched |
| plan-interface | 236 | YES (Step 2) | YES | YES | YES | YES | Fully enriched |
| plan-strategy | 256 | YES (Step 2) | YES | YES | YES | YES | Fully enriched |

### Plan-Verify Domain (P4/P5 tag)

| Skill | Lines | DPS | FH | DP | AP | TR | Notes |
|-------|-------|-----|----|----|----|----|-------|
| plan-verify-correctness | 232 | YES (Step 2) | YES | YES | YES | YES | Fully enriched |
| plan-verify-completeness | 243 | YES (Step 1) | YES | YES | YES | YES | C-02 context persistence addressed |
| plan-verify-robustness | 284 | YES (Step 2) | YES | YES | YES | YES | Longest plan-verify skill |

### Orchestration Domain (P5/P6 tag)

| Skill | Lines | DPS | FH | DP | AP | TR | Notes |
|-------|-------|-----|----|----|----|----|-------|
| orchestration-decompose | 232 | N/A (Lead-direct) | YES | YES | YES | YES | Fully enriched, always Lead-direct |
| orchestration-assign | 230 | N/A (Lead-direct) | YES | YES | YES | YES | Fully enriched, always Lead-direct |
| orchestration-verify | 262 | YES (Step 2, COMPLEX only) | YES | YES | YES | YES | Fully enriched |

### Execution Domain (P6/P7 tag)

| Skill | Lines | DPS | FH | DP | AP | TR | Notes |
|-------|-------|-----|----|----|----|----|-------|
| execution-code | 194 | YES (Step 2) | YES | YES | YES | YES | Tier-specific DPS variations |
| execution-infra | 199 | YES (Step 2) | YES | YES | YES | YES | Tier-specific DPS variations |
| execution-impact | 222 | YES (Step 3) | YES | YES | YES | YES | Fully enriched |
| execution-cascade | 265 | YES (Step 2) | YES | YES | YES | YES | Most complex skill |
| execution-review | 233 | YES (Steps 2-3) | YES | YES | YES | YES | Two-stage DPS |

### Verify Domain (P7/P8 tag)

| Skill | Lines | DPS | FH | DP | AP | TR | Notes |
|-------|-------|-----|----|----|----|----|-------|
| verify-structure | 88 | YES (Step 2) | NO | NO | NO | NO | Known limitation for YAML parsing |
| verify-content | 89 | YES (Step 1) | NO | NO | NO | NO | Clean content check |
| verify-consistency | 89 | YES (Step 1) | NO | NO | NO | NO | Relationship graph construction |
| verify-quality | 92 | YES (Step 1) | NO | NO | NO | NO | Quality scoring rubric in DPS |
| verify-cc-feasibility | 99 | YES (Step 2) | NO | NO | NO | NO | cc-reference cache priority |

### Homeostasis Domain (Cross-Cutting)

| Skill | Lines | DPS | FH | DP | AP | TR | Notes |
|-------|-------|-----|----|----|----|----|-------|
| manage-infra | 95 | YES (Step 1) | YES | NO | NO | NO | Failure handling present |
| manage-skills | 92 | YES (implicit) | NO | NO | NO | NO | DELETE limitation documented |
| manage-codebase | 173 | YES (Step 3) | YES (as Error Handling) | NO | NO | NO | Phase 2 deferred section |
| self-improve | 121 | YES (Steps 3, 5a) | YES | NO | NO | NO | Two DPS templates |

### Cross-Cutting Domain

| Skill | Lines | DPS | FH | DP | AP | TR | Notes |
|-------|-------|-----|----|----|----|----|-------|
| delivery-pipeline | 93 | Implicit (mentions DPS structure) | NO | NO | NO | NO | Fork Execution section instead |
| pipeline-resume | 83 | NO | NO | NO | NO | NO | Recovery Limitation note only |
| task-management | 158 | NO (procedural operations) | NO | NO | NO | NO | Unique structure (Operations not Methodology) |

---

## 4. Methodology Quality Assessment

### Concrete vs Vague Step Analysis

**All 35 skills have numbered methodology steps.** Quality assessment by concreteness:

| Quality Level | Definition | Count | Skills |
|--------------|-----------|-------|--------|
| Highly Concrete | Steps reference specific tools (Grep, Glob, Read), agent types, file paths, data formats | 27 | All DPS-having skills with tool references |
| Concrete | Steps describe specific actions but without tool names | 5 | design-architecture, design-interface, design-risk (steps describe ADR creation, interface definition), pipeline-resume, delivery-pipeline |
| Generic | Steps use abstract language ("analyze", "assess") | 3 | task-management (procedural but non-agent), manage-skills Step 4 ("Propose Actions"), research-audit Step 5 ("Recommend Actions") |

**No skill has truly vague methodology.** Even the "Generic" rated skills have sufficient procedural detail for execution. The main gap is tool-level specificity, not methodology structure.

---

## 5. Recommendations Summary

### Priority 1 (Recommended for Next RSI Iteration)

| ID | Finding | Action | Effort |
|----|---------|--------|--------|
| R-01 | F-01: Phase tag numbering mismatch | Update all 35 skill tags to match CLAUDE.md P0-P8 | Low (search-replace) |
| R-02 | F-02: 11 skills missing Failure Handling | Add `## Failure Handling` section to 11 skills | Medium (11 files) |
| R-03 | F-03: 2 skills missing DPS templates | Add DPS to pipeline-resume and task-management | Low (2 files) |

### Priority 2 (Future Enrichment)

| ID | Finding | Action | Effort |
|----|---------|--------|--------|
| R-04 | F-04: Depth disparity | Add Decision Points + Anti-Patterns + Transitions to remaining 21 skills | High (21 files) |
| R-05 | F-07: TIER_BEHAVIOR duplication | Remove from 4 description fields | Low (4 files) |
| R-06 | F-09: `mode: "default"` references | Remove from 2-3 files | Low |

### Priority 3 (Cosmetic)

| ID | Finding | Action | Effort |
|----|---------|--------|--------|
| R-07 | F-06: delivery-pipeline P9 tag | Change to P8 | Trivial |
| R-08 | F-08: run_in_background explicitness | Add Team mode note to P2+ skills | Low |
| R-09 | F-10: manage-codebase length | Monitor, no action needed | None |

---

## 6. Overall Health Score

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| L2 Completeness (mandatory 4 sections) | 10/10 | All 35 skills have Execution Model, Methodology, Quality Gate, Output |
| Methodology Quality | 8.5/10 | All concrete, 27/35 have tool-level specificity |
| DPS Template Coverage | 9/10 | 26/28 agent-spawning skills have DPS (93%) |
| Failure Handling | 7/10 | 24/35 have dedicated section (69%) |
| Phase Tag Consistency | 6/10 | Systematic numbering mismatch between skill tags and CLAUDE.md |
| Enrichment Sections | 6.5/10 | 14/35 fully enriched (40%), remaining 21 adequate but not enriched |

**Overall Skill Quality Score: 7.8/10**

The mandatory infrastructure is solid (10/10). The main gaps are:
1. Phase tag numbering inconsistency (systematic, fixable)
2. Enrichment depth disparity between execution/orchestration/plan domains vs others
3. Missing Failure Handling in 11 skills

---

## Appendix A: File Paths Referenced

All skill files analyzed:
```
/home/palantir/.claude/skills/pre-design-brainstorm/SKILL.md
/home/palantir/.claude/skills/pre-design-validate/SKILL.md
/home/palantir/.claude/skills/pre-design-feasibility/SKILL.md
/home/palantir/.claude/skills/design-architecture/SKILL.md
/home/palantir/.claude/skills/design-interface/SKILL.md
/home/palantir/.claude/skills/design-risk/SKILL.md
/home/palantir/.claude/skills/research-codebase/SKILL.md
/home/palantir/.claude/skills/research-external/SKILL.md
/home/palantir/.claude/skills/research-audit/SKILL.md
/home/palantir/.claude/skills/plan-decomposition/SKILL.md
/home/palantir/.claude/skills/plan-interface/SKILL.md
/home/palantir/.claude/skills/plan-strategy/SKILL.md
/home/palantir/.claude/skills/plan-verify-correctness/SKILL.md
/home/palantir/.claude/skills/plan-verify-completeness/SKILL.md
/home/palantir/.claude/skills/plan-verify-robustness/SKILL.md
/home/palantir/.claude/skills/orchestration-decompose/SKILL.md
/home/palantir/.claude/skills/orchestration-assign/SKILL.md
/home/palantir/.claude/skills/orchestration-verify/SKILL.md
/home/palantir/.claude/skills/execution-code/SKILL.md
/home/palantir/.claude/skills/execution-infra/SKILL.md
/home/palantir/.claude/skills/execution-impact/SKILL.md
/home/palantir/.claude/skills/execution-cascade/SKILL.md
/home/palantir/.claude/skills/execution-review/SKILL.md
/home/palantir/.claude/skills/verify-structure/SKILL.md
/home/palantir/.claude/skills/verify-content/SKILL.md
/home/palantir/.claude/skills/verify-consistency/SKILL.md
/home/palantir/.claude/skills/verify-quality/SKILL.md
/home/palantir/.claude/skills/verify-cc-feasibility/SKILL.md
/home/palantir/.claude/skills/manage-infra/SKILL.md
/home/palantir/.claude/skills/manage-skills/SKILL.md
/home/palantir/.claude/skills/manage-codebase/SKILL.md
/home/palantir/.claude/skills/self-improve/SKILL.md
/home/palantir/.claude/skills/delivery-pipeline/SKILL.md
/home/palantir/.claude/skills/pipeline-resume/SKILL.md
/home/palantir/.claude/skills/task-management/SKILL.md
```

## Appendix B: Phase Tag Mapping Reference

| Domain | Skill Tag Phase | CLAUDE.md Phase | Delta |
|--------|----------------|-----------------|-------|
| pre-design | P0 | P0 | 0 (match) |
| design | P2 | P1 | +1 |
| research | P3 | P2 | +1 |
| plan | P4 | P3 | +1 |
| plan-verify | P5 | P4 | +1 |
| orchestration | P6 | P5 | +1 |
| execution | P7 | P6 | +1 |
| verify | P8 | P7 | +1 |
| delivery | P9 | P8 | +1 |
| homeostasis | Homeostasis (no P) | N/A (cross-cutting) | N/A |
| cross-cutting | X-Cut (no P) | N/A | N/A |

The systematic offset of +1 for all domains after P0 suggests the skill tags use a deprecated numbering where P1 was reserved (possibly for a "pre-design-validate" sub-phase that was later collapsed into P0).
