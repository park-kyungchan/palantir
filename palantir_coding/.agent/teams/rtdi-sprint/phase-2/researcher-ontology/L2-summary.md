# L2 Summary — Researcher-Ontology (Phase 2)

> **Status:** COMPLETE
> **GC Version:** GC-v4
> **Last Updated:** 2026-02-08T01:30:00Z
> **Research Method:** WebSearch (7 queries) + WebFetch (8 pages) — MCP tools unavailable

---

## 1. Executive Summary

Completed research across 5 topics yielding 12 findings. Identified **4 TRUE documentation gaps** requiring new content and **3 depth enhancement opportunities** for existing sections.

### TRUE Gaps (New Content Needed)
1. **Granular Policies** (F-001, F-002) — Entirely missing from Security_and_Governance.md. Found comprehensive details: 8 comparison types, user attributes, weight limits, Object + Property Security Policies.
2. **Render Hints & UI Metadata** (F-003, F-004) — Minimal coverage in Ontology.md. Found: 8 render hint types with dependency chain, icon/color/title/search configuration.
3. **Python Functions GA** (F-007) — Not documented in OSDK_Reference.md. Python Functions went GA July 2025 with OSDK-native support.
4. **Ontology MCP** (F-009) — New feature announced January 2026. Model Context Protocol integration for external AI agents.

### Updates Needed (Existing Content)
5. **Python OSDK 2.x** (F-005) — Major version update GA July 2025, OSDK_Reference.md needs version bump.
6. **TS v2 Functions** (F-006) — GA July 2025 with full Node.js runtime. Current docs may reference beta status.
7. **AIP Logic Blocks** (F-008) — 6 block types and 4 LLM tool types need explicit enumeration in existing AIP section.

### No Change Needed
8. **Ontology Decomposition Guide** (F-010) — No official Palantir methodology exists. Existing Decision Matrix covers this.

---

## 2. Detailed Findings by Topic

### Topic 1: Granular Policies (F-001, F-002) — HIGH Priority

**Source:** Palantir official documentation on Granular Policies, Object Security Policies, Property Security Policies.

**Key Details:**
- **Comparison Types (8):** Equal, Intersects, Subset of, Superset of, Less than, Greater than, Less than or equal to, Greater than or equal to
- **User Attribute Types:** String, Multivalue String, Numeric
- **Weight System:** Each comparison has a weight; collection-to-field comparisons weight 1000; max 10 comparisons per policy; total weight must be < 10,000
- **Object Security Policies:** Row-level filtering — objects not matching policy are invisible to users lacking matching attributes
- **Property Security Policies:** Column-level + cell-level security — individual properties can be hidden or masked based on user attributes
- **Combined Effect:** Object Security (which rows) + Property Security (which columns/cells) = fine-grained cell-level access control
- **Relationship to Existing Content:** Complements existing Markings (classification-based) and CBAC (project-based) in Security_and_Governance.md

**Recommendation:** Add new section "## Granular Policies" in Security_and_Governance.md (~150-200 lines) covering all comparison types, user attributes, weight system, Object Security Policies, Property Security Policies, and combined usage patterns.

### Topic 2: Ontology Manager UI Metadata (F-003, F-004) — HIGH/MEDIUM Priority

**Source:** Palantir documentation on Ontology Manager configuration, render hints.

**Key Details:**
- **Render Hints (8 types):**
  1. Disable formatting — raw value display
  2. Identifier — marks property as object identifier in UIs
  3. Keywords — tokenized keyword display
  4. Long text — multi-line text rendering
  5. Low cardinality — enables dropdown/filter UIs
  6. Selectable — enables selection in tables/lists
  7. Sortable — enables column sorting
  8. Searchable — enables full-text search indexing
- **Dependency Chain:** Searchable is a prerequisite for Selectable, Sortable, and Low cardinality
- **ObjectType Display Config:** icon (BlueprintIcon enum), color, titleProperty (display name source), descriptionProperty, visibility settings
- **Search Configuration:** Which properties are searchable, fuzzy matching options, search weight/boost

**Recommendation:** Add new subsection under ObjectType in Ontology.md (~80-120 lines) covering render hints with dependency diagram and ObjectType display configuration.

### Topic 3: OSDK 2025-2026 Updates (F-005, F-006, F-007, F-009) — HIGH Priority

**Source:** Palantir platform changelog, OSDK documentation, Foundry announcements.

**Key Details:**
- **Python OSDK 2.x GA (July 2025):**
  - Major version bump with breaking changes from 1.x
  - New features: derived properties (beta), media sets (beta)
  - New query syntax and improved type safety
  - Migration required from 1.x

- **TypeScript v2 Functions GA (July 2025):**
  - Full Node.js runtime (previously V8 isolate with limitations)
  - Resource limits: 5GB memory, 8 CPUs
  - OSDK-native: full programmatic access to Ontology within Functions
  - Streaming support for real-time data processing

- **Python Functions GA (July 2025):**
  - OSDK first-class citizen (not just pandas DataFrames)
  - External API access via `functions.sources` configuration
  - Lightweight Functions for simple transforms
  - Configurable resources (memory, CPU allocation)

- **Ontology MCP (January 2026):**
  - Model Context Protocol integration
  - Exposes Developer Console applications as MCP tools
  - External AI agents (Claude, GPT, etc.) can query Ontology objects, execute actions
  - Early announcement — limited public documentation

**Recommendation:** Update OSDK_Reference.md Python section for 2.x (~50 lines), add Python Functions section (~80 lines), update TS Functions for v2 GA (~30 lines), add Ontology MCP section (~60 lines).

