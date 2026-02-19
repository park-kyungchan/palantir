---
name: pre-design-brainstorm
description: >-
  Gathers requirements through structured user questioning.
  Extracts scope, constraints, criteria, and edge cases via
  AskUserQuestion. Pipeline entry point with no prerequisite
  skills. Reads from user request as raw unstructured input.
  Produces requirement list with tier estimate and requirement
  document with open questions for pre-design-validate.
  AskUserQuestion is Lead-direct only — analysts handle
  categorization and synthesis (Steps 1, 2, 4, 5). TRIVIAL:
  Lead-direct, 2-3 questions. STANDARD: 1 background analyst
  (maxTurns: 10). COMPLEX: 2-4 analysts split by dimension
  (scope, constraints, integration, edge-cases). On FAIL (user
  unresponsive or conflicting requirements), Lead applies D12
  escalation. DPS needs user requirements as raw input. Exclude
  pipeline history and technical constraints. Loops with
  pre-design-validate (max 3 iterations per D15).
user-invocable: true
disable-model-invocation: true
argument-hint: "[topic]"
---

# Pre-Design — Brainstorm

## Execution Model
- **TRIVIAL**: Lead-direct. Parse request, ask 2-3 questions, synthesize.
- **STANDARD**: 1-2 analysts (run_in_background, maxTurns: 10). Separate requirement dimensions.
- **COMPLEX**: 2-4 background agents (maxTurns: 10). Divide: scope, constraints, integration, edge-cases.

> Step 3 (AskUserQuestion) is ALWAYS Lead-direct. Analysts handle Steps 1, 2, 4, 5 only.

## Decision Points

### Tier Assessment
Initial tier UNKNOWN. Lead estimates from user request:
- **TRIVIAL**: "fix bug", "rename X" — narrow, specific target
- **STANDARD**: "add feature X", "refactor Y" — moderate scope, clear module
- **COMPLEX**: "redesign X", "build system Y", "migrate A to B" — broad, multi-module
- Tier CONFIRMED in Step 4 after requirements gathered

### Question Strategy
- **TRIVIAL**: 2-3 targeted (scope + acceptance only)
- **STANDARD**: 3-4 (scope + constraints + criteria)
- **COMPLEX**: 4-6 across all dimensions, multiple rounds possible

### When to Skip
Skip when user provided >5 sentences with explicit scope/constraints/criteria, or task is re-run from PT metadata, or user says "skip brainstorm." Create L1/L2 directly, proceed to validate.

### Analyst Usage
- **Lead-only** (TRIVIAL): No spawn needed
- **Background** (STANDARD): 1 analyst for unknown categorization
- **Multiple** (COMPLEX): 2-4 analysts by dimension

Key: Only Lead can AskUserQuestion. Analysts do analysis only.

### P0-P1 Execution Context
Pipeline ENTRY POINT. TRIVIAL/STANDARD: P0-P1 local (run_in_background). COMPLEX: Team infra from P0. AskUserQuestion = Lead-only.

## Methodology
For detailed steps and patterns: Read `resources/methodology.md`

Summary:
1. **Parse** user request (explicit + implicit requirements)
2. **Categorize** unknowns across 4 dimensions (scope/constraints/criteria/edge-cases)
3. **Ask** via AskUserQuestion (Lead-direct, 3-6 questions, max 3 rounds)
4. **Classify** tier based on evidence (file count, module count)
5. **Synthesize** requirements document

### Iteration Tracking (D15)
- `metadata.iterations.brainstorm: N` in PT
- Iterations 1-2: strict (FAIL from validate → re-question)
- Iteration 3: relaxed (proceed with gaps, flag in phase_signals)
- Max: 3

## Failure Handling
For D12 escalation ladder: Read `~/.claude/resources/failure-escalation-ladder.md`

| Failure | Level | Action |
|---------|-------|--------|
| Analyst tool error | L0 | Retry same analyst |
| Vague user answers | L1 | Rephrase with examples |
| Analyst exhausted | L2 | Fresh analyst, narrower scope |
| 3+ rounds, no convergence | L3 | Pare scope, best-effort synthesis |
| User unresponsive | L4 | AskUserQuestion with concrete options |

For detailed failure protocols: Read `resources/methodology.md` § Failure Protocols

## Anti-Patterns

### DO NOT: Ask >6 questions total
3-6 across all rounds. Beyond that, synthesize with best-effort assumptions.

### DO NOT: Skip brainstorm for COMPLEX tasks
Even with detailed user input, implicit requirements and edge cases are almost always missing.

### DO NOT: Let analysts ask users questions
Only Lead has AskUserQuestion. Route analyst needs through Lead's question queue.

### DO NOT: Assume technical knowledge
"OAuth 2.0 or username/password?" → "real-time updates or can they be slightly delayed?"

### DO NOT: Brainstorm implementation details
Gather WHAT and WHY, not HOW. "Need responsive UI" ✅ vs "Use React" ❌

### DO NOT: Classify tier without evidence
"Feels COMPLEX" is invalid. Show file count, module count, scope breadth.

## Transitions

### Receives From
| Source | Data |
|--------|------|
| User request | Raw task description |
| pipeline-resume | Recovered pipeline state (if resuming) |

### Sends To
| Target | Condition |
|--------|-----------|
| pre-design-validate | Always |

### Failure Routes
| Failure | Route | Data |
|---------|-------|------|
| User unresponsive | validate (with assumptions) | Best-effort + open questions |
| Out of CC scope | validate → feasibility | Requirements + infeasibility notes |
| Contradictory reqs | Self (re-ask) | Contradiction details |

## Quality Gate
- All 4 dimensions have ≥1 requirement
- No circular/contradictory requirements
- Tier classification has evidence
- Open questions have clear deferral rationale

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
