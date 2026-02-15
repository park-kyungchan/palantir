# Implementer Agent Memory

## Cross-File Editing Patterns

### Cross-Reference Integrity
- When format strings must be identical across N files, copy-paste from a single source of truth (implementation plan), NEVER retype
- Use Grep validation after all edits to verify character-level identity across files
- Anchor edits by surrounding text patterns, not line numbers (line numbers shift after earlier edits)
- Execute edits top-to-bottom within each file to minimize line shift confusion

### Edit Ordering Strategy
- Version headers FIRST (single-line replacements, no line shift)
- Then insertions from top of file to bottom
- Separate Task A (foundation files) from Task B (consumer files) -- foundation defines what consumers reference

## Structural Optimization Patterns

### Full-File Rewrite vs Incremental Edit
- When reducing a file by >30%, full rewrite (Write tool) is cleaner than 15+ incremental Edits
- Reduces risk of line-shift confusion and missed edits
- Requires careful semantic audit against original -- checklist every section header

### Deduplication Strategy
- Identify RULES (behavioral: what to do) vs PROCEDURES (operational: how to do it)
- Rules stay in the always-loaded file (CLAUDE.md system prompt)
- Procedures can move to external reference files (require active Read)
- This creates a safety net: if reference file fails, rules still work

### disallowedTools Cleanup Principle
- Only list tools that COULD be called but shouldn't (TaskCreate, TaskUpdate)
- Don't list tools already absent from the tools allowlist (mechanical enforcement handles it)
- Always Grep-verify after cleanup across all agent files

## Infrastructure File Patterns

### Agent .md Structure
- Agents use YAML frontmatter for L1 metadata (model, tools, permissions, description)
- Agent body = role identity, loaded in isolated context on spawn
- Pipeline phases: P0-P8 (sequential numbering, see CLAUDE.md tier table)

### Skill SKILL.md Structure
- Frontmatter L1: description with WHEN/DOMAIN/INPUT_FROM/OUTPUT_TO/METHODOLOGY (max 1024 chars)
- Body L2: Execution Model + Methodology (5 steps) + Quality Gate + Output
- Enrichment sections: Decision Points, Anti-Patterns, Transitions, Failure Handling

## Git Workflow Patterns
- Commit after each logical unit of work, not after every file edit
- Use conventional commit format: type(scope): description
- Stage only the files relevant to the current change

## Error Handling Patterns
- Edit tool fails if old_string is not unique -- add more surrounding context to disambiguate
- Edit tool fails if file has not been read first -- always Read before Edit
- When editing YAML frontmatter, preserve exact indentation (spaces, not tabs)
- Validate JSON mentally after editing settings.json (check brackets, commas, trailing commas)
