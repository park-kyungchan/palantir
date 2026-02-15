---
name: manage-skills
description: |
  [Homeostasis·Manager·Skills] Session-aware skill lifecycle manager. Detects codebase changes via git diff, maps changed files to domains, determines CREATE/UPDATE/DELETE actions across all 8 pipeline domains.

  WHEN: After implementing features with new patterns, after modifying skills, before PR, or periodic drift detection. AI can auto-invoke.
  DOMAIN: Homeostasis (cross-cutting, operates on .claude/skills/).

  DETECTION_RULES: .claude/agents/ -> design domain, .claude/skills/ -> self-management, docs/plans/ -> plan domain, 3+ uncovered files in same domain -> CREATE.
  METHODOLOGY: (1) Git diff to detect changes, (2) Map files to domains via detection rules, (3) Check skill coverage per domain, (4) Propose CREATE/UPDATE/DELETE actions, (5) Execute after approval, (6) Run verify-cc-feasibility on results.
  OUTPUT_FORMAT: L1 YAML action list (CREATE/UPDATE/DELETE per skill), L2 markdown change analysis with rationale.
user-invocable: true
disable-model-invocation: false
---

# Manage — Skills

## Execution Model
- **TRIVIAL**: Lead-direct. Quick scan for 1-2 domain changes.
- **STANDARD**: Spawn analyst. Full domain coverage analysis.
- **COMPLEX**: Spawn 2 analysts. One for change detection, one for coverage analysis.

## Methodology

### 1. Detect Changes
**Executor: Lead-direct** (requires Bash for git commands).

Run git diff to identify modified files:
- `git diff --name-only HEAD` for unstaged changes
- `git diff --name-only --cached` for staged changes
- Categorize each changed file by domain

Lead runs git diff and passes the output as context to analysts spawned in subsequent steps.

**Note**: Analysts have no Bash tool. Lead runs `git diff --name-only HEAD` before spawning and pastes the output into the analyst's Context block.

### Tier-Specific Delegation (DPS Templates)

**TRIVIAL DPS** (1-2 changed files, single domain):
Lead maps files directly without spawning an analyst. Check domain coverage inline by counting skills in the affected domain. If coverage holds, propose UPDATE actions immediately. No analyst overhead for simple drift.
```
Context: [1-2 file paths from git diff]
Task: Map to domain, check coverage, propose action.
Constraints: Lead-direct, no spawn.
Expected Output: Inline action list (1-2 items).
```

**STANDARD DPS** (3-8 changed files, 1-2 domains):
Spawn a single analyst with git diff output and all 35 skill descriptions pre-loaded.
```
Context: git diff output (file list + summary), all skill descriptions (frontmatter only).
Task: "Map changed files to domains. For each affected domain, check coverage against
       minimum thresholds. Propose CREATE/UPDATE/DELETE with rationale for each action."
Constraints: maxTurns:15, analyst agent, Read+Grep+Glob tools only.
Expected Output: L1 YAML action list with severity per action.
```

**COMPLEX DPS** (8+ changed files, 3+ domains):
Spawn 2 analysts in sequence. Analyst-1 handles change detection and domain mapping. Analyst-2 receives Analyst-1's output and performs coverage analysis with action proposals.
```
Analyst-1:
  Context: git diff output (full), detection rules table.
  Task: "Classify every changed file into a domain. Flag ambiguous files as unclassified."
  Constraints: maxTurns:20, analyst agent.
  Expected Output: Domain-classified file list.

Analyst-2:
  Context: Analyst-1 output (classified file list) + full skill inventory (35 descriptions).
  Task: "For each affected domain, compare current skill count against minimum thresholds.
         Propose CREATE/UPDATE/DELETE actions. Include rationale and severity."
  Constraints: maxTurns:20, analyst agent.
  Expected Output: L1 YAML action list + L2 coverage analysis.
```

### 2. Map Changes to Domains
Apply detection rules:
- `.claude/agents/` changes → design domain skills
- `.claude/skills/` changes → self-management (this skill)
- `docs/plans/` changes → plan domain skills
- Source code changes → execution domain skills
- 3+ uncovered files in same domain → signal for CREATE new skill

### 3. Check Domain Coverage
For all domains (8 pipeline + homeostasis + cross-cutting = 35 skills):
- List existing skills in that domain
- Identify if the domain change is covered by an existing skill
- If not covered: propose CREATE action with suggested skill name and description

### 4. Propose Actions
Generate action list:
- **CREATE**: New skill needed (domain gap detected)
- **UPDATE**: Existing skill needs description/body changes (methodology evolved)
- **DELETE**: Skill no longer serves a purpose (domain removed or merged)
Include rationale for each action.

### 5. Execute and Verify
**Executor: spawn infra-implementer** for file modifications. Lead coordinates.

