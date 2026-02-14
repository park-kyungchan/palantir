---
name: pre-design-brainstorm
description: |
  [P0-1·PreDesign·Brainstorm] Initial requirement gathering through structured user interaction. Asks clarifying questions via AskUserQuestion to extract feature scope, constraints, success criteria, and edge cases. First skill invoked in any new pipeline.

  WHEN: Starting a new feature or task. User says "build X", "add Y", or has unclear requirements needing structured extraction. No prerequisites — pipeline entry point.
  DOMAIN: pre-design (skill 1 of 3). Sequential: brainstorm → validate → feasibility.
  INPUT_FROM: User request (raw, unstructured).
  OUTPUT_TO: pre-design-validate (structured requirements document).

  METHODOLOGY: (1) Parse user request for explicit and implicit requirements, (2) Categorize unknowns into scope/constraints/criteria/edge-cases, (3) Generate 3-6 clarifying questions via AskUserQuestion, (4) Synthesize answers into structured requirement document, (5) Identify remaining ambiguities for follow-up round.
  TIER_BEHAVIOR: TRIVIAL=Lead-only, STANDARD=1-2 analysts, COMPLEX=2-4 analysts.
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

## Execution Model
- **TRIVIAL**: Lead-direct. Parse request, ask 2-3 questions via AskUserQuestion, synthesize.
- **STANDARD**: Spawn 1-2 analysts. Each covers separate requirement dimensions.
- **COMPLEX**: Spawn 2-4 analysts. Divide: scope, constraints, integration, edge-cases.

## Methodology

### 1. Parse User Request
Extract explicit and implicit requirements from user input.
- Explicit: "must", "should", "need" statements
- Implicit: unstated assumptions about environment, scale, constraints

### 2. Categorize Unknowns
Map gaps to 4 dimensions:

| Dimension | Question Type | Example |
|-----------|--------------|---------|
| Scope | What's included/excluded? | "Should this affect existing X?" |
| Constraints | Technical/resource limits? | "Max file count? Performance target?" |
| Criteria | How to measure success? | "What defines done?" |
| Edge Cases | What could go wrong? | "What if Y fails mid-process?" |

### 3. Ask Clarifying Questions
Use AskUserQuestion with 3-6 questions grouped by dimension.
Max 3 question rounds before proceeding with best-effort synthesis.
After each round, merge answers into evolving requirement document.

### 4. Classify Tier
Based on gathered requirements:
- TRIVIAL: ≤2 files, single module, clear scope
- STANDARD: 3-8 files, 1-2 modules
- COMPLEX: >8 files, 3+ modules, cross-cutting concerns

### 5. Synthesize Requirements Document
Combine all gathered information into structured output.
Flag unresolved items as open questions with rationale.

## Quality Gate
- All 4 dimensions have ≥1 requirement
- No circular or contradictory requirements
- Tier classification has evidence (file count, module estimate)
- Open questions have clear rationale for deferral

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
