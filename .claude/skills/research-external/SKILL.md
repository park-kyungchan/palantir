---
name: research-external
description: >-
  Collects community patterns via tavily MCP and WebSearch. Filters
  for verified and reproducible information, cross-references
  with official docs. Tags CC-native behavioral claims from
  community sources for shift-left verification. Parallel with
  research-codebase. Use after design domain complete when
  technology choices, API contracts, and risk areas needing
  validation are defined. Reads from design-architecture technology
  choices, design-interface API contracts, and design-risk risk
  areas. Produces community pattern matrix with source URLs for
  audit skills, plus CC-native claims for research-cc-verify gate.
  Requires general-purpose subagent_type for MCP ToolSearch access.
  On FAIL (MCP unavailable or no verified results), pauses for MCP
  health check. NO_FALLBACK: never substitute WebSearch for MCP tools.
  DPS needs design-architecture technology choices, design-risk risk
  areas. Exclude internal codebase patterns (research-codebase handles those).
user-invocable: true
disable-model-invocation: true
---

# Research — External

## Execution Model
- **TRIVIAL**: Lead-direct. Quick web search for one library/API.
- **STANDARD**: Spawn researcher (has web access). Systematic documentation research.
- **COMPLEX**: Spawn 2-4 researchers. Each covers non-overlapping external topics.

> Phase-aware routing and compaction survival: read `.claude/resources/phase-aware-execution.md`

## Methodology

### 1. Extract Technical Decisions Needing Community Validation
From architecture decisions, list items needing community-sourced evidence:
- Technology choices with known community discussion activity
- Implementation patterns where practical experience differs from official docs
- Known constraints or workarounds not documented officially
- Post-Opus-4.6 behavioral changes reported by community

### 2. Search Community Discussions
For STANDARD/COMPLEX tiers, construct delegation DPS with:
- **Context** (D11): INCLUDE technology choices and risk areas from design domain, specific research questions per dependency. EXCLUDE internal codebase patterns, pre-design history, rejected alternatives. Budget ≤ 30% effective context.
- **Task**: "Search post-Opus-4.6 community discussions for [assigned topic list]. For each topic: find GitHub Issues/Discussions with verified solutions, search forums for practical patterns and workarounds, identify constraints not in official docs, check for post-release behavioral changes."
- **Constraints**: Web-enabled research only (WebSearch, WebFetch, tavily). No file modifications. Cite all sources with full URLs. Prioritize verified/reproducible findings. `maxTurns: 25`.
- **Output**: Per-topic — topic, pattern found, verification status (verified/anecdotal/unconfirmed), source URL, practical impact, confidence rating.
- **Delivery**: Ch2: write to `{work_dir}/p2-external.md`. Ch3 micro-signal to Lead: `"PASS|validated:{count}|ref:{work_dir}/p2-external.md"`.

Priority order: 1. **WebSearch** (GitHub Issues/Discussions) → 2. **tavily** (broader forum search) → 3. **WebFetch** (specific GitHub thread extraction).

**WebFetch Restriction**: `settings.json` limits WebFetch to `github.com` and `raw.githubusercontent.com`. Use tavily for non-GitHub content.

> Tier-specific delegation templates (TRIVIAL/STANDARD/COMPLEX), tool selection heuristic: read `resources/methodology.md`

### 3. Filter for Verified/Reproducible Information
For each community finding, apply verification filter:
- **Verified**: Multiple independent reports confirming same behavior/pattern
- **Reproducible**: Steps or conditions clearly documented, can be tested
- **Anecdotal**: Single report without confirmation — include with `confidence: low`

### 4. Cross-Reference with CC-Feasibility Findings
Compare community findings against official documentation from pre-design-feasibility:
- Community contradicts official docs → flag as potential undocumented behavior
- Community confirms official docs → increase confidence
- Community adds info not in official docs → flag as community-only knowledge

### 5. Synthesize Practical Patterns
For each validated community finding record: source URL, pattern discovered, verification status, practical impact, version context (which version/date applies).

### 5.5. Tag CC-Native Behavioral Claims
Community CC-native claims (CC runtime behavior, agent teams mechanics, hook behaviors, context management) require **extra scrutiny** — posts may describe older CC versions, different configurations, or conflate CC with general Claude behavior.

Tagging protocol for each CC-native behavioral claim from community sources:
- Apply `[CC-CLAIM]` tag with claim text, category, source URL, and publication date
- **Confidence downgrade**: community-sourced CC claims start at `confidence: low` until verified
- **Version context**: note which CC version the claim was reportedly observed on
- Tagged claims join research-codebase claims in the research-cc-verify verification pipeline

## Decision Points

### Tool Priority Selection
- **context7 first**: well-known libraries with structured docs (npm packages, popular frameworks) — fastest and most structured
- **WebSearch first**: hosted service, API, or non-library technology (protocol specs, cloud services) — context7 only covers library docs
- **tavily first**: escalation when context7 returns empty and WebSearch yields only tangential results

