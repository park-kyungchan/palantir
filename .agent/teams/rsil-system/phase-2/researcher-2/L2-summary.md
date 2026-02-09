# L2 Summary — /rsil-review Improvements + Agent Memory Schema

**Researcher:** researcher-2 | **Phase:** 2 | **Date:** 2026-02-09
**Target:** /rsil-review SKILL.md (561L) + agent-memory/rsil/ schema design

---

## Topic 1: /rsil-review Specific Improvement Items

### IMP-1: Ultrathink Integration (HIGH)

**What:** The official Claude Code skills documentation states: _"To enable extended thinking
in a skill, include the word 'ultrathink' anywhere in your skill content."_ (code.claude.com/docs/en/skills)

**Current state:** SKILL.md has no ultrathink keyword. R-0 synthesis phase relies on
sequential-thinking MCP tool but doesn't trigger extended thinking in the Claude Code
runtime itself.

**Proposed delta:** Add "ultrathink" as a natural word in the R-0 Phase description.
The official docs say including it "anywhere in your skill content" is sufficient.
Best placement: near line 237 where R-0 begins, or in the skill intro (line 9-11).

**Example:** Line 10 could read: "Meta-Cognition-Level quality review skill with ultrathink
deep reasoning. Applies universal research lenses..."

**Important nuance:** The common-workflows doc (code.claude.com/docs/en/common-workflows)
says thinking keywords "are interpreted as regular prompt instructions" — but the skills
doc explicitly recommends this for skills. Opus 4.6 uses adaptive reasoning with effort
levels (low/medium/high), and the ultrathink keyword in skills appears to set maximum
thinking budget. Architect should verify this doesn't conflict with /effort settings.

### IMP-2: Three-Tier Reading Optimization (MEDIUM)

**What:** Currently R-0 Step 1 (lines 251-261) reads target files during execution. Dynamic
context injection (`!`shell``) pre-reads files at skill load time. Could we pre-read
target files to reduce execution-time tool calls?

**Analysis:** This is NOT recommended for /rsil-review because:
1. Target files are specified via $ARGUMENTS, which varies per invocation
2. `!`shell`` commands execute at skill load time with the literal $ARGUMENTS string
3. You CAN use `!`shell`` with $ARGUMENTS — the docs confirm `$ARGUMENTS` is substituted
   before shell commands execute
4. However, pre-reading large files in dynamic context bloats the initial prompt

**Recommended approach:** Keep current model (read during R-0) but add a targeted
`!`wc -l $ARGUMENTS 2>/dev/null`` to pre-check file sizes. This helps R-0 decide whether
to read files in chunks or whole. Minimal context cost (~1 line of output).

### IMP-3: Agent Memory Integration (HIGH)

**What:** Cross-session RSIL learning currently relies on: (a) narrow-rsil-tracker.md
for raw findings, (b) main MEMORY.md for patterns. No structured cumulative data accessible
at skill load time.

**Proposed delta — Two integration points:**

1. **R-0 (read):** Add to Dynamic Context section (after line 51):
   `!`cat ~/.claude/agent-memory/rsil/MEMORY.md 2>/dev/null | head -50``
   This pre-loads the statistical summary (lens performance, recurring patterns) into context
   before Lead begins R-0 synthesis. The 50-line head captures the most critical data.

2. **R-4 (write):** After line 483 (MEMORY.md Update), add instruction:
   "Update `~/.claude/agent-memory/rsil/MEMORY.md` with: per-lens acceptance rate from this
   review, any new cross-cutting patterns discovered, any lens evolution candidates identified.
   Use Read-Merge-Write — never overwrite."

### IMP-4: NL Refinement / Redundancy Reduction (MEDIUM)

**What:** Structural analysis reveals significant overlap between three sections:

| Section | Lines | Content |
|---------|-------|---------|
| Key Principles (§) | 537-549 (13L) | 11 positive statements |
| Never (§) | 551-561 (11L) | 10 negative statements |
| Various phase instructions | scattered | Same concepts embedded in workflow |

**Overlap analysis:** 60% of Key Principles have a direct "Never" counterpart:
- "Framework is universal, scope is dynamic" ↔ "Use hardcoded Research Questions"
- "AD-15 inviolable" ↔ "Propose adding a new hook"
- "Evidence-based only" ↔ "Accept findings without evidence"
- "User confirms application" ↔ "Modify files without user approval"
- "Sequential thinking always" ↔ (no counterpart — unique)
- "Terminal, no auto-chain" ↔ "Auto-chain to another skill"

