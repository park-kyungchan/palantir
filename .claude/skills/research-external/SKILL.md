---
name: research-external
description: |
  [P3·Research·External] External documentation researcher. Fetches and synthesizes documentation from web sources, official docs, and package registries using WebSearch, WebFetch, context7, and tavily tools.

  WHEN: design domain complete. Architecture decisions reference external libraries, APIs, or patterns needing documentation validation.
  DOMAIN: research (skill 2 of 3). Parallel-capable: codebase ∥ external → audit.
  INPUT_FROM: design domain (technology choices, library references needing doc validation).
  OUTPUT_TO: research-audit (external findings for gap analysis), plan-strategy (external constraints for implementation strategy).

  METHODOLOGY: (1) Extract external dependencies from architecture decisions, (2) Search official docs via WebSearch/context7, (3) Fetch and analyze key pages via WebFetch, (4) Verify version compatibility and API availability, (5) Synthesize into structured findings with source links.
  MAX_TEAMMATES: 4. Each researcher handles non-overlapping external topics.
  OUTPUT_FORMAT: L1 YAML dependency validation matrix, L2 markdown documentation summary with source URLs, L3 detailed API analysis.
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
Priority order for each dependency:
1. **context7** (resolve-library-id → query-docs) for library docs
2. **WebSearch** for official documentation sites
3. **WebFetch** for specific documentation pages
4. **tavily** for comprehensive search when others fail

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

## Quality Gate
- Every external dependency has ≥1 documented source
- Version compatibility confirmed for all libraries
- No undocumented assumptions about external APIs
- Sources cited with URLs

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
- Dependency validation matrix with source URLs
- Compatibility analysis per dependency
- Alternatives for problematic dependencies
