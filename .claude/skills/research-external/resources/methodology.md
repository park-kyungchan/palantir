# Research External — Detailed Methodology

> On-demand reference. Contains tier-specific delegation templates, tool capability reference, decision point details, failure severity classification, and output L2 spec.

## Tier-Specific Delegation Templates

### TRIVIAL — Lead Performs Research Directly
No researcher spawn. Query WebSearch with `"[library name] [version] official documentation"`. Read first authoritative result. Report: name, version status, key limitation. Total effort: 2-3 tool calls. If context7 is available, prefer `resolve-library-id` + `query-docs` over WebSearch for library-type dependencies.

### STANDARD — Single Researcher
```
Context: [Technical decisions list with specific validation questions]
  INCLUDE: Technology choices and risk areas from design domain. Questions per dependency.
  EXCLUDE: Internal codebase patterns. Pre-design history. Rejected alternatives.
  Budget: Context field ≤ 30% of effective context budget.
Task: Search post-Opus-4.6 community discussions for [assigned topic list]. For each topic:
  (1) find GitHub Issues/Discussions with verified solutions,
  (2) search forums for practical patterns and workarounds,
  (3) identify known constraints not in official docs,
  (4) check for post-release behavioral changes.
  Use WebSearch first for GitHub Issues, tavily for broader forum coverage,
  WebFetch for specific GitHub threads.
Constraints: Web-enabled research only. No file modifications. Cite all sources with full URLs.
  Prioritize verified/reproducible findings. maxTurns: 25.
Expected Output: Per-topic entry: topic, pattern found, verification status, source URL,
  practical impact, confidence rating.
Delivery: Write to tasks/{team}/p2-external.md. Send micro-signal to Lead:
  "PASS|validated:{count}|ref:tasks/{team}/p2-external.md".
```

### COMPLEX — 2-4 Researchers with Non-Overlapping Lists
Split strategy:
- **By technology domain**: researcher-1 handles libraries/frameworks, researcher-2 handles APIs/protocols, researcher-3 handles infrastructure/tooling.
- **By dependency coupling**: If dependency X requires knowledge of dependency Y, assign both to the same researcher. Never split coupled dependencies.
- **Coordination default**: Parallel execution. Exception: if set B depends on set A (e.g., framework version determines compatible plugin versions), serialize — researcher-1 completes, Lead passes results to researcher-2.
- Each researcher gets `maxTurns: 25` independently.
- **Naming convention**: Name by domain for attribution — "researcher-libs", "researcher-apis", "researcher-infra".
- **Conflict resolution**: If researchers report conflicting info on the same technology, spawn a third researcher to arbitrate, or escalate to research-audit with both findings marked `confidence: conflicted`.

## Tool Capability Reference

| Tool | Best For | Limitations | Settings Restriction |
|------|----------|-------------|----------------------|
| context7 (`resolve-library-id` + `query-docs`) | Library docs (npm, PyPI, popular frameworks). Structured output. | Only covers indexed libraries. Niche or enterprise-internal returns empty. | Requires `mcp__context7__*` in `permissions.allow[]` |
| WebSearch | General search, official sites, blog posts, release announcements. | Results may not be authoritative. SEO-optimized low-quality content possible. | Always available (native tool) |
| WebFetch | Specific page content from known URLs. GitHub README/CHANGELOG extraction. | Domain restricted to `github.com` and `raw.githubusercontent.com`. | Allowlist in `permissions.allow[]` |
| tavily (`search`) | Broad search with AI-enhanced summarization. Good for comparison queries. | Higher latency. May duplicate WebSearch. Best as fallback. | Requires `mcp__tavily__search` in `permissions.allow[]` |

**Tool selection heuristic for DPS construction**:
- Library/framework dependency → context7 first (structured docs)
- Cloud API/service → WebSearch first (official service docs not in context7)
- GitHub-hosted project → WebFetch for README.md, CHANGELOG.md directly
- "Which library is best for X?" comparison → tavily first (AI-enhanced comparison)

## Version Ambiguity Resolution

- **Pin to latest stable**: When architecture specifies library without version, default to latest stable, document in findings.
- **Pin to codebase-compatible**: When existing codebase uses a version (from research-codebase findings), prefer compatible range unless architecture explicitly requires upgrade.

## Confidence Threshold for Proceeding

- **Strict (all high confidence)**: Require official documentation for every dependency. Use for production-critical or security-sensitive.
- **Pragmatic (medium acceptable)**: Accept community resources for non-critical dependencies. Use when official docs are sparse but community consensus is strong.

## Documentation Freshness Assessment

| Status | Condition | Action |
|--------|-----------|--------|
| Stable | Major version ≥ 1.0, last release > 12 months | Normal confidence. Architecture decisions can rely on this. |
| Evolving | Major version ≥ 1.0, last release < 6 months | Flag `volatility: medium`. API stable but check for deprecation warnings. |
| Volatile | Major version < 1.0, or pre-release, or last release < 3 months | Flag `volatility: high`. Include specific version researched and research date. |
| Unmaintained | No release > 24 months, archived repo | Flag `volatility: critical`. Recommend alternative. Route to design-architecture if critical-path. |

## Failure Severity Classification

| Failure | Severity | Blocking? | Lead Route |
|---------|----------|-----------|------------|
| All tools fail for critical dependency | HIGH | No (increases risk) | research-audit with `status: issue` |
| Version incompatibility detected | HIGH | Conditional | design-architecture if core component; otherwise research-audit with alternative |
| License incompatibility detected | HIGH | Yes | design-architecture for technology replacement |
| Only community sources found | MEDIUM | No | research-audit with `confidence: low` |
| MCP tool not configured | LOW | No | Fall back to WebSearch-only; add DPS constraint |
| Researcher runs out of turns | MEDIUM | No | If ≥50% covered → forward as partial; if <50% → respawn with remaining list |

## Output L2 Detailed Spec

### Dependency Validation Matrix
Per-dependency row with:
- **Name**: Library/API/service name as referenced in architecture
- **Version**: Pinned version researched (or range if specified)
- **Status**: `validated` | `issue` | `unknown`
- **Confidence**: `high` (official docs) | `medium` (community) | `low` (inference) | `conflicted`
- **Volatility**: `stable` | `evolving` | `volatile` | `critical` (unmaintained)
- **Source URL**: Direct link to documentation page (not domain-level)
- **Tool Used**: Which tool produced this finding (context7/WebSearch/WebFetch/tavily)
- **License**: SPDX identifier (e.g., MIT, Apache-2.0, GPL-3.0)

### Compatibility Analysis
Per dependency:
- Version compatibility with target environment (runtime, build tools, OS)
- API stability assessment (GA, beta, deprecated endpoints)
- Known breaking changes between current and researched version
- Maintenance health: last release date, open critical issues, contributor activity

### Alternatives Section (conditional — `status: issue` or `volatility: critical`)
- Alternative library/service name
- Brief comparison (pros/cons vs original choice)
- Migration effort estimate (trivial/moderate/significant)

### Research Gaps (conditional — `status: unknown`)
- Tools attempted and results (e.g., "context7: not indexed, WebSearch: no official docs")
- Recommended next steps (e.g., "contact vendor directly", "check internal documentation")
- Risk assessment if proceeding without validation

### CC-Native Claims Section (conditional)
- Claim text with [CC-CLAIM] tag
- Source URL and publication date
- CC version context (if mentioned)
- Confidence: low (pending research-cc-verify)
