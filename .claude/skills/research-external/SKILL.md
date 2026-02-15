---
name: research-external
description: |
  [P2·Research·External] External documentation researcher. Fetches and synthesizes documentation from web sources, official docs, and package registries using WebSearch, WebFetch, context7, and tavily.

  WHEN: design domain complete. Architecture decisions reference external libraries, APIs, or patterns needing doc validation.
  DOMAIN: research (skill 2 of 3). Parallel-capable: codebase || external -> audit.
  INPUT_FROM: design domain (technology choices, library references needing doc validation).
  OUTPUT_TO: research-audit (external findings for gap analysis), plan-strategy (external constraints). Unvalidated deps reported to research-audit.

  METHODOLOGY: (1) Extract external dependencies from architecture decisions, (2) Search official docs via WebSearch/context7, (3) Fetch key pages via WebFetch, (4) Verify version compatibility and API availability, (5) Synthesize into structured findings with source links.
  OUTPUT_FORMAT: L1 YAML dependency validation matrix, L2 markdown doc summary with source URLs.
user-invocable: true
disable-model-invocation: false
---

# Research — External

## Execution Model
- **TRIVIAL**: Lead-direct. Quick web search for one library/API.
- **STANDARD**: Spawn researcher (has web access). Systematic documentation research.
- **COMPLEX**: Spawn 2-4 researchers. Each covers non-overlapping external topics.

## Methodology

### 1. Extract External Dependencies
From architecture decisions, list external dependencies needing research:
- Libraries and their versions
- API endpoints and protocols
- Design patterns from official documentation
- Claude Code native capabilities (via claude-code-guide or context7)

### 2. Search Official Documentation
For STANDARD/COMPLEX tiers, construct the delegation prompt for each researcher with:
- **Context**: Paste the dependency list from Step 1 with version constraints (from design-architecture L1 `technologies[]` and L2 version specifications). Include the specific documentation questions needing validation per dependency.
- **Task**: "Research official documentation for [assigned dependency list]. For each dependency: (1) verify version compatibility with current environment, (2) confirm API availability and stability, (3) check for known issues or deprecations, (4) verify license compatibility. Use context7 first, WebSearch second, WebFetch for specific pages, tavily as fallback."
- **Scope**: Explicit list of dependencies assigned to this researcher. For COMPLEX, split by technology domain (e.g., researcher-1: libraries/frameworks, researcher-2: APIs/protocols).
- **Constraints**: Web-enabled research only (WebSearch, WebFetch, context7, tavily). No file modifications. Cite all sources with full URLs.
- **Expected Output**: Per-dependency validation entry: name, version, status (validated/issue/unknown), source URL, key facts, impact on architecture, confidence rating (high=official docs, medium=community, low=inference).

Priority order for each dependency:
1. **context7** (resolve-library-id → query-docs) for library docs
2. **WebSearch** for official documentation sites
3. **WebFetch** for specific documentation pages
4. **tavily** for comprehensive search when others fail

**WebFetch Restriction**: settings.json limits WebFetch to `github.com` and `raw.githubusercontent.com`. For non-GitHub documentation, use context7 or tavily instead. WebFetch is only effective for GitHub-hosted docs and READMEs.

#### Tier-Specific Delegation

**TRIVIAL**: Lead performs research directly. No researcher spawn. Query WebSearch with `"[library name] [version] official documentation"`. Read first authoritative result. Report: name, version status, key limitation. Total effort: 2-3 tool calls. If context7 is available, prefer `resolve-library-id` + `query-docs` over WebSearch for library-type dependencies.

**STANDARD**: Single researcher with full DPS template (above). Set `maxTurns: 25` explicitly to prevent premature termination on multi-dependency lists. Tool priority chain: context7 (structured, fastest) -> WebSearch (broad coverage) -> WebFetch (GitHub-specific pages) -> tavily (fallback broad search). Researcher handles 1-5 dependencies sequentially.