### Topic 4: AIP Logic Enhancement (F-008) — MEDIUM Priority

**Source:** Palantir AIP Logic documentation, block configuration guides.

**Key Details:**
- **Block Types (6):**
  1. Use LLM — sends prompt to language model with configured tools
  2. Apply Action — executes an Ontology Action
  3. Execute Function — calls a Foundry Function
  4. Conditionals — branching logic based on variable values
  5. Loops — iteration over object sets or lists
  6. Create Variable — stores intermediate computation results

- **LLM Tool Types (4):**
  1. Apply Actions — LLM can trigger Ontology Actions
  2. Call Function — LLM can invoke Foundry Functions
  3. Query Objects — LLM can search and retrieve Ontology objects
  4. Calculator — LLM can perform arithmetic computations

**Recommendation:** Enhance existing AIP Logic section in Ontology.md (~40-60 lines) with explicit block type and tool type enumerations.

### Topic 5: Ontology Decomposition Guide (F-010) — LOW Priority

**Finding:** No official Palantir methodology for mapping source code or data models to Ontology types. Palantir's approach is domain-driven (map real-world concepts, not database tables). The existing Decision Matrix section in Ontology.md already covers type selection guidance adequately.

**Recommendation:** No new content needed. Existing coverage is sufficient.

---

## 3. Cross-Impact Matrix

| Finding | Security_and_Governance.md | Ontology.md | OSDK_Reference.md | ObjectType_Reference.md |
|---------|---------------------------|-------------|-------------------|------------------------|
| F-001 Granular Policies: Comparisons | ADD ~100 lines | — | — | — |
| F-002 Granular Policies: Obj/Prop Security | ADD ~100 lines | — | — | — |
| F-003 Render Hints | — | ADD ~60 lines | — | — |
| F-004 UI Metadata | — | ADD ~60 lines | — | — |
| F-005 Python OSDK 2.x | — | — | UPDATE ~50 lines | — |
| F-006 TS v2 Functions | — | — | UPDATE ~30 lines | — |
| F-007 Python Functions | — | — | ADD ~80 lines | — |
| F-008 AIP Logic Blocks | — | ENHANCE ~50 lines | — | — |
| F-009 Ontology MCP | — | — | ADD ~60 lines | — |
| F-010 Decomposition Guide | — | NO CHANGE | — | — |
| F-011 Writeback Enhancement | — | ENHANCE ~30 lines | — | — |
| F-012 Rules Engine Enhancement | — | ENHANCE ~30 lines | — | — |
| **Total Estimated Lines** | **~200** | **~230** | **~220** | **0** |

---

## 4. Content Recommendations (Prioritized)

| # | Action | Target Doc | Finding | Est. Lines | Priority |
|---|--------|-----------|---------|------------|----------|
| 1 | Add "Granular Policies" section | Security_and_Governance.md | F-001, F-002 | 200 | HIGH |
| 2 | Add "Render Hints" subsection | Ontology.md | F-003 | 60 | HIGH |
| 3 | Add "UI Metadata & Display Config" subsection | Ontology.md | F-004 | 60 | HIGH |
| 4 | Update Python SDK section for 2.x GA | OSDK_Reference.md | F-005 | 50 | HIGH |
| 5 | Add "Python Functions" section | OSDK_Reference.md | F-007 | 80 | HIGH |
| 6 | Update TS Functions section for v2 GA | OSDK_Reference.md | F-006 | 30 | HIGH |
| 7 | Enumerate AIP Logic block/tool types | Ontology.md | F-008 | 50 | MEDIUM |
| 8 | Add "Ontology MCP" section | OSDK_Reference.md | F-009 | 60 | MEDIUM |
| 9 | Enhance Writeback patterns | Ontology.md | F-011 | 30 | LOW |
| 10 | Enhance Rules Engine examples | Ontology.md | F-012 | 30 | LOW |

**Total estimated new/updated content: ~650 lines across 3 documents.**

---

## 5. Research Sources

### Official Palantir Documentation (WebFetch)
1. Palantir Foundry — Granular Policies overview
2. Palantir Foundry — Object Security Policies configuration
3. Palantir Foundry — Property Security Policies configuration
4. Palantir Foundry — Ontology Manager render hints reference
5. Palantir Foundry — OSDK Python 2.x release notes
6. Palantir Foundry — TypeScript v2 Functions documentation
7. Palantir Foundry — Python Functions GA announcement
8. Palantir Foundry — Ontology MCP announcement (January 2026)

### Web Searches Conducted (7)
1. "Palantir Foundry Granular Policies 2025 2026"
2. "Palantir Ontology Manager render hints configuration"
3. "Palantir OSDK Python 2.x 2025 release"
4. "Palantir TypeScript Functions v2 Node.js runtime"
5. "Palantir Python Functions GA 2025"
6. "Palantir AIP Logic block types configuration"
7. "Palantir Ontology MCP Model Context Protocol 2026"

---

## 6. MCP Tools Usage Report

| Tool | Status | Usage | Fallback |
|------|--------|-------|----------|
| sequential-thinking | UNAVAILABLE | 0 calls | Inline reasoning in analysis |
| tavily | UNAVAILABLE | 0 calls | WebSearch (7 queries) |
| context7 | UNAVAILABLE | 0 calls | WebFetch (8 pages) |
| github | Not needed | 0 calls | N/A |

**Note:** MCP tools (tavily, context7, sequential-thinking) were not available in this session environment. WebSearch and WebFetch were used as equivalent fallbacks with comparable research coverage.
