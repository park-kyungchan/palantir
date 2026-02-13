# Team Memory — RTDI Sprint

## Lead
- [Decision] 2+2 workstream split: INFRA (DIA v5.0) + Ontology docs refinement
- [Decision] RTDI-001~008 permanent directives established from user requirements
- [Decision] Consolidated INFRA files under single implementer for cross-reference integrity
- [Decision] claude-code-guide pre-research for Opus 4.6 capability limits
- [Finding] claude-code-guide research complete — 14 hook events (not 7), 6 permissionModes, RTDI pattern via PostToolUse+additionalContext+TaskAPI
- [Finding] New hooks: UserPromptSubmit, PermissionRequest, PostToolUseFailure, Notification, Stop, SessionEnd
- [Finding] Skills: `context: fork` for subagent skills, `ultrathink` keyword, `hooks` field for skill-scoped hooks
- [Finding] RTDI pattern: PostToolUse detects changes → shared filesystem → SessionStart injects to other agents → TaskAPI coordinates
- [Finding] MAX_MCP_OUTPUT_TOKENS env var for MCP output limit control
- [Finding] PreToolUse can modify tool input via `updatedInput`, PostToolUse can modify MCP output via `updatedMCPToolOutput`
- [Warning] BUG-001 confirmed: plan mode blocks MCP tools. Always use mode: "default" with disallowedTools
- [Pattern] Opus 4.6 measured language: YAML frontmatter for structured data, 2-3 paragraph instructions max, tables for reference, code examples over prose

## researcher-ontology
- Spawned 2026-02-08, GC-v2 received, impact analysis submitted (5/5 RC PASS)
- LDAP challenge issued: DEPENDENCY_RISK (temporal dependency with implementer-ontology)
- [Finding] Phase 2 COMPLETE: 12 findings (F-001~F-012), 7 WebSearches, 8 WebFetches
- [Finding] Granular Policies: 8 comparison types (Equal, Intersects, Subset, Superset, LT, GT, LTE, GTE), user attributes (string, multivalue string, numeric), weight system (max 10 comparisons, collection-to-field weight 1000, total < 10000)
- [Finding] Object Security Policies = row-level filtering; Property Security Policies = column-level + cell-level; combined = fine-grained cell-level access control
- [Finding] Render Hints: 8 types (Disable formatting, Identifier, Keywords, Long text, Low cardinality, Selectable, Sortable, Searchable). Dependency chain: Searchable → Selectable/Sortable/Low cardinality
- [Finding] UI Metadata: icon (BlueprintIcon enum), color, titleProperty, descriptionProperty, searchConfiguration
- [Finding] Python OSDK 2.x GA July 2025: breaking changes from 1.x, new query syntax, derived properties (beta)
- [Finding] Python Functions GA July 2025: OSDK first-class, external APIs via functions.sources, Lightweight Functions
- [Finding] TS v2 Functions GA July 2025: full Node.js runtime (5GB/8CPU), OSDK-native, streaming support
- [Finding] Ontology MCP Jan 2026: MCP integration, Dev Console apps as MCP tools for external AI agents
- [Finding] AIP Logic: 6 block types (Use LLM, Apply Action, Execute Function, Conditionals, Loops, Create Variable) + 4 LLM tool types (Apply Actions, Call Function, Query Objects, Calculator)
- [Decision] No official Palantir Ontology Decomposition methodology exists — existing Decision Matrix is sufficient foundation
- [Warning] MCP tools (tavily/context7/sequential-thinking) were unavailable in researcher session; WebSearch/WebFetch used as fallback

## implementer-infra
- Spawned 2026-02-08 with mode: "plan" → SHUTDOWN (RTDI-009: plan mode permanently disabled)
- Re-spawned as implementer-infra-2 with mode: "default", GC-v4
- [Finding] Most ACs already PASS — infrastructure was already at v5.0 quality from prior work
- [Finding] Only 2 edits needed: CLAUDE.md version tag (AC-9) + execution-plan mode fix (AC-4)
- [Finding] Zero [MANDATORY]/[FORBIDDEN] in any target file — Opus 4.6 measured language already applied
- [Decision] permissionMode: acceptEdits stays for implementer/integrator — RTDI-009 targets spawn mode, not frontmatter (LDAP SCOPE_BOUNDARY defense accepted)
- [Finding] All protocol format strings already consistent across 16+ files (grep verified)
- [Warning] mode: "plan" was only remaining in execution-plan SKILL.md line 155 — now fixed