**Proposed delta:** Merge into single "Principles" section with ~15 items (vs current 21).
Each principle stated once in its positive form. Estimated savings: ~8 lines.

Opus 4.6 NL optimization note: The current language is already measured and natural.
No excessive ALL CAPS or [MANDATORY] markers. The main improvement is deduplication,
not tone change.

### IMP-5: Dynamic Context Optimization (LOW)

**Current state:** 7 shell commands (lines 38-51):
1. `ls hooks/*.sh` — hook files
2. `jq hooks keys` — hook config
3. `ls agents/*.md` — agent files
4. `ls skills/*/SKILL.md` — skill files
5. `head -3 CLAUDE.md` — version header
6. `git diff --name-only HEAD~1` — recent changes
7. `wc -l agent-common-protocol.md` — protocol size

**Assessment:** These are well-chosen and minimal. Each provides specific context for the
Integration Audit (which checks cross-file consistency). No removals recommended.

**Addition:** As noted in IMP-3, add one more:
`!`cat ~/.claude/agent-memory/rsil/MEMORY.md 2>/dev/null | head -50``

### IMP-6: Structural Redundancy — Merge Key Principles + Never (HIGH)

See IMP-4 analysis. Additionally, the "What this skill does / does NOT do" section (lines
29-34) partially overlaps with Key Principles. Consider moving the "does NOT" items into
the merged Principles section.

### IMP-7: Output Format Templates (MEDIUM)

**Current state:** Lines 201-231 prescribe exact output format for both [A] and [B] agents.

**Issue:** These templates are sent to one-shot subagents in their directive (R-0 Step 4).
The templates are appropriate but slightly over-formatted with markdown code blocks inside
markdown code blocks (nested formatting). Opus 4.6 follows natural instructions well —
the templates could be simplified to guidance rather than exact format.

**Proposed delta:** Convert from exact template to structured guidance:
"Include: Findings table (ID, finding, layer, category, evidence), per-finding detail
(what, where, capability, why suboptimal, proposed text), L1 Optimality Score, Top 3."
Saves ~5 lines while maintaining all required content.

### IMP-8 & IMP-9: Minor Items (LOW)

- IMP-8: R-0 sequential-thinking instruction is fine; ultrathink (IMP-1) covers the gap
- IMP-9: Error handling table (lines 522-534) is well-structured, not redundant — keep

---

## Topic 2: Agent Memory Schema for Cross-Session RSIL

### Design: ~/.claude/agent-memory/rsil/MEMORY.md

**Key constraint:** First 200 lines auto-loaded into system prompt. Must be concise and
immediately useful. Topic files loaded on-demand.

### Proposed Schema (4 sections, ~120 lines initial)

```markdown
# RSIL Agent Memory

## 1. Configuration
- Last review date: {date}
- Total reviews completed: {N}
- Cumulative findings: {N} (accepted: {N}, rejected: {N}, deferred: {N})
- Acceptance rate: {%}
- Active lenses: L1-L8 (last updated: {date})

## 2. Lens Performance Statistics
| Lens | Reviews Applied | Findings Generated | Accepted | Acceptance Rate |
|------|----------------|-------------------|----------|-----------------|
| L1 TRANSITION INTEGRITY | {n} | {n} | {n} | {%} |
| L2 EVALUATION GRANULARITY | {n} | {n} | {n} | {%} |
| ... (L3-L8) | | | | |

Top-performing lenses: {list by acceptance rate}
Low-yield lenses: {list with <50% acceptance}

## 3. Cross-Cutting Patterns (Universal)
Only patterns applicable across ANY target. One-off findings stay in tracker.

### Pattern: {name}
- Origin: {sprint/finding ID}
- Scope: {where applicable}
- Principle: {one-line}
- Applied in: {list of targets}

## 4. Lens Evolution Candidates
New universal patterns that may become L9, L10, etc.

### Candidate: {name}
- Evidence: {finding IDs from multiple reviews}
- Universality test: Applies to ≥3 different target types?
- Proposed lens question: {draft}
- Status: CANDIDATE / PROMOTED / REJECTED
```

### Separation of Concerns