**COMPLEX**: Spawn 2-4 researchers with non-overlapping dependency lists. Split strategy:
- **By technology domain**: researcher-1 handles libraries/frameworks, researcher-2 handles APIs/protocols, researcher-3 handles infrastructure/tooling.
- **By dependency coupling**: If dependency X requires knowledge of dependency Y (e.g., a plugin that requires its host framework), assign both to the same researcher. Never split coupled dependencies across researchers.
- **Coordination**: Researchers run in parallel by default. If set B depends on set A findings (e.g., framework version determines compatible plugin versions), serialize: researcher-1 completes set A, Lead passes results to researcher-2 for set B. This is the exception, not the norm.
- Each researcher gets `maxTurns: 25` independently.

### 3. Validate Compatibility
For each dependency:
- Version compatibility with current environment
- API availability and stability
- License compatibility
- Known issues or deprecations

### 4. Synthesize Findings
For each researched topic:
- **Source**: URL or documentation reference
- **Key Facts**: Version, API surface, limitations
- **Impact on Architecture**: How this affects design decisions
- **Alternatives**: If issues found, what else could work

### 5. Report Confidence
Rate each finding by source reliability:
- Official docs → high confidence
- Community resources → medium confidence
- Inference/extrapolation → low confidence, flag for verification

## Decision Points

### Tool Priority Selection
- **context7 first** (default): Use for well-known libraries with structured docs (npm packages, popular frameworks). Fastest and most structured results.
- **WebSearch first**: Use when the dependency is a hosted service, API, or non-library technology (e.g., protocol specs, cloud services). context7 only covers library docs.
- **tavily first**: Use as escalation when context7 returns empty and WebSearch yields only tangential results. tavily provides broader search coverage at higher latency.

### Researcher Scope Division (COMPLEX)
- **By technology domain**: Split researchers by category -- libraries/frameworks vs APIs/protocols vs infrastructure/tooling. Use when dependencies span diverse technology types.
- **By criticality**: One researcher handles critical-path dependencies (blocking), another handles nice-to-have or optional dependencies. Use when time pressure requires prioritizing validation of blockers.

### Version Ambiguity Resolution
- **Pin to latest stable**: When architecture decisions specify a library without version, default to latest stable release and document the pinned version in findings.
- **Pin to codebase-compatible**: When existing codebase already uses a version of the dependency (from research-codebase findings), prefer the compatible version range unless architecture explicitly requires an upgrade.

### Confidence Threshold for Proceeding
- **Strict** (all high confidence): Require official documentation for every dependency. Use for production-critical or security-sensitive dependencies.
- **Pragmatic** (medium acceptable): Accept community resources for non-critical dependencies. Use when official docs are sparse or outdated but community consensus is strong.

### MCP Tool Availability Check
Before spawning researchers, Lead must verify which web tools are available in `settings.json` permissions. This affects the DPS tool priority chain:
- **Full stack available** (context7 + WebSearch + WebFetch + tavily): Use standard priority chain. This is the expected configuration.
- **No context7**: Remove context7 from DPS tool list. Researcher uses WebSearch as primary, tavily as secondary. Library documentation quality degrades -- flag findings as `confidence: medium` maximum for library-type dependencies.
- **No tavily**: Remove tavily from DPS tool list. Researcher uses context7 + WebSearch + WebFetch only. Acceptable for most cases; tavily is a fallback tool.
- **WebSearch-only**: Both MCP servers missing. Researcher limited to WebSearch + WebFetch (GitHub only). Add DPS constraint: "Focus on GitHub-hosted documentation. For non-GitHub libraries, report `status: unknown` with note 'MCP tools unavailable'."
- **Verification method**: Lead checks `settings.json` `permissions.allow[]` for `mcp__context7__*` and `mcp__tavily__*` entries before constructing DPS.

### Documentation Freshness Assessment
Researcher must assess documentation volatility for each dependency:
- **Stable** (major version >= 1.0, last release > 12 months ago): Architecture decisions can rely on this. Normal confidence rating.
- **Evolving** (major version >= 1.0, last release < 6 months ago): Acceptable but flag as `volatility: medium`. API surface likely stable but check for deprecation warnings.
- **Volatile** (major version < 1.0, or pre-release, or last release < 3 months ago): Flag as `volatility: high`. Architecture decisions based on volatile dependencies should be flagged in research-audit for re-validation before deployment. Include the specific version researched and the date of research in findings.
- **Unmaintained** (no release in > 24 months, archived repo): Flag as `volatility: critical`. Recommend alternative in findings. Route to design-architecture if this is a critical-path dependency.

