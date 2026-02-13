## Summary

Architecture design for README.md rewrite visualizing `.claude/` INFRA v9.0. Defines 12-section hierarchy (Architecture-First), 8 ASCII diagrams, 14 standardized tables, and 16 collapsible sections. Estimated ~950 lines. Covers all 78 infrastructure files with explicit mapping. Key design: hero diagram (~25 lines) as simplified layer view, detailed pipeline in Section 2, per-category collapsible agent details.

## Section Hierarchy

| # | Section | Subsections | Est. Lines | Key Visual |
|---|---------|-------------|-----------|------------|
| 1 | System Architecture | Hero diagram + legend | ~80 | Layer diagram: PT → Lead → Coordinators → Workers |
| 2 | Pipeline Flow | Phase chain, tiers, PRE/EXEC/POST, rollback | ~90 | Vertical pipeline with tier branching |
| 3 | Agents (43) | Overview, coordinators, 14 categories, tool matrix, colors | ~255 | 14 collapsible category sections |
| 4 | Skills (10) | Coverage timeline, reference table, coordinator mapping | ~60 | Horizontal phase-coverage timeline |
| 5 | Hooks (4) | Lifecycle diagram, reference table, dependency chain | ~65 | Session lifecycle event flow |
| 6 | References (9) | Consumer network, table, fan-in | ~65 | Fan-out consumer diagram |
| 7 | Configuration | Hierarchy, env vars, MCP, permissions | ~60 | 3-layer settings merge diagram |
| 8 | Observability (RTD) | Directory structure, event flow | ~45 | Hook → events.jsonl → monitoring flow |
| 9 | Agent Memory | Persistence model, file listing | ~30 | — |
| 10 | CLAUDE.md | Section map, decision integration | ~45 | D-001~D-017 matrix |
| 11 | Directory Tree | Complete .claude/ listing | ~85 | Collapsible tree (all 78 files) |
| 12 | Key Concepts | L1/L2/L3, PT, lenses, coordinator modes | ~60 | — |
| — | Version + badges | Title, badges, ToC | ~30 | GitHub badges |

## Architecture Decisions

**AD-1: Architecture-First ordering.** System Architecture diagram at the top, progressive drill-down through components, Key Concepts as glossary at the bottom. Rationale: readers grasp the system visually first, then explore details. Alternative rejected: concept-first (requires reading abstractions before seeing the system).

**AD-2: Collapsible `<details>` for dense content.** 14 agent category sections + directory tree default-closed. Rationale: ~255 lines of agent tables would overwhelm. Risk: some GitHub clients render details poorly — mitigated by including summary stats in the visible portion.

**AD-3: 4-5 column table maximum.** Agent tables split per-category (4 cols each) rather than one mega-table (8 cols). Rationale: GitHub wraps wide tables with horizontal scroll, degrading readability. The Tool Distribution Matrix (Section 3.4) uses 4 columns.

**AD-4: English-primary, Korean parenthetical.** All ASCII diagrams use English labels only (Korean breaks monospace alignment). Korean appears in: main subtitle, parenthetical annotations after key terms, and table descriptions where helpful. Rationale: monospace fonts require single-width characters for alignment.

**AD-5: Hero diagram simplified (~25 lines).** Shows 5 layers: PT → Lead → 8 Coordinators → Lead-Direct agents → Cross-cutting systems. Detailed 60-line pipeline diagram in Section 2. Rationale: hero must fit in one screen; detail available on scroll.

**AD-6: Pipeline Tiers in Section 2, not separate.** TRIVIAL/STANDARD/COMPLEX tier definitions live next to the pipeline flow diagram where they are immediately relevant. Same for rollback paths. Ontological Lenses go in Section 12 (Key Concepts). Rationale: context-adjacent placement reduces cross-referencing.

**AD-7: 78-file coverage guarantee.** Explicit mapping: agents(43) in S3, skills(10) in S4, hooks(4) in S5, references(9) in S6, settings(2)+.claude.json(1) in S7, CLAUDE.md(1) in S10, agent-memory(8) in S9. Directory Tree in S11 is the completeness verification — lists every file path.

## Diagram Specifications

8 ASCII diagrams planned:
1. **Hero (System Architecture):** 5-layer cake — PT → Lead → Coordinators(8) → Lead-Direct(4) → Foundation
2. **Pipeline Flow:** Vertical P0-P9 with PRE/EXEC/POST borders, coordinator+workers at each phase
3. **Skill Coverage Timeline:** Horizontal P0-Post with skill spans
4. **Hook Lifecycle:** Session timeline with 4 event types
5. **Hook Dependency Chain:** Data flow between hooks (registry, current-dp)
6. **Reference Consumer Fan-out:** Each reference → its consumers with criticality
7. **Configuration Hierarchy:** 3-layer merge (.claude.json → settings.json → settings.local.json)
8. **Observability Event Flow:** Lead writes → hooks capture → events.jsonl → monitoring reads

## Table Templates

All tables use GFM pipe syntax. Standard formats:

- **Agent per-category:** `| Agent | MaxTurns | Key Tools | Description |` (4 cols)
- **Coordinator overview:** `| Coordinator | Workers | Phase | MaxTurns |` (4 cols)
- **Skill reference:** `| Skill | Phase | Lines | Coordinator | Description |` (5 cols)
- **Hook reference:** `| Event | Script | Mode | Timeout | Purpose |` (5 cols)
- **Reference listing:** `| Document | Version | Lines | Consumers | Purpose |` (5 cols)
- **Tool distribution:** `| Tool | Workers | Coordinators | Total |` (4 cols)

## GitHub Rendering Decisions

1. All ASCII inside triple-backtick code blocks (no language tag)
2. `<details><summary>` for: 14 agent categories, directory tree, detailed pipeline
3. Badges at top: 43 Agents, 10 Skills, 4 Hooks, 9 References, 78 Files, ~10K Lines
4. Manual ToC with GitHub heading anchor links
5. No nested `<details>` (unreliable rendering)
6. No HTML beyond `<details>` tags
7. Unicode box-drawing characters (verified: GitHub renders in code blocks)

## Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| Hero diagram too complex | MEDIUM | Simplified 25-line layer view; detail in Section 2 |
| GitHub `<details>` rendering issues | LOW | Summary always shows key stats; content degrades gracefully |
| 950-line README overwhelming | MEDIUM | 16 collapsible sections reduce visible length to ~400 |
| Korean characters breaking alignment | LOW | English-only in code blocks; Korean only in markdown text |
| Missing file coverage | HIGH | Section 11 Directory Tree = completeness checklist |

## PT Goal Linkage

- Exhaustive INFRA visualization: all 78 files mapped across 12 sections with 8 diagrams
- Architecture-First: hero diagram in Section 1, progressive drill-down through Sections 2-12
- GitHub-renderable: all decisions verified against GFM spec, no exotic features
- English primary, Korean secondary: AD-4 defines the exact language boundaries

## Evidence Sources

- Phase 2 research: L2-summary.md (43 agents, 10 skills, 4 hooks, 9 references, 78 files)
- Agent inventory: L3-full/agent-inventory.md (complete tool matrix, colors, maxTurns)
- Skills inventory: L3-full/skills-inventory.md (lines, coordinators, phase coverage)
- Infrastructure inventory: L3-full/infrastructure-inventory.md (hooks, references, settings, CLAUDE.md)
- Relationship map: L3-full/relationship-map.md (skill→agent, hook→event, reference→consumer)
- Current README.md: /home/palantir/README.md (655 lines, v7.1.0, completely outdated)