| Data | Location | Why Here |
|------|----------|----------|
| Per-review raw findings | narrow-rsil-tracker.md | Detailed audit trail, per-sprint structure |
| Cumulative statistics | agent-memory/rsil/MEMORY.md §1-2 | Auto-loaded, cross-session continuity |
| Universal patterns | agent-memory/rsil/MEMORY.md §3 | Auto-loaded, inform R-0 synthesis |
| Lens evolution candidates | agent-memory/rsil/MEMORY.md §4 | Auto-loaded, guide lens expansion |
| RSIL summary for user | main MEMORY.md (projects/) | User-facing, high-level status only |
| Session-specific notes | TEAM-MEMORY.md | Ephemeral, single-session coordination |

**Key principle:** agent-memory/rsil is the RSIL agent's working memory. It reads this at
the start of every /rsil-review invocation (via dynamic context injection) and writes to
it at the end (R-4 phase). The tracker is the permanent audit trail. Main MEMORY.md gets
a one-line status update only.

### Interaction Model

```
Skill load → !`cat agent-memory/rsil/MEMORY.md | head -50`
                  ↓
R-0 synthesis (informed by lens performance + known patterns)
                  ↓
R-1/R-2 research + classification
                  ↓
R-4 record → Update agent-memory/rsil/MEMORY.md (statistics + patterns)
           → Update narrow-rsil-tracker.md (detailed findings)
           → Update main MEMORY.md (one-line summary if pattern discovered)
```

### 200-Line Budget Allocation

| Section | Estimated Lines | Priority |
|---------|----------------|----------|
| §1 Configuration | 8 | Critical — basic stats |
| §2 Lens Performance | 20 | Critical — informs R-0 lens selection |
| §3 Cross-Cutting Patterns | 60-80 | High — informs R-0 research questions |
| §4 Lens Evolution | 30-50 | Medium — forward-looking |
| Buffer | 40-80 | Growth room for new patterns/candidates |

Initial population: Seed from current tracker data (24 findings, 4 patterns, 79% acceptance).

---

## Summary of Recommendations

### For Architect (Phase 3):

1. **IMP-1 (ultrathink):** Add keyword per official docs. Verify interaction with /effort.
2. **IMP-3 (agent memory):** Design the read/write integration points in R-0 and R-4.
3. **IMP-6 (merge principles/never):** Merge 21→~15 items, net -8 lines.
4. **IMP-7 (output templates):** Simplify to guidance, net -5 lines.
5. **MEM-1 (schema):** Use the 4-section schema. Seed from tracker data.
6. **MEM-2 (separation):** Agent memory = stats+patterns, tracker = raw, main = summary.
7. **IMP-2 (reading):** Add `wc -l` pre-check only. Don't pre-read full files.
8. **IMP-5 (dynamic context):** Add agent memory read as 8th shell command.

### Shared Foundation Impact:
- All improvements are within /rsil-review scope only
- Shared Foundation (8 Lenses, AD-15, Layer 1/2 Boundary) remains UNCHANGED
- Agent memory schema is /rsil-review-specific, not shared with /rsil-global
- /rsil-global can independently adopt similar agent memory pattern later

---

## Evidence Sources

| Source | What Used |
|--------|-----------|
| code.claude.com/docs/en/skills | Ultrathink in skills, dynamic context injection, $ARGUMENTS |
| code.claude.com/docs/en/memory | Agent memory 200-line limit, auto-loading, topic files |
| code.claude.com/docs/en/common-workflows | Extended thinking, effort levels, adaptive reasoning |
| platform.claude.com/docs/en/extended-thinking | Opus 4.6 adaptive thinking, budget deprecation |
| goatreview.com/claude-code-thinking-levels | Token budgets: think 4K, megathink 10K, ultrathink 32K |
| SKILL.md lines 1-561 | Full structural analysis, section-by-section |
| narrow-rsil-tracker.md lines 1-252 | Cumulative data: 24 findings, 4 patterns, 79% acceptance |
| agent-memory/*/MEMORY.md (6 files) | Existing schema patterns for agent memory |
| CLAUDE.md lines 1-173 | Infrastructure reference, AD-15, Layer definitions |
| agent-common-protocol.md lines 1-89 | Agent memory section (line 85-89), completion protocol |

## MCP Tools Usage

| Tool | Used For | Status |
|------|----------|--------|
| sequential-thinking | N/A — analysis done through structural reading | Not needed for this research scope |
| tavily | N/A — replaced by WebSearch/WebFetch | Unavailable in session |
| context7 | N/A | Unavailable in session |
| WebSearch | Claude Code features research (3 queries) | USED |
| WebFetch | Official docs: skills, memory, extended-thinking, common-workflows (5 fetches) | USED |