### Multi-Researcher Coordination (COMPLEX)
When spawning multiple researchers, define explicit coordination protocol:
- **Default: Parallel execution**. Each researcher gets a non-overlapping dependency list. No inter-researcher communication needed. Lead collects all results after all researchers complete.
- **Exception: Serial with handoff**. When dependency set B requires knowledge from set A findings (e.g., framework version determines compatible middleware versions), researcher-1 completes set A first. Lead extracts relevant findings and includes them in researcher-2's DPS Context section as "Prior findings: [framework X] validated at version [Y], confirmed API [Z] available."
- **Researcher naming convention**: In COMPLEX DPS, name researchers by their domain for Lead tracking: "researcher-libs", "researcher-apis", "researcher-infra". This aids in result attribution during research-audit consolidation.
- **Conflict resolution**: If two researchers report conflicting information about the same technology (possible when domains overlap at boundaries), Lead flags the conflict and either: (a) spawns a third researcher to arbitrate, or (b) escalates to research-audit with both findings marked `confidence: conflicted`.

## Failure Handling
- **Web tools fail** (WebSearch/WebFetch/context7/tavily): Set per-dependency `status: issue`, note tool failure in L2
- **All research fails**: Set skill status to `partial`, forward gaps to research-audit for consolidation
- **Routing**: research-audit receives gaps and may recommend design revision if critical dependencies unvalidated
- **Pipeline impact**: Non-blocking. Unvalidated dependencies increase risk rating in research-audit

### Failure Severity Classification

| Failure | Severity | Blocking? | Lead Route |
|---------|----------|-----------|------------|
| All tools fail for critical dependency | HIGH | No (increases risk) | research-audit with `status: issue`, flag in plan-strategy risk section |
| Version incompatibility detected | HIGH | Conditional | design-architecture if incompatibility affects core component; otherwise research-audit with alternative recommendation |
| License incompatibility detected | HIGH | Yes | design-architecture for technology replacement decision |
| Only community sources found (no official docs) | MEDIUM | No | research-audit with `confidence: low`, note source quality in L2 |
| MCP tool not configured | LOW | No | Fall back to WebSearch-only chain; add DPS constraint about limited tool availability |
| Researcher runs out of turns (maxTurns hit) | MEDIUM | No | Check partial results; if >=50% dependencies covered, forward to research-audit as `status: partial`; if <50%, respawn with remaining list |

## Anti-Patterns

### DO NOT: Accept Blog Posts as Authoritative Sources
Community blog posts may be outdated or incorrect. Always prefer official documentation, release notes, or GitHub READMEs. If only blog sources exist, rate confidence as "low" and flag for verification.

### DO NOT: WebFetch Non-GitHub URLs
settings.json restricts WebFetch to `github.com` and `raw.githubusercontent.com`. Attempting other URLs wastes researcher turns with permission denials. Use context7 or tavily for non-GitHub documentation.

### DO NOT: Research Dependencies Not in Architecture Decisions
Scope creep wastes researcher turns. Only research dependencies explicitly listed in architecture decisions or interface definitions. If a researcher discovers an unlisted transitive dependency, note it but don't deep-dive.

### DO NOT: Skip Version Compatibility Checks
Finding that a library exists is insufficient. Every dependency must have version compatibility confirmed against the target environment. An incompatible version is worse than no finding.

### DO NOT: Report "Unknown" Without Exhausting All Tools
Before marking a dependency as `status: unknown`, the researcher must have tried all 4 tools in priority order (context7, WebSearch, WebFetch, tavily). Premature "unknown" creates false gaps in research-audit.

### DO NOT: Deep-Dive Transitive Dependencies
If library A depends on library B, only research A (the direct dependency). Researching B is scope creep unless the architecture explicitly references B as a direct integration point. Transitive dependencies are the library maintainer's responsibility. If a researcher discovers a transitive dependency with a known critical vulnerability, note it as a one-line advisory in findings but do not spend turns investigating.

### DO NOT: Conflate Popularity with Quality
A library with 50K GitHub stars may still have critical issues. Researcher must check: last release date, open critical issues count, and maintenance status -- not just star count or download numbers. A well-maintained library with 500 stars and active releases is preferable to an abandoned library with 50K stars. Include maintenance health indicators in the L2 findings for each dependency.

