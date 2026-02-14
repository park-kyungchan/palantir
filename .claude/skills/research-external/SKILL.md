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
input_schema:
  type: object
  properties:
    focus:
      type: string
      description: "Specific library, API, or topic to research externally"
  required: []
---

# Research — External

## Output

### L1
```yaml
domain: research
skill: external
dependency_count: 0
validated: 0
unvalidated: 0
dependencies:
  - name: ""
    version: ""
    status: validated|unvalidated|incompatible
    source: ""
```

### L2
- Dependency validation matrix with source URLs
- Version compatibility analysis
- API availability and limitations
