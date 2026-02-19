# Pre-Design Brainstorm — Detailed Methodology

> On-demand reference for pre-design-brainstorm. Contains detailed steps, patterns, and guidelines.

## Step 1: Parse User Request — Extraction Patterns

| User Input Pattern | Extracted Requirement Type | Example |
|-------------------|--------------------------|---------| 
| "I want X" / "Build X" | Functional scope | "I want user authentication" → scope: auth module |
| "It should/must X" | Constraint | "It should handle 100 users" → constraint: scale |
| "When X happens, Y" | Edge case / error handling | "When login fails, show error" → error: auth failure |
| "Like X but with Y" | Reference implementation | "Like current auth but with OAuth" → scope: OAuth migration |
| "Don't X" / "Never X" | Exclusion / constraint | "Don't modify the database" → constraint: no DB changes |

### Implicit Requirement Detection
Common implicit requirements users don't state but expect:
- **Backward compatibility**: Changes shouldn't break existing functionality
- **Testing**: New code should have tests
- **Documentation**: Significant changes should be documented
- **Error handling**: New features should handle failures gracefully
- **Performance**: Changes shouldn't degrade performance
Flag these as "assumed requirements" in Step 5.

## Step 2: Categorize Unknowns — DPS

**DPS (analyst spawn for STANDARD/COMPLEX)**:
- **Context**: Parsed user request from Step 1 (explicit + implicit requirements)
- **Task**: Categorize unknowns across 4 dimensions, identify gaps
- **Constraints**: Read-only analysis (no AskUserQuestion — cannot interact with user)
- **Output**: Categorized unknowns by dimension with suggested questions
- **Delivery**: Lead reads directly (P0-P1 mode)

Tier-specific:
- **TRIVIAL**: Lead categorizes directly — no spawn
- **STANDARD**: 1 analyst. maxTurns: 10.
- **COMPLEX**: 2-4 analysts split by dimension. maxTurns: 10 each.

## Step 3: AskUserQuestion Guidelines

### Question Quality Rules
**Good**: Specific ("OAuth 2.0 or username/password?"), actionable, non-leading, mutually exclusive options
**Bad**: Vague ("What do you want?"), jargon-heavy, compound ("fast AND secure?")

### AskUserQuestion Best Practices
- Group related questions (max 4 per call)
- Provide 2-4 distinct options
- Include option descriptions explaining implications
- `header` field: short label (max 12 chars): "Scope", "Auth type"
- First option = recommended approach (add "(Recommended)")

## Step 4: Tier Classification Evidence

| Tier | Evidence Required | Example |
|------|------------------|---------| 
| TRIVIAL | ≤2 files, single module | "Fix typo in README.md" → 1 file |
| STANDARD | 3-8 files, 1-2 modules | "Add OAuth to auth" → auth.ts, config.ts, tests |
| COMPLEX | >8 files, 3+ modules | "Redesign pipeline" → skills, agents, hooks |

## Failure Protocols (Detail)

**User provides no useful answers**: Use implicit requirements + best-effort synthesis. `status: needs-followup`. Flag assumed decisions. → validate catches missing dimensions.

**Out of CC scope**: Explain limitations, suggest alternatives. `status: needs-followup` with infeasibility note. → validate → feasibility formally confirms.

**3 rounds without convergence**: Stop. Best-effort + documented open questions. → validate flags gaps.

**Analyst failed**: Lead performs Steps 1,2,4,5 directly. Less thorough but functional.

**Conflicting requirements**: Flag, ask user priority via AskUserQuestion. Record prioritized, document deferred as exclusion.