## Tool Capability Reference

| Tool | Best For | Limitations | Settings Restriction |
|------|----------|-------------|----------------------|
| context7 (`resolve-library-id` + `query-docs`) | Library docs (npm, PyPI, popular frameworks). Structured output. | Only covers indexed libraries. Niche or enterprise-internal libraries return empty. | Requires `mcp__context7__*` in `permissions.allow[]` |
| WebSearch | General search, official sites, blog posts, release announcements. | Results may not be authoritative. Ranking can surface SEO-optimized but low-quality content. | Always available (native tool) |
| WebFetch | Specific page content extraction from known URLs. | Domain restricted to `github.com` and `raw.githubusercontent.com` per `settings.json`. | Allowlist in `permissions.allow[]` |
| tavily (`search`) | Broad search with AI-enhanced result summarization. Good for comparison queries. | Higher latency than WebSearch. May duplicate WebSearch results. Best as fallback. | Requires `mcp__tavily__search` in `permissions.allow[]` |

**Tool selection heuristic for DPS construction**:
- Library/framework dependency -> context7 first (structured docs)
- Cloud API/service dependency -> WebSearch first (official service docs not in context7)
- GitHub-hosted project -> WebFetch for README.md, CHANGELOG.md directly
- "Which library is best for X?" comparative query -> tavily first (AI-enhanced comparison)

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| design-architecture | Technology choices and library references | L1 YAML: `components[]` with technology dependencies, L2: ADRs with external references |
| design-interface | API contracts referencing external services | L1 YAML: `interfaces[]` with external endpoints, L2: protocol specifications |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| research-audit | External findings for gap analysis | Always (external -> audit consolidation) |
| plan-strategy | External constraints for sequencing | Via research-audit output |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Web tools fail | research-audit | Per-dependency `status: issue` with tool failure details |
| All research fails | research-audit | Partial results with `status: partial` and gap list |
| Critical dependency unvalidated | design-architecture | Dependency details requiring architecture revision |

## Quality Gate
- Every external dependency has >=1 documented source (official docs preferred, community acceptable with confidence downgrade)
- Version compatibility confirmed for all libraries against target environment
- No undocumented assumptions about external APIs (every API behavior claim has a source URL)
- Sources cited with full URLs (not just domain names -- direct links to specific documentation pages)
- License compatibility verified for all libraries (MIT/Apache/BSD compatible with project; GPL flagged for review)
- Tool chain documented: each finding notes which tool produced it (context7, WebSearch, WebFetch, or tavily) for reproducibility and audit

## Output

### L1
```yaml
domain: research
skill: external
dependency_count: 0
validated: 0
issues: 0
dependencies:
  - name: ""
    version: ""
    status: validated|issue|unknown
    source: ""
```

### L2
Structured markdown report containing:

#### Dependency Validation Matrix
For each dependency, a row with:
- **Name**: Library/API/service name as referenced in architecture
- **Version**: Pinned version researched (or range if architecture specifies range)
- **Status**: `validated` | `issue` | `unknown`
- **Confidence**: `high` (official docs) | `medium` (community) | `low` (inference) | `conflicted` (researcher disagreement)
- **Volatility**: `stable` | `evolving` | `volatile` | `critical` (unmaintained)
- **Source URL**: Direct link to documentation page (not domain-level)
- **Tool Used**: Which tool produced this finding (context7/WebSearch/WebFetch/tavily)
- **License**: SPDX identifier (e.g., MIT, Apache-2.0, GPL-3.0)

#### Compatibility Analysis
Per-dependency narrative including:
- Version compatibility with target environment (runtime, build tools, OS)
- API stability assessment (GA, beta, deprecated endpoints)
- Known breaking changes between current and researched version
- Maintenance health: last release date, open critical issues, contributor activity

#### Alternatives Section (conditional)
For dependencies with `status: issue` or `volatility: critical`:
- Alternative library/service name
- Brief comparison (pros/cons vs original choice)
- Migration effort estimate (trivial/moderate/significant)

#### Research Gaps (conditional)
For dependencies with `status: unknown`:
- Tools attempted and results (e.g., "context7: library not indexed, WebSearch: no official docs found")
- Recommended next steps (e.g., "contact vendor directly", "check internal documentation")
- Risk assessment if proceeding without validation
