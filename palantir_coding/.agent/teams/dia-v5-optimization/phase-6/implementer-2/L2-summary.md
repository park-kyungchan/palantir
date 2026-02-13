# L2 Summary — Agent .md Measured Language Rewrite + BUG-001 Fix

## Overview
Rewrote all 6 agent definition files (`.claude/agents/*.md`) to apply Opus 4.6 measured language
and fix BUG-001 (permissionMode blocking MCP tools for researcher/architect).

## Changes Applied

### BUG-001 Fix (Critical)
- **researcher.md:** `permissionMode: plan` → `permissionMode: default`
- **architect.md:** `permissionMode: plan` → `permissionMode: default`
- Other agents' permissionMode values were already correct and left unchanged.

### Measured Language Transformation (all 6 files)
1. **Removed all `[MANDATORY]` inline markers** — section headings now use parenthetical tier info
   - Example: `Phase 1: Impact Analysis [MANDATORY — TIER 1 Full, max 3 attempts]`
   - → `Phase 1: Impact Analysis (TIER 1 Full, max 3 attempts)`
2. **Removed all `[PERMANENT]` inline markers** — integrated naturally into text
3. **Removed all `[FORBIDDEN]` markers** — replaced with "never" or "do not"
4. **Preserved protocol format tags** — `[IMPACT-ANALYSIS]`, `[STATUS]`, `[CHALLENGE]`, `[DIRECTIVE]`
   remain unchanged (these are protocol identifiers, not emphasis markers)
5. **All bold ALL CAPS constraints** → natural sentence case phrasing
   - `**Plan Approval is MANDATORY**` → `Plan approval is required`
   - `You CANNOT modify...` → `You cannot modify...`
   - `You are COMPLETELY read-only` → `You are completely read-only`

### Numbering Fixes
- **integrator.md:** Phase 3 Execution had duplicate `5.` items and skipped `7.`
  - Before: 1,2,3,4,5,5,6,8,9,10 → After: 1,2,3,4,5,6,7,8,9,10
- **devils-advocate.md:** Phase 1 Execution had duplicate `2.` item
  - Before: 1,2,2,3,4,5,6,7,8 → After: 1,2,3,4,5,6,7,8,9

### Structural Consistency (all 6 files follow same pattern)
1. Frontmatter (name, description, model, permissionMode, memory, tools, disallowedTools)
2. `# {Role} Agent` heading
3. `## Role` — brief description
4. `## Protocol` — Phase 0 → Phase 1 → Phase 1.5 → Phase 2+ (varies by role)
5. `## Output Format` — L1/L2/L3
6. Role-specific sections (Challenge Categories, Test Design Principles, etc.)
7. `## Context Pressure & Auto-Compact`
8. `## Constraints`
9. `## Memory`

## Validation Results
- `grep [MANDATORY]`: 0 matches across all 6 files
- `grep [FORBIDDEN]`: 0 matches across all 6 files
- `grep [PERMANENT]`: 0 matches across all 6 files
- BUG-001 fix confirmed: researcher + architect both have `permissionMode: default`
- All frontmatter YAML preserved identically (except permissionMode fixes)
- All protocol tags preserved: [IMPACT-ANALYSIS], [STATUS], [CHALLENGE], etc.
