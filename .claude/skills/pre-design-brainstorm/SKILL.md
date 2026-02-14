---
name: pre-design-brainstorm
description: |
  [P0-1·PreDesign·Brainstorm] Initial requirement gathering through structured user interaction. Asks clarifying questions via AskUserQuestion to extract feature scope, constraints, success criteria, and edge cases. First skill invoked in any new pipeline.

  WHEN: Starting a new feature or task. User says "build X", "add Y", or has unclear requirements needing structured extraction. No prerequisites — pipeline entry point.
  DOMAIN: pre-design (skill 1 of 3). Sequential: brainstorm → validate → feasibility.
  INPUT_FROM: User request (raw, unstructured).
  OUTPUT_TO: pre-design-validate (structured requirements document).

  METHODOLOGY: (1) Parse user request for explicit and implicit requirements, (2) Categorize unknowns into scope/constraints/criteria/edge-cases, (3) Generate 3-6 clarifying questions via AskUserQuestion, (4) Synthesize answers into structured requirement document, (5) Identify remaining ambiguities for follow-up round.
  TIER_BEHAVIOR: TRIVIAL=Lead-only, STANDARD=1-2 agents, COMPLEX=coordinator+3 workers.
  MAX_TEAMMATES: 4. RETRY_LIMIT: 3 question rounds before proceeding with best-effort.
  OUTPUT_FORMAT: L1 YAML requirement list with categories, L2 markdown requirement document with rationale and open questions.
user-invocable: true
disable-model-invocation: true
input_schema:
  type: object
  properties:
    topic:
      type: string
      description: "Feature or task to brainstorm"
    tier:
      type: string
      enum: ["trivial", "standard", "complex", "auto"]
      description: "Pipeline tier (default: auto-detect)"
  required:
    - topic
---

# Pre-Design — Brainstorm

## Output

### L1
```yaml
domain: pre-design
skill: brainstorm
tier: auto
status: complete|needs-followup
requirement_count: 0
open_questions: 0
```

### L2
- Requirements by category (scope, constraints, criteria, edge-cases)
- Open questions with rationale
- Tier classification with evidence