### Researcher Scope Division (COMPLEX)
- **By technology domain**: libraries/frameworks vs APIs/protocols vs infrastructure/tooling — use when dependencies span diverse types
- **By criticality**: critical-path (blocking) vs nice-to-have — use when time pressure requires prioritizing blockers

### MCP Tool Availability Check
Before spawning researchers, verify which tools are available in `settings.json` permissions:
- **Full stack** (context7 + WebSearch + WebFetch + tavily): use standard priority chain
- **No context7**: WebSearch as primary, tavily as secondary; max confidence `medium` for library-type deps
- **No tavily**: context7 + WebSearch + WebFetch only — acceptable for most cases
- **WebSearch-only**: add DPS constraint "Focus on GitHub-hosted docs; report `status: unknown` for non-GitHub libraries"

> Version ambiguity resolution, confidence thresholds: read `resources/methodology.md`
> Documentation freshness assessment, multi-researcher coordination: read `resources/methodology.md`

## Failure Handling

| Failure Type | Level | Action |
|---|---|---|
| MCP tool error, timeout, single dependency fails | L0 Retry | Re-invoke same researcher, same dependency list |
| Incomplete research or off-topic findings | L1 Nudge | Respawn with refined DPS targeting dependency scope or narrower questions |
| Researcher exhausted turns or context polluted | L2 Respawn | Kill → fresh researcher with remaining dependency list |
| MCP unavailable, tool chain broken for critical dependency | L3 Restructure | Split by tool availability, serialize with fallback constraints |
| 3+ L2 failures or critical dependency unvalidatable | L4 Escalate | AskUserQuestion with gap summary and options |

- **Web tools fail**: set per-dependency `status: issue`, note tool failure in L2; forward to audit-* skills
- **All research fails**: set skill status to `partial`, forward gaps to research-audit for consolidation

> Escalation ladder details: read `.claude/resources/failure-escalation-ladder.md`
> Failure severity classification table: read `resources/methodology.md`

## Anti-Patterns

- **Blog posts as authoritative**: prefer official docs, release notes, or GitHub READMEs; blog-only findings = `confidence: low`
- **WebFetch non-GitHub URLs**: settings.json restricts to `github.com` and `raw.githubusercontent.com` — use context7/tavily for other domains
- **Scope creep on unlisted deps**: only research dependencies in architecture decisions; note transitive deps as one-line advisory, no deep-dive
- **Existence without version**: confirm version compatibility against target environment — incompatible version is worse than no finding
- **Premature `status: unknown`**: exhaust all 4 tools in priority order before marking unknown
- **Deep-diving transitive dependencies**: transitive deps are the library maintainer's responsibility; if critical vulnerability found, note as one-line advisory only
- **Popularity over quality**: check last release date, open critical issues, contributor activity — not just star count or download numbers

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| design-architecture | Technology choices and library references | L1 YAML: `components[]` with tech deps, L2: ADRs with external references |
| design-interface | API contracts referencing external services | L1 YAML: `interfaces[]` with external endpoints, L2: protocol specs |
| design-risk | Risk areas needing external validation | L1 YAML: `risk_areas[]` with severity, L2: external risk factors |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| audit-static | Community dependency constraints | Always (Wave 1 → Wave 2 parallel audits) |
| audit-behavioral | Community behavioral workarounds | Always (Wave 1 → Wave 2 parallel audits) |
| audit-relational | Community relationship patterns | Always (Wave 1 → Wave 2 parallel audits) |
| audit-impact | Community change propagation findings | Always (Wave 1 → Wave 2 parallel audits) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Web tools fail | audit-* (all 4) | Per-topic `status: issue` with tool failure details |
| All research fails | audit-* (all 4) | Partial results with `status: partial` and gap list |
| Critical pattern unvalidated | design-architecture | Pattern details requiring architecture revision |

> D17 Note: Two-Channel protocol — Ch2 output file in work directory, Ch3 micro-signal to Lead.
> Micro-signal format: read `.claude/resources/output-micro-signal-format.md`

## Quality Gate
- Every external dependency has ≥1 documented source (official docs preferred, community acceptable with confidence downgrade)
- Version compatibility confirmed for all libraries against target environment
- No undocumented assumptions about external APIs — every API behavior claim has a source URL
- Sources cited with full URLs (direct links to specific documentation pages)
- License compatibility verified for all libraries (MIT/Apache/BSD compatible; GPL flagged for review)
- Tool chain documented: each finding notes which tool produced it (context7/WebSearch/WebFetch/tavily)
- CC-native behavioral claims tagged with [CC-CLAIM] and source-attributed (if any discovered)

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
cc_native_claims: 0
pt_signal: "metadata.phase_signals.p2_research"
signal_format: "PASS|validated:{count}|cc_claims:{n}|ref:{work_dir}/p2-external.md"
```

### L2
> Dependency Validation Matrix, Compatibility Analysis, Alternatives, Research Gaps, CC-Native Claims spec: read `resources/methodology.md`