After user approval:
- For CREATE: generate SKILL.md with frontmatter + L2 body
- For UPDATE: edit existing SKILL.md
- For DELETE: remove skill directory
  **Limitation**: Analysts cannot delete files (no Bash tool). DELETE actions are flagged for user manual action. Lead reports the orphaned path for user to remove.
- Run verify-cc-feasibility on all changed skills

## Decision Points

### Change Detection Source
- **git diff HEAD** (default): Detects all uncommitted changes. Use for routine drift detection and pre-PR checks.
- **git diff against main**: Detects all changes on the current branch vs main. Use for comprehensive branch-level skill lifecycle assessment.
- **User-provided file list**: When Lead already knows which files changed (e.g., from SRC log or pipeline context). Skip git diff entirely and map directly.

### Action Threshold for CREATE
- **3+ uncovered files** (rule-based): Default detection rule. If 3 or more changed files map to a domain with no covering skill, propose CREATE.
- **Pattern emergence**: Even with <3 files, if changes introduce a genuinely new capability pattern (e.g., a new hook type, a new agent role), propose CREATE with justification.
- **Never CREATE for temporary patterns**: One-off scripts, experiment files, or debug utilities should not trigger new skills.

### Self-Management Detection
- **Changes to `.claude/skills/`**: This skill manages itself. When skill files are the changed files, the analyst must distinguish between "I need to update this skill" vs "this skill was already updated by another pipeline."
- **Resolution**: Check git authorship and commit messages. If changes were made by a pipeline execution, validate them. If they're manual edits, propose UPDATE actions.

### UPDATE vs DELETE Decision
- **UPDATE**: Skill exists but methodology, description, or scope has evolved due to codebase changes. The skill's core purpose remains valid.
- **DELETE**: Skill's purpose is entirely obsoleted (domain removed, capability merged into another skill). Rare -- prefer UPDATE.

### Domain Coverage Assessment
After mapping changes, Lead checks per-domain skill count against expected minimums:

| Domain | Min Skills | Current Count |
|--------|-----------|---------------|
| pre-design | 3 | 3 |
| design | 3 | 3 |
| research | 3 | 3 |
| plan | 3 | 3 |
| plan-verify | 3 | 3 |
| orchestration | 3 | 3 |
| execution | 5 | 5 |
| verify | 5 | 5 |
| homeostasis | 4 | 4 |
| cross-cutting | 3 | 3 |

If any domain would fall below its minimum after a proposed DELETE: reject the DELETE. The coverage table is the hard floor -- no domain can lose skills below its minimum without explicit user approval and a plan to replace the coverage.

### Skill Naming Convention
New skills must follow the naming pattern: `{domain}-{action}`. Examples: `execution-code`, `verify-structure`, `manage-infra`. Rules:
- The domain prefix must match one of the 10 registered domains above.
- The action suffix must be a concrete verb or noun describing the skill's purpose.
- Never use generic names like `utility`, `helper`, `misc`, or `general`.
- The full name must be unique across all 35 skills. Check existing names before proposing CREATE.
- Naming violations are caught by verify-structure and block the pipeline.

### Post-Action Verification Chain
After every CREATE, UPDATE, or DELETE action is executed, run the following verification sequence in order:
1. **verify-structure**: Confirms YAML frontmatter parses correctly, directory exists, file naming is valid.
2. **verify-content**: Confirms description utilization >80% of 1024 chars, all orchestration map keys present (WHEN, DOMAIN, INPUT_FROM, OUTPUT_TO).
3. **verify-cc-feasibility**: Confirms only CC native fields used, no custom fields that would be silently ignored.

If any verification step fails: route to execution-infra for correction. Do NOT mark manage-skills as complete until all three verifications pass for every affected skill. This chain is non-negotiable -- it prevents invisible routing failures caused by non-native frontmatter.

## Failure Handling

### Git Diff Unavailable
- **Cause**: Not in a git repository, or git command fails
- **Action**: Fall back to full filesystem scan of `.claude/skills/` and compare against expected domain coverage. Report `detection_mode: filesystem-only` in L1.

### Domain Mapping Ambiguous
- **Cause**: Changed files don't clearly map to any domain (e.g., utility scripts, configuration files)
- **Action**: Flag as `domain: unclassified` in the action list. Do not force-classify -- let Lead decide routing.

### Analyst Cannot Delete Files
- **Cause**: Analyst tool profile lacks Bash/Write-destructive capabilities
- **Action**: Flag DELETE actions as `requires_manual: true` with the exact path for user to remove. Lead reports orphaned path.

### Verify-CC-Feasibility Fails on New Skill
- **Cause**: Newly created SKILL.md has non-native fields or structural issues
- **Action**: Route back to infra-implementer for frontmatter correction before committing.

