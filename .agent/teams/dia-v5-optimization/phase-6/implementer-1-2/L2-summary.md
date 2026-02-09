# L2 Summary — DIA v5.0 Measured Language Rewrite

## Implementer-1 | Phase 6

### Objective
Rewrite CLAUDE.md and task-api-guideline.md with Opus 4.6 measured language, bumping both from v4.0 to v5.0. The content and protocol structure remain identical — only the presentation tone changes.

### What Changed

**CLAUDE.md (353 lines → 353 lines)**
- Version bumped from 4.0 to 5.0 in header
- All inline `[MANDATORY]` tags removed — replaced with natural phrasing like "must", "always", "required"
- Inline `[PERMANENT]` removed from body text (e.g., "Reference injected global-context.md for pipeline awareness [PERMANENT]" → "Always reference injected global-context.md for pipeline awareness.")
- `[PERMANENT]` kept only at the `## [PERMANENT] Semantic Integrity Guard` section heading
- `[FORBIDDEN]` / "FORBIDDEN" replaced with "never" or "do not"
- ALL CAPS emphasis words (NEVER, EVERY, BEFORE, FULL, ANY) lowercased throughout
- `**Blocked:**` → `**Blocked commands:**` for clarity
- Section §7 title: "Mandatory Usage" → "Required Usage"
- MCP tools table: "Mandatory" column values → "Required"
- "WHY:" prefix labels converted to natural explanatory sentences
- "Prevention cost << Rework cost" → "Prevention cost is far less than rework cost"
- Korean inline text `TaskCreate/TaskUpdate는 Lead 전용` → English equivalent

**task-api-guideline.md (537 lines → 537 lines)**
- Version bumped from 4.0 to 5.0, date updated to 2026-02-08
- Title `[PERMANENT]` prefix removed
- Header "OWNERSHIP NOTE" → "Ownership"
- §1 heading: "Mandatory Pre-Call Protocol" → "Pre-Call Protocol"
- §2 subheading: "ABSOLUTE" → "cross-scope access is impossible"
- §6 heading: "[PERMANENT]" prefix removed
- ALL CAPS words normalized to lowercase throughout
- `[REQUIRED]` tag in CIP description → natural phrasing
- `FORBIDDEN` in tables → "Blocked" or "never allowed"
- "WHY:" prefix labels → natural explanatory prose
- "ALL PASS" in verification flow → "All pass"
- All period-terminated sentences where originals used abbreviated style

### What Did Not Change
- All protocol format strings ([DIRECTIVE], [IMPACT-ANALYSIS], etc.) — these are identifiers
- All table structures and their data
- All code blocks and YAML examples
- Section numbering (§0-§9 in CLAUDE.md, §1-§14 in task-api-guideline.md)
- §0 Language Policy content (per instruction)
- All technical content, thresholds, tier definitions, RC checklist items
- Output directory structure template

### Approach
Both files were rewritten as complete replacements using the Write tool, preserving the exact structure while systematically converting every instance of shouted emphasis, compliance tags, and verbose protocol language into natural, precise English that Opus 4.6 follows more effectively.