## implementer-ontology
- Spawned 2026-02-08 with mode: "plan" → SHUTDOWN (RTDI-009: plan mode permanently disabled)
- Re-spawned as implementer-ontology-2 with mode: "default", GC-v4, scope correction applied
- [Finding] All 4 docs read: Ontology.md 3178 lines (v3.0), OSDK_Reference.md 1954 lines (v2.0), Security_and_Governance.md 1673 lines (v2.0), ObjectType_Reference.md 703 lines (v1.0)
- [Finding] Previous L1/L2 from GC-v1 era exist — structural analysis valid but scope was too broad
- [Finding] TRUE gaps confirmed: (1) Ontology Decomposition Guide, (2) Granular Policies, (3) UI metadata, (4) OSDK currency, (5) Cross-refs
- [Decision] Will NOT duplicate existing searchAround/groupBy/3D-agg/AIP/Funnel content
- Impact analysis submitted to Lead, [IMPACT_VERIFIED] + LDAP PASS received
- [Decision] Self-research via tavily (2 searches) replaced killed researcher-ontology
- [Finding] IMPLEMENTATION COMPLETE — all 5 GAPs implemented:
  - GAP-1: Ontology Decomposition Guide (Section 20, ~350 lines, 8 phases with decision trees)
  - GAP-2: Granular Policies (Section 10 in Security doc, ~170 lines, from tavily research)
  - GAP-3: UI Metadata (subsection in Section 1, ~80 lines, render hints + search config)
  - GAP-4: OSDK 2025-2026 Updates (~80 lines, TS v2, Python v2, MCP, Platform SDKs)
  - GAP-5: Cross-references updated across all 4 docs (bidirectional, version-consistent)
- [Finding] Version bumps: Ontology.md 3.0→4.0, Security 2.0→3.0, OSDK 2.0→2.1, ObjectType 1.0→1.1
- [Finding] GC-v5 ENHANCEMENT PASS — integrated researcher-ontology 12 findings:
  - GAP-2: +8 comparison types, user attribute types, weight formula (1000/10000)
  - GAP-3: Replaced generic render hints with official 8 types + dependency chain
  - GAP-4: +Python Functions GA, TS v2 runtime (5GB/8CPU), Ontology MCP Jan 2026
  - NEW: AIP Logic Block Types (6 blocks + 4 LLM tools + composition pattern)
- [Decision] F-011 (Writeback) and F-012 (Rules Engine) deferred — low priority, existing content adequate

## implementer-integrator
- Spawned 2026-02-08, GC-v6 → auto-compact x2 (BUG-002). Monolithic 9-file directive too large.
- [Finding] Partial work preserved: ontology_1.md +UI Metadata (lines 172-253), ontology_7.md created (758 lines), ontology_8.md created (512 lines)
- [Warning] BUG-002 pattern: 9-file scope + read ALL files = context exhaustion before L1 save
- [Decision] Superseded by 3 batch agents (batch1/batch2/batch3) after Lead orchestration failure
- Led to Gate S-1/S-2/S-3 Pre-Spawn Checklist addition to CLAUDE.md §6

## implementer-batch1
- Spawned 2026-02-08, GC-v7. COMPLETE — ontology_1, 2, 3 enriched.
- [Finding] ontology_1.md: UI Metadata already present from integrator (lines 172-253) — added code_pattern_identification only (6 rules: @Entity, Aggregate Root, unique ID, DB table, Value Object, Enum)
- [Finding] ontology_2.md: +3 LinkType anti-patterns (LT_ANTI_006~008), +LinkType code_pattern_identification (4 ORM patterns), +Interface code_pattern_identification with decision_matrix
- [Finding] ontology_3.md: +ActionType code_pattern_identification (6 patterns), +AIP Logic Block Types (Section 1.10: 6 blocks + 4 LLM tool types + composition pattern)
- [Decision] Preserved existing structure — additive only, no reorganization

## implementer-batch2
- Spawned 2026-02-08, GC-v7. COMPLETE — ontology_4, 5, 6 enriched.
- [Finding] ontology_4.md: +5 sections (streaming pipelines, incremental config, MDO, code patterns, data connection sources)
- [Finding] ontology_5.md: +4 subsections (searchAround patterns, groupBy patterns, 3D aggregation, extended anti-patterns)
- [Finding] ontology_6.md: +section 2.9 OSDK 2025-2026 Updates (TS v2, Python v2, Platform SDKs, Functions GA, MCP, dev tooling)
- [Decision] All additions source-attributed with "> Source:" lines. No duplication.

## implementer-batch3
- Spawned 2026-02-08, GC-v7. AUTO-COMPACT after enriching ontology_7.md (758→1380 lines).
- [Finding] ontology_7.md enriched with deeper Function/Automation/Rules/AIP content from Ontology.md
- [Warning] L1 not updated before compact — all 4 files still "pending" in L1 despite ontology_7 being done
- [Decision] Remaining 3 files reassigned to batch3r (Gate S-3 applied)
