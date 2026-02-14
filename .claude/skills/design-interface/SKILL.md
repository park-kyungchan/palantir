---
name: design-interface
description: |
  [P2·Design·Interface] API contracts and integration point designer. Defines precise interfaces between components: function signatures, data types, protocols, and error contracts for all component boundaries.

  WHEN: After design-architecture produces component structure. Components exist but interfaces undefined.
  DOMAIN: design (skill 2 of 3). Can run in parallel with design-risk after architecture completes.
  INPUT_FROM: design-architecture (component structure, module boundaries).
  OUTPUT_TO: design-risk (interfaces for risk assessment), plan-interface (interface specs for implementation planning).

  METHODOLOGY: (1) Read component structure from architecture output, (2) For each component boundary: define input/output types, (3) Define communication protocols (sync/async, message format), (4) Specify error contracts (error types, propagation rules), (5) Document integration points with sequence diagrams.
  MAX_TEAMMATES: 4.
  OUTPUT_FORMAT: L1 YAML interface registry with types, L2 markdown interface specification with examples, L3 detailed type definitions and sequence diagrams.
user-invocable: true
disable-model-invocation: false
---

# Design — Interface

## Output

### L1
```yaml
domain: design
skill: interface
interface_count: 0
integration_points: 0
interfaces:
  - boundary: ""
    input_type: ""
    output_type: ""
    protocol: sync|async
```

### L2
- Interface specifications per component boundary
- Error contracts and propagation rules
- Integration point documentation
