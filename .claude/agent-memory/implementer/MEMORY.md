# Implementer Agent Memory

## Cross-File Editing Patterns

### Cross-Reference Integrity (CH-001 LDAP, 2026-02-07)
- When format strings must be identical across N files, copy-paste from a single source of truth (implementation plan), NEVER retype
- Use Grep validation after all edits to verify character-level identity across files
- Anchor edits by surrounding text patterns, not line numbers (line numbers shift after earlier edits)
- Execute edits top-to-bottom within each file to minimize line shift confusion

### Edit Ordering Strategy
- Version headers FIRST (single-line replacements, no line shift)
- Then insertions from top of file to bottom
- Separate Task A (foundation files) from Task B (consumer files) — foundation defines what consumers reference

## DIA Protocol Learnings

### LDAP Bootstrap
- When implementing the protocol that defines your OWN Phase 1.5, Lead provides [BOOTSTRAP] section in the directive
- Bootstrap contains the rules for the session even though the agent .md file doesn't have them yet
- This is a chicken-and-egg pattern: you follow bootstrap LDAP rules while implementing permanent LDAP rules

### Impact Analysis Quality
- Map 3-tier consumption chains: definition (Lead reads to generate) → procedure (Lead reads to execute) → instruction (teammate reads to parse/respond)
- Trace format mismatch propagation: parser failure → gate stall → pipeline halt (3 hops)
- Two-Gate Flow as abstract interface contract: input→output boundaries, not internal substeps

## Structural Optimization Patterns (INFRA E2E, 2026-02-08)

### Full-File Rewrite vs Incremental Edit
- When reducing a file by >30%, full rewrite (Write tool) is cleaner than 15+ incremental Edits
- Reduces risk of line-shift confusion and missed edits
- Requires careful semantic audit against original — checklist every section header

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
- Phase sections are numbered: Phase 0, Phase 1, Phase 1.5 (new), Phase 2, Phase 3
- implementer/integrator have Two-Gate System section between Phase 1 and Phase 2
- architect/tester/researcher go directly from Phase 1 to Phase 2
- devils-advocate has TIER 0 exemption — goes Phase 0 → Phase 1: Execution (no impact analysis)

### CLAUDE.md [PERMANENT] Section
- Lead duties: numbered 1-7 (items 1-6 original, 7 added for LDAP)
- Teammate duties: numbered 1-6 with 2a inserted (Challenge Response between 2 and 3)
- WHY paragraph: describes all 3 DIA layers with cost estimate
