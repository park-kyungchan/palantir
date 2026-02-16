---
name: research-external
description: |
  [P2·Research·External] Collects community patterns via WebSearch/tavily. Filters for verified/reproducible information, cross-references with official docs. Parallel with research-codebase.

  WHEN: Design domain complete. Parallel with research-codebase.
  DOMAIN: research (skill 2 of 3).
  INPUT_FROM: design-architecture (technology choices), design-interface (API contracts), design-risk (risk areas needing validation).
  OUTPUT_TO: audit-static, audit-behavioral, audit-relational, audit-impact (community pattern matrix, report with source URLs).

  METHODOLOGY: (1) Identify external validation needs, (2) Search official docs + community, (3) Filter for verified/reproducible info, (4) Cross-reference with cc-feasibility, (5) Produce sourced pattern matrix.
  OUTPUT_FORMAT: L1 YAML (community pattern matrix), L2 pattern report with source URLs.
user-invocable: true
disable-model-invocation: false
---

# Research — External

## Execution Model
- **TRIVIAL**: Lead-direct. Quick web search for one library/API.
- **STANDARD**: Spawn researcher (has web access). Systematic documentation research.
- **COMPLEX**: Spawn 2-4 researchers. Each covers non-overlapping external topics.

## Methodology

### 1. Extract Technical Decisions Needing Community Validation
From architecture decisions, list items needing community-sourced evidence:
- Technology choices with known community discussion activity
- Implementation patterns where practical experience differs from official docs
- Known constraints or workarounds not documented officially
- Post-Opus-4.6 behavioral changes reported by community

### 2. Search Community Discussions
For STANDARD/COMPLEX tiers, construct the delegation prompt for each researcher with:
- **Context**: Paste the technical decisions list from Step 1 with specific questions needing community validation. Include design-architecture L1 `components[]` and relevant ADRs.
- **Task**: "Search post-Opus-4.6 community discussions for [assigned topic list]. For each topic: (1) find GitHub Issues/Discussions with verified solutions, (2) search forums for practical patterns and workarounds, (3) identify known constraints not in official docs, (4) check for post-release behavioral changes. Use WebSearch first for GitHub Issues, tavily for broader forum coverage, WebFetch for specific GitHub threads."
- **Scope**: Explicit list of topics assigned to this researcher. For COMPLEX, split by technology domain.
- **Constraints**: Web-enabled research only (WebSearch, WebFetch, tavily). No file modifications. Cite all sources with full URLs. Prioritize verified/reproducible findings.
- **Expected Output**: Per-topic entry: topic, pattern found, verification status (verified/anecdotal/unconfirmed), source URL, practical impact, confidence rating.
- **Delivery**: Upon completion, send L1 summary to Lead via SendMessage. Include: status (PASS/FAIL), files changed count, key metrics. L2 detail stays in agent context.

Priority order for community research:
1. **WebSearch** for GitHub Issues/Discussions (most targeted)
2. **tavily** for broader forum and community search
3. **WebFetch** for specific GitHub thread content extraction

**WebFetch Restriction**: settings.json limits WebFetch to `github.com` and `raw.githubusercontent.com`. For non-GitHub content, use tavily instead.

#### Tier-Specific Delegation

**TRIVIAL**: Lead performs research directly. No researcher spawn. Query WebSearch with `"[library name] [version] official documentation"`. Read first authoritative result. Report: name, version status, key limitation. Total effort: 2-3 tool calls. If context7 is available, prefer `resolve-library-id` + `query-docs` over WebSearch for library-type dependencies.

**STANDARD**: Single researcher with full DPS template (above). Set `maxTurns: 25` explicitly to prevent premature termination on multi-dependency lists. Tool priority chain: context7 (structured, fastest) -> WebSearch (broad coverage) -> WebFetch (GitHub-specific pages) -> tavily (fallback broad search). Researcher handles 1-5 dependencies sequentially.

**COMPLEX**: Spawn 2-4 researchers with non-overlapping dependency lists. Split strategy:
- **By technology domain**: researcher-1 handles libraries/frameworks, researcher-2 handles APIs/protocols, researcher-3 handles infrastructure/tooling.
- **By dependency coupling**: If dependency X requires knowledge of dependency Y (e.g., a plugin that requires its host framework), assign both to the same researcher. Never split coupled dependencies across researchers.
- **Coordination**: Researchers run in parallel by default. If set B depends on set A findings (e.g., framework version determines compatible plugin versions), serialize: researcher-1 completes set A, Lead passes results to researcher-2 for set B. This is the exception, not the norm.
- Each researcher gets `maxTurns: 25` independently.

### 3. Filter for Verified/Reproducible Information
For each community finding, apply verification filter:
- **Verified**: Multiple independent reports confirming the same behavior/pattern
- **Reproducible**: Steps or conditions clearly documented, can be tested
- **Anecdotal**: Single report without confirmation -- include with low confidence flag
- Discard purely speculative or opinion-based content

### 4. Cross-Reference with CC-Feasibility Findings
Compare community findings against official documentation from pre-design-feasibility:
- Where community contradicts official docs, flag as potential undocumented behavior
- Where community confirms official docs, increase confidence
- Where community adds information not in official docs, flag as community-only knowledge
- Note the date and version context of community discussions

### 5. Synthesize Practical Patterns
For each validated community finding:
- **Source**: Full URL to discussion/issue thread
- **Pattern**: What the community discovered or recommends
- **Verification Status**: verified/reproducible/anecdotal
- **Practical Impact**: How this affects implementation approach
- **Version Context**: Which version/date the finding applies to

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

## Phase-Aware Execution

This skill runs in P2+ Team mode only. Agent Teams coordination applies:
- **Communication**: Use SendMessage for result delivery to Lead. Write large outputs to disk.
- **Task tracking**: Update task status via TaskUpdate after completion.
- **No shared memory**: Insights exist only in your context. Explicitly communicate findings.
- **File ownership**: Only modify files assigned to you. No overlapping edits with parallel agents.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| design-architecture | Technology choices and library references | L1 YAML: `components[]` with technology dependencies, L2: ADRs with external references |
| design-interface | API contracts referencing external services | L1 YAML: `interfaces[]` with external endpoints, L2: protocol specifications |
| design-risk | Risk areas needing external validation | L1 YAML: `risk_areas[]` with severity, L2: external risk factors and validation priorities |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| audit-static | Community dependency constraints | Always (Wave 1 -> Wave 2 parallel audits) |
| audit-behavioral | Community behavioral workarounds | Always (Wave 1 -> Wave 2 parallel audits) |
| audit-relational | Community relationship patterns | Always (Wave 1 -> Wave 2 parallel audits) |
| audit-impact | Community change propagation findings | Always (Wave 1 -> Wave 2 parallel audits) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Web tools fail | audit-* (all 4 audits) | Per-topic `status: issue` with tool failure details |
| All research fails | audit-* (all 4 audits) | Partial results with `status: partial` and gap list |
| Critical pattern unvalidated | design-architecture | Pattern details requiring architecture revision |

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
