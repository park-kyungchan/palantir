---
name: pre-design-brainstorm
description: |
  [P0·PreDesign·Brainstorm] Requirement gathering through structured interaction. Extracts scope, constraints, criteria, and edge cases via AskUserQuestion. Pipeline entry point.

  WHEN: Starting a new feature or task. User says "build X", "add Y", or has unclear requirements. No prerequisites.
  DOMAIN: pre-design (skill 1 of 3). Sequential: brainstorm -> validate -> feasibility.
  INPUT_FROM: User request (raw, unstructured).
  OUTPUT_TO: pre-design-validate (structured requirements document).

  METHODOLOGY: (1) Parse user request for requirements, (2) Categorize unknowns (scope/constraints/criteria/edge-cases), (3) Ask 3-6 questions via AskUserQuestion, (4) Synthesize into requirement document, (5) Flag remaining ambiguities.
  TIER_BEHAVIOR: TRIVIAL=Lead-only, STANDARD=1-2 analysts, COMPLEX=2-4 analysts.
  OUTPUT_FORMAT: L1 YAML requirement list with categories, L2 requirement document with open questions.
user-invocable: true
disable-model-invocation: true
argument-hint: "[topic]"
---

# Pre-Design — Brainstorm

## Execution Model
- **TRIVIAL**: Lead-direct. Parse request, ask 2-3 questions via AskUserQuestion, synthesize.
- **STANDARD**: Launch 1-2 analysts (run_in_background). Each covers separate requirement dimensions.
- **COMPLEX**: Launch 2-4 background agents (run_in_background). Divide: scope, constraints, integration, edge-cases.

> Note: Step 3 (AskUserQuestion) is ALWAYS Lead-direct regardless of tier. Analysts handle analysis work in Steps 1, 2, 4, 5 only.

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

**DPS (for STANDARD/COMPLEX tiers — spawn analyst):**
- **Context**: Parsed user request from Step 1 (explicit + implicit requirements)
- **Task**: Categorize unknowns across all 4 dimensions, identify gaps in requirements
- **Constraints**: Read-only analysis (analyst has no AskUserQuestion — cannot interact with user)
- **Expected Output**: Categorized unknowns by dimension (scope/constraints/criteria/edge-cases) with suggested questions for Lead to ask

### 3. Ask Clarifying Questions
**Executor: Lead-direct** (AskUserQuestion requires direct user interaction, not available to spawned agents).

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
