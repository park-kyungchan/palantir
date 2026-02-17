---
name: pre-design-brainstorm
description: >-
  Gathers requirements through structured user questioning.
  Extracts scope, constraints, criteria, and edge cases via
  AskUserQuestion. Pipeline entry point with no prerequisite
  skills. Reads from user request as raw unstructured input.
  Produces requirement list with tier estimate and requirement
  document with open questions for pre-design-validate.
user-invocable: true
disable-model-invocation: true
argument-hint: "[topic]"
---

# Pre-Design — Brainstorm

## Execution Model
- **TRIVIAL**: Lead-direct. Parse request, ask 2-3 questions via AskUserQuestion, synthesize.
- **STANDARD**: Launch 1-2 analysts (run_in_background, maxTurns: 10). Each covers separate requirement dimensions.
- **COMPLEX**: Launch 2-4 background agents (run_in_background, maxTurns: 10). Divide: scope, constraints, integration, edge-cases.

> Note: Step 3 (AskUserQuestion) is ALWAYS Lead-direct regardless of tier. Analysts handle analysis work in Steps 1, 2, 4, 5 only.

## Decision Points

### Tier Assessment at Brainstorm Stage
Initial tier is UNKNOWN at brainstorm start. Lead estimates based on user request:
- **TRIVIAL signals**: User says "fix this bug", "rename X", "update Y" -- narrow scope, specific target
- **STANDARD signals**: User says "add feature X", "refactor Y" -- moderate scope, clear module
- **COMPLEX signals**: User says "redesign X", "build new system Y", "migrate from A to B" -- broad scope, multiple modules
- **Tier confirmed in Step 4**: Actual tier determined after requirements gathering, may differ from initial estimate

### Question Strategy Selection
How many and what type of questions to ask:
- **Minimal questions** (TRIVIAL): 2-3 targeted questions. Focus on scope confirmation and acceptance criteria only. Don't over-explore simple tasks.
- **Standard questions** (STANDARD): 3-4 questions covering scope + constraints + criteria. Balance thoroughness with speed.
- **Deep exploration** (COMPLEX): 4-6 questions across all 4 dimensions. Multiple rounds may be needed. Use analysts for unknown categorization.

### When to Skip Brainstorm
Brainstorm can be abbreviated when:
- User provided detailed requirements (>5 sentences with explicit scope, constraints, and criteria)
- Task is a re-run of a previously planned feature (requirements in PT metadata)
- User explicitly says "skip brainstorm, here are my requirements"

In these cases: Lead creates L1/L2 directly from user input, sets `status: complete`, proceeds to validate.

### Analyst Usage Decision
- **Lead-only** (TRIVIAL): Lead parses request and asks questions directly. No analyst needed.
- **Background analyst** (STANDARD): Launch 1 analyst to categorize unknowns (Step 2) while Lead prepares initial questions. Analyst output informs question refinement.
- **Multiple analysts** (COMPLEX): Launch 2-4 analysts for different requirement dimensions. Each produces categorized unknowns for their dimension. Lead synthesizes into question set.

Key constraint: Only Lead can use AskUserQuestion (Step 3). Analysts perform analysis work in Steps 1, 2, 4, 5 only.

### P0-P1 Execution Context
This skill is the pipeline ENTRY POINT:
- TRIVIAL/STANDARD: Runs in P0-P1 (Lead with local agents, no Team infrastructure)
- COMPLEX: Runs with Team infrastructure from P0 (TeamCreate, TaskCreate/Update, SendMessage available)
- Use `run_in_background: true` for analyst spawns (TRIVIAL/STANDARD). COMPLEX uses Team agents.
- AskUserQuestion is Lead-only (agents cannot interact with users)
- This is the only skill where user interaction happens during pipeline execution

## Methodology

### 1. Parse User Request
Extract explicit and implicit requirements from user input.
- Explicit: "must", "should", "need" statements
- Implicit: unstated assumptions about environment, scale, constraints

#### Requirement Extraction Patterns
| User Input Pattern | Extracted Requirement Type | Example |
|-------------------|--------------------------|---------|
| "I want X" / "Build X" | Functional scope | "I want user authentication" -> scope: auth module |
| "It should/must X" | Constraint | "It should handle 100 users" -> constraint: scale |
| "When X happens, Y" | Edge case / error handling | "When login fails, show error" -> error: auth failure |
| "Like X but with Y" | Reference implementation | "Like current auth but with OAuth" -> scope: OAuth migration |
| "Don't X" / "Never X" | Exclusion / constraint | "Don't modify the database" -> constraint: no DB changes |

#### Implicit Requirement Detection
Common implicit requirements that users don't state but expect:
- **Backward compatibility**: Changes shouldn't break existing functionality
- **Testing**: New code should have tests
- **Documentation**: Significant changes should be documented
- **Error handling**: New features should handle failures gracefully
- **Performance**: Changes shouldn't degrade performance

Flag these as "assumed requirements" in Step 5 if not explicitly mentioned.

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
- **Delivery**: Lead reads background agent output directly (P0-P1 mode, no SendMessage)

#### Step 2 Tier-Specific DPS Variations
**TRIVIAL**: Lead categorizes unknowns directly — no analyst spawn. Quick inline assessment.
**STANDARD**: Single analyst with DPS above. maxTurns: 10.
**COMPLEX**: 2-4 analysts split by dimension (scope, constraints, integration, edge-cases). Each uses DPS above scoped to assigned dimensions. maxTurns: 10 per analyst.

### 3. Ask Clarifying Questions
**Executor: Lead-direct** (AskUserQuestion requires direct user interaction, not available to spawned agents).