### Conflicting Actions Proposed
- **Cause**: Two analysts propose contradictory actions for the same skill (one says UPDATE, other says DELETE). This occurs in COMPLEX tier with parallel analysts operating on overlapping domain boundaries.
- **Action**: Prefer UPDATE over DELETE (conservative principle). Flag the conflict in the L1 output with `conflict: true` and include both rationales. Lead reviews and makes final decision. Never auto-resolve in favor of DELETE -- data loss is irreversible.

### New Domain Detected
- **Cause**: Changed files introduce patterns that don't map to any of the 10 existing domains (8 pipeline + homeostasis + cross-cutting). This is a rare structural evolution event indicating the pipeline itself is growing.
- **Action**: Do NOT force-classify into an existing domain. Flag as `new_domain_candidate: true` with a proposed domain name and justification. Creating a new domain category requires: (1) user approval, (2) CLAUDE.md domain count update, (3) at least 1 skill created for the new domain. Route to Lead for user confirmation before proceeding.

## Anti-Patterns

### DO NOT: Create Skills for Every File Change
Not every code change warrants a new skill. Skills represent stable, repeatable methodologies. A one-time refactoring or bug fix is handled by existing execution skills, not a new skill.

### DO NOT: Delete Skills Without Checking References
Before proposing DELETE, verify no other skill's INPUT_FROM/OUTPUT_TO references the target skill. Deleting a referenced skill breaks the pipeline routing chain.

### DO NOT: Skip CC Feasibility Verification
Every CREATE or UPDATE action must be followed by verify-cc-feasibility. Non-native frontmatter fields are silently ignored by CC, causing invisible routing failures.

### DO NOT: Run Git Commands in Analyst Context
Analysts have no Bash tool. Lead must run `git diff` and pass the output as context. Spawning an analyst with instructions to run git commands wastes turns on permission failures.

### DO NOT: Merge Skills Without Domain Coverage Check
Merging two skills into one may leave a domain gap. Always verify post-merge domain coverage -- every domain must retain at least 1 skill.

### DO NOT: Use manage-skills to Modify Skill L2 Bodies
This skill manages skill LIFECYCLE: create frontmatter, update descriptions, delete orphaned skills. It does NOT rewrite L2 methodology bodies. L2 body improvements go through the self-improve skill or manual editing. manage-skills only touches the YAML frontmatter and top-level structural metadata. If an analyst proposes "UPDATE: rewrite the methodology section," reject it and redirect to self-improve.

### DO NOT: Propose DELETE for Recently Created Skills
A skill created in the current pipeline iteration should not be flagged for DELETE in the same cycle. Wait at least one full pipeline completion before proposing removal. New skills need time to prove or disprove their value through actual routing and execution. If a brand-new skill seems redundant immediately after creation, that indicates a CREATE decision error -- route to Lead for root cause analysis, not a DELETE action.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| (self-triggered) | Drift detection request after codebase changes | No structured input -- uses git diff |
| manage-infra | Skill-specific drift detected during health check | L1 YAML: skill count mismatch or orphan alert |
| delivery-pipeline | Pre-commit skill validation request | L1 YAML: pipeline completion status with changed files |
| self-improve | Post-RSI skill frontmatter refresh | L1 YAML: list of modified .claude/skills/ files |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| execution-infra | CREATE/UPDATE file modification tasks | When user approves proposed actions |
| verify-cc-feasibility | Changed skill files for compliance check | After every CREATE or UPDATE execution |
| (user) | Action list with rationale | Always (terminal -- report proposed actions) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Git diff unavailable | (self, filesystem mode) | Falls back to full scan, reports detection_mode |
| Domain mapping ambiguous | (user) | Unclassified files for manual domain assignment |
| CC feasibility fails | execution-infra | Frontmatter correction task for failed skills |
| DELETE requires manual action | (user) | Orphaned path for manual removal |

## Quality Gate
- All domains (8 pipeline + homeostasis + cross-cutting) have ≥1 skill
- All proposed actions have clear rationale (no "UPDATE: description outdated" without specifying what changed and what the new description should say)
- No domain left uncovered after actions applied
- Changed skills pass CC feasibility check (native fields only, description ≤1024 chars)
- Skill naming follows `{domain}-{action}` convention -- no generic names like `utility` or `helper`
- No duplicate skill names across all domains (35 unique names required)
- Post-action verification chain completed: verify-structure -> verify-content -> verify-cc-feasibility (all three must pass before marking complete)

## Output

### L1
```yaml
domain: homeostasis
skill: manage-skills
status: complete
actions:
  - skill: ""
    action: CREATE|UPDATE|DELETE
    domain: ""
    reason: ""
```

### L2
- Git diff analysis summary
- Domain coverage report
- Proposed action rationale per skill