Use AskUserQuestion with 3-6 questions grouped by dimension.
Max 3 question rounds before proceeding with best-effort synthesis.
After each round, merge answers into evolving requirement document.

#### Question Quality Guidelines
Good questions:
- Specific: "Should the auth module support OAuth 2.0 or just username/password?"
- Actionable: Answer directly informs a design decision
- Non-leading: Don't suggest the answer in the question
- Mutually exclusive options: When using AskUserQuestion options, ensure they're distinct

Bad questions:
- Vague: "What do you want?" (too broad)
- Technical jargon without context: "Should we use CQRS?" (user may not know the term)
- Compound: "Should it be fast AND secure?" (ask separately)

#### AskUserQuestion Best Practices
- Group related questions in a single AskUserQuestion call (max 4 questions per call)
- Provide 2-4 distinct options per question (CC AskUserQuestion requirement)
- Include option descriptions that explain implications of each choice
- Use `header` field as short label (max 12 chars): "Scope", "Auth type", "Scale"
- First option should be the recommended approach (add "(Recommended)" to label)

### 4. Classify Tier
Based on gathered requirements:
- TRIVIAL: ≤2 files, single module, clear scope
- STANDARD: 3-8 files, 1-2 modules
- COMPLEX: >8 files, 3+ modules, cross-cutting concerns

#### Tier Classification Evidence
| Tier | Evidence Required | Example |
|------|------------------|---------|
| TRIVIAL | ≤2 files identified, single module mentioned | "Fix the typo in README.md" -> 1 file, docs module |
| STANDARD | 3 files identified, 1-2 modules | "Add OAuth to auth module" -> auth.ts, config.ts, tests |
| COMPLEX | >=4 files, 2+ modules, cross-cutting | "Redesign pipeline" -> skills, agents, hooks, settings, CLAUDE.md |

Tier classification feeds directly into:
- Pipeline phase selection (CLAUDE.md Section 2)
- Resource allocation in orchestration phase
- Verification depth in verify phase

### 5. Synthesize Requirements Document
Combine all gathered information into structured output.
Flag unresolved items as open questions with rationale.

## Failure Handling

### User Provides No Useful Answers
- **Cause**: User responds with "I don't know" or "whatever you think is best" to all questions
- **Action**: Use implicit requirements and best-effort synthesis. Set `status: needs-followup`. Flag all assumed decisions in L2.
- **Routing**: Proceed to validate, which will catch missing dimensions

### User Request is Out of CC Scope
- **Cause**: User wants something CC cannot do (e.g., deploy to production, send emails)
- **Action**: Explain CC limitations. Suggest alternative approaches if possible. Set `status: needs-followup` with infeasibility note.
- **Routing**: Still proceed to validate → feasibility, which formally confirms infeasibility

### 3 Question Rounds Without Convergence
- **Cause**: Each round reveals new unknowns instead of resolving existing ones
- **Action**: Stop questioning. Synthesize best-effort requirements with documented open questions. Set `open_questions > 0`.
- **Routing**: Proceed to validate. Open questions become "gaps" that validate may flag as FAIL dimensions.

### Analyst Background Task Failed
- **Cause**: Background analyst exhausted turns or errored
- **Action**: Lead performs Steps 1, 2, 4, 5 directly. Only Step 3 (AskUserQuestion) requires Lead anyway.
- **Impact**: Slightly less thorough unknown categorization, but functional.

### Conflicting Requirements Detected
- **Cause**: User stated contradictory requirements (e.g., "must be simple" AND "must handle every edge case")
- **Action**: Flag contradiction. Ask user to choose priority via AskUserQuestion: "Which is more important: simplicity or comprehensiveness?"
- **Resolution**: Record the prioritized requirement, document the deferred one as explicit exclusion.

## Anti-Patterns

### DO NOT: Ask More Than 6 Questions Total
Over-questioning frustrates users and delays the pipeline. 3-6 questions across all rounds is the sweet spot. If you still have unknowns after 6 questions, synthesize with best-effort assumptions.

### DO NOT: Skip Brainstorm for Complex Tasks
Even when users provide detailed requirements, COMPLEX tasks benefit from brainstorm's structured dimension analysis. Implicit requirements and edge cases are almost always missing.

### DO NOT: Let Analysts Ask Users Questions
Only Lead has AskUserQuestion tool access. Analysts perform analysis work. If an analyst needs user input, it must be routed through Lead's question queue.

### DO NOT: Assume Technical Knowledge
Frame questions in terms users understand. "Should we use WebSocket or SSE?" should be "Should updates be real-time (instant) or can they be slightly delayed (refresh-based)?"

### DO NOT: Brainstorm Implementation Details
This skill gathers WHAT and WHY, not HOW. "Use React" is an implementation detail (design phase). "Need a responsive UI" is a requirement (brainstorm phase).

### DO NOT: Classify Tier Without Evidence
Tier classification must reference specific evidence: file count, module count, scope breadth. "Feels like COMPLEX" is not valid -- show the evidence.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| User request | Raw, unstructured task description | Natural language text |
| pipeline-resume | Recovered pipeline state (if resuming) | PT metadata with previous requirements |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| pre-design-validate | Structured requirements document | Always (brainstorm -> validate) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| User unresponsive | pre-design-validate (with assumptions) | Best-effort requirements + open questions |
| Out of CC scope | pre-design-validate -> feasibility | Requirements with infeasibility notes |
| Contradictory requirements | Self (re-ask) | Contradiction details for user resolution |

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
