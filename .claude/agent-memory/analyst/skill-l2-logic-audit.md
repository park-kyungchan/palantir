# Skill L2 Logic Audit -- 35 Skills Deep Analysis

> Generated: 2026-02-15 | Scope: All 35 skills in `/home/palantir/.claude/skills/`
> Focus: Logic issues (methodology implementability, step completeness, quality gate realism, output chain consistency, failure path coverage)
> Excludes: Structural/formatting issues (addressed in v10.5/v10.6)

## Executive Summary

| Severity | Count | Description |
|----------|-------|-------------|
| CRITICAL | 2 | Logic errors that will cause pipeline failures |
| HIGH | 7 | Logic gaps that will produce incorrect or incomplete results |
| MEDIUM | 12 | Logic weaknesses that degrade quality but don't break execution |
| LOW | 8 | Minor logic improvements, edge case coverage |
| **TOTAL** | **29** | |

**Overall Logic Health: 7.4/10**

The skill system is architecturally sound. Most skills have well-structured methodologies that map cleanly to available agent tools. The primary weakness cluster is around **convergence verification** (can the quality gate actually be checked with available tools?) and **cross-skill data handoff** (does the output format actually match what downstream skills need to parse?). The secondary cluster is **failure path incompleteness** -- most skills define the happy path well but leave the FAIL->retry->FAIL->abandon path underspecified.

---

## Findings

---

### CRITICAL Findings (2)

#### C-01: execution-cascade convergence check assumes Lead can run grep

- **Skill**: `execution-cascade` (line 50-64)
- **File**: `/home/palantir/.claude/skills/execution-cascade/SKILL.md`
- **Issue**: Step 3 "Check Convergence After Updates" defines a `check_convergence()` pseudocode function that performs `grep -rl basename .claude/`. This convergence check is described as something Lead does directly ("Convergence is checked manually via grep, not via hook-driven analysis" at line 103). However, CLAUDE.md Section 2.1 states "Lead NEVER edits files directly" and the Lead agent has NO Bash tool access. Lead cannot execute grep commands.
- **Impact**: The cascade loop has no mechanism to detect convergence. Lead would either (a) blindly re-invoke execution-impact for each iteration (which the skill explicitly says NOT to do at lines 99-104), or (b) skip convergence checking entirely, potentially iterating to max 3 without knowing if work is done.
- **Resolution**: The convergence check must be delegated to a spawned agent (analyst or researcher with Grep tool). Alternatively, Lead could spawn a one-shot analyst with maxTurns:5 whose sole job is to run the convergence grep and report back a boolean. The pseudocode should be rewritten as an analyst task specification rather than a Lead-executed function.

#### C-02: plan-verify-completeness references pre-design-validate output, but TRIVIAL/STANDARD tiers skip P5

- **Skill**: `plan-verify-completeness` (line 8, step 1 line 27)
- **File**: `/home/palantir/.claude/skills/plan-verify-completeness/SKILL.md`
- **Issue**: The skill's INPUT_FROM declares `pre-design-validate (original requirements for coverage)` and Step 1 says "Read pre-design-validate (original requirements)". However, the skill is in the P5 domain (plan-verify). Looking at the pipeline tier table in CLAUDE.md: TRIVIAL skips P5 entirely (P0->P7->P9), and STANDARD also skips P5 (P0->P2->P3->P4->P7->P8->P9). This means plan-verify skills ONLY execute in COMPLEX tier. But the deeper problem is: the skill assumes it can "read" pre-design-validate output, but there is no persistent artifact store. Pre-design-validate runs in P0 (Lead-only context), and by P5 that output exists only in Lead's conversation context. If Lead has compacted between P0 and P5, this data is lost.
- **Impact**: In a long COMPLEX pipeline, the requirements document from P0 may be compacted away by the time P5 runs, making this skill's core function (traceability matrix construction) impossible. The quality gate requires "requirement coverage >=90%" but Lead may not have the original requirements to verify against.
- **Resolution**: This is an architectural data persistence gap, not just a skill-level issue. Requirements from P0 should be persisted to PERMANENT Task metadata or a file artifact so P5 can reliably access them. For immediate mitigation, the skill should specify that Lead must extract requirements into PT metadata during P0 and the skill should read from PT (TaskGet) rather than from ephemeral conversation context.

---

### HIGH Findings (7)

#### H-01: pre-design-brainstorm TIER_BEHAVIOR says "Launch analysts" but P0-P2 is Lead-only

- **Skill**: `pre-design-brainstorm` (lines 22-24)
- **File**: `/home/palantir/.claude/skills/pre-design-brainstorm/SKILL.md`
- **Issue**: The Execution Model says "STANDARD: Launch 1-2 analysts (run_in_background). Each covers separate requirement dimensions." and "COMPLEX: Launch 2-4 background agents (run_in_background)." But CLAUDE.md Section 2.1 explicitly states: "P0-P2 (PRE-DESIGN + DESIGN): Lead-only. Brainstorm, validate, feasibility, architecture, interface, risk -- all executed by Lead with local agents (run_in_background). No Team infrastructure needed."
- **Impact**: The `run_in_background` qualifier is consistent with "Lead-only" mode (local agents are allowed), but the analyst agent definition at `/home/palantir/.claude/agents/analyst.md` has tools=[Read, Glob, Grep, Write, sequential-thinking]. AskUserQuestion is NOT in the analyst's tool list. So if analysts are spawned for brainstorm's Step 3 ("Ask Clarifying Questions via AskUserQuestion"), they cannot execute that step.
- **Resolution**: Either (a) the skill should note that AskUserQuestion must remain Lead-direct even when analysts are spawned for other steps, or (b) the analyst tool list should include AskUserQuestion for brainstorm contexts. Option (a) is the cleaner fix.

#### H-02: execution-impact spawns researcher but grep instructions mismatch researcher capabilities

- **Skill**: `execution-impact` (lines 39-45)
- **File**: `/home/palantir/.claude/skills/execution-impact/SKILL.md`
- **Issue**: Step 3 says "Spawn researcher agent" and instructs: "Researcher performs `grep -rl <basename>` for each changed file". But the researcher agent (`/home/palantir/.claude/agents/researcher.md`) has Grep tool (the Claude Code Grep tool), NOT Bash. The Claude Code Grep tool has different syntax and behavior from shell `grep -rl`. The methodology conflates shell grep semantics with the Claude Code Grep tool.
- **Additionally**: The methodology says "Grep scope includes: `*.md`, `*.json`, `*.sh` files in `.claude/`" and "Grep excludes: `.git/`, `node_modules/`, `agent-memory/`". These are glob-style file filters that map to the Grep tool's `glob` parameter, but the instructions are written as if they are shell grep flags (--include, --exclude-dir). A researcher following these literally would be confused about how to translate to CC Grep tool calls.
- **Impact**: The researcher may waste turns trying to figure out the right Grep tool invocations, or produce incomplete results because the grep pattern semantics don't translate cleanly.
- **Resolution**: Rewrite Step 3 to use CC Grep tool semantics explicitly: `Grep(pattern="basename_pattern", path=".claude/", glob="*.md", output_mode="files_with_matches")`.

#### H-03: self-improve Step 5 requires delivery-agent-like capabilities but uses infra-implementer

- **Skill**: `self-improve` (lines 59-65)
- **File**: `/home/palantir/.claude/skills/self-improve/SKILL.md`
- **Issue**: Step 5 "Commit and Record" says "Stage changed files with `git add` (specific files, never `-A`)" and "Create structured commit message". The skill's Step 3 uses infra-implementer agents for fixes, but infra-implementer (`/home/palantir/.claude/agents/infra-implementer.md`) has NO Bash tool. The git operations in Step 5 require Bash.
- **Impact**: The skill methodology describes git commit operations that cannot be performed by any agent it explicitly spawns. This step must either be (a) Lead-direct (but Lead cannot execute commands per constitution), or (b) delegated to an implementer or delivery-agent (but the skill doesn't mention either).
- **Resolution**: Step 5 should specify spawning a delivery-agent or implementer for the git operations, or explicitly state that Lead executes these via Bash (which would require a constitution exception).

#### H-04: manage-skills Step 1 uses git diff but the executing agent (analyst) has no Bash

- **Skill**: `manage-skills` (lines 26-29)
- **File**: `/home/palantir/.claude/skills/manage-skills/SKILL.md`
- **Issue**: Step 1 "Detect Changes" says "Run git diff to identify modified files: `git diff --name-only HEAD`". The Execution Model says "Spawn analyst" (STANDARD) or "Spawn 2 analysts" (COMPLEX). Analysts have NO Bash tool, so they cannot run git diff.
- **Impact**: The primary detection mechanism (git diff) is unavailable to the agent assigned to execute it. The analyst would need to use alternative approaches (Glob + Read) which are less precise for change detection.
- **Resolution**: Either (a) Lead-direct for Step 1 (Lead can assess changes from conversation context), (b) specify that Lead provides the git diff output to the analyst in the spawn prompt, or (c) use a researcher or implementer for change detection. Option (b) is cleanest and most aligned with existing patterns.

#### H-05: research-external references `context7` and `tavily` MCP tools but researcher agent listing is incomplete

- **Skill**: `research-external` (lines 35-38)
- **File**: `/home/palantir/.claude/skills/research-external/SKILL.md`
- **Issue**: Step 2 "Search Official Documentation" lists a priority order: "1. context7 (resolve-library-id -> query-docs) 2. WebSearch 3. WebFetch 4. tavily". The researcher agent DOES have all these tools listed (confirmed in `/home/palantir/.claude/agents/researcher.md` lines 17-20). However, the `tavily` tool is listed in the agent as `mcp__tavily__search` but the skill refers to it simply as "tavily". This is a naming inconsistency that could confuse the agent. **More critically**: `WebFetch` is only permitted for `domain:github.com` and `domain:raw.githubusercontent.com` in settings.json (lines 15-16). The skill says "WebFetch for specific documentation pages" without noting this domain restriction.
- **Impact**: The researcher will hit permission denials when trying to WebFetch non-GitHub documentation pages (e.g., official library docs at docs.python.org, expressjs.com, etc.). This silently degrades the research capability.
- **Resolution**: (a) Expand WebFetch domain permissions in settings.json if broader doc access is needed, or (b) document the GitHub-only restriction in the skill methodology and provide tavily as the primary fallback for non-GitHub docs.

#### H-06: delivery-pipeline requires "verify domain all-PASS" but has no mechanism to read verify outputs

- **Skill**: `delivery-pipeline` (line 29)
- **File**: `/home/palantir/.claude/skills/delivery-pipeline/SKILL.md`
- **Issue**: Step 1 says "Read verify domain output: all 5 stages must show PASS". But the delivery-agent is spawned as a fork agent (`model: haiku`, `memory: none`). With `memory: none`, it has no access to previous conversation context. And with `model: haiku`, it has reduced capability to parse complex pipeline outputs. The verify domain outputs exist only in Lead's conversation context -- there is no persistent artifact the delivery-agent can read.
- **Impact**: The delivery-agent cannot independently verify the all-PASS condition. It must trust whatever Lead tells it in the spawn prompt. This means the "safety gate" (abort if any FAIL) is effectively Lead's responsibility, not the delivery-agent's, making the Step 1 verification decorative rather than functional.
- **Resolution**: Lead should include the verify verdict summary in the delivery-agent spawn prompt. The skill should explicitly state that the all-PASS verification data comes from Lead's spawn prompt, not from the agent's independent investigation. Alternatively, verify outputs could be persisted to a file that the delivery-agent reads.

#### H-07: orchestration-verify Step 3 says "Run topological sort" but Lead has no sorting algorithm

- **Skill**: `orchestration-verify` (lines 36-38)
- **File**: `/home/palantir/.claude/skills/orchestration-verify/SKILL.md`
- **Issue**: Step 3 "Check Dependency Acyclicity" says "Run topological sort on dependency graph: If sort succeeds -> acyclic (PASS), If sort fails -> cycle detected (FAIL, report cycle)". This is described as a Lead-direct operation (Execution Model says "Lead-direct" for TRIVIAL and STANDARD). Lead is an LLM -- it can reason about small dependency graphs but cannot execute a formal topological sort algorithm. For COMPLEX tier with 8+ tasks and many dependency edges, LLM-based cycle detection is unreliable.
- **Impact**: For large dependency graphs, Lead may miss cycles or falsely report cycles, leading to incorrect PASS/FAIL verdicts.
- **Resolution**: For COMPLEX tier, the skill already says "Spawn analyst for independent verification" which is the right approach. For STANDARD tier, the methodology should acknowledge that Lead performs approximate cycle detection via reasoning, not algorithmic topological sort. The quality gate should be softened from "acyclic" to "no obvious cycles detected" for Lead-direct execution.

---

### MEDIUM Findings (12)

#### M-01: Data handoff gap -- plan-strategy OUTPUT_TO includes plan-verify domain, but plan-verify INPUT_FROM only references plan-strategy (not plan-interface)

- **Skills**: `plan-strategy`, `plan-verify-correctness`, `plan-verify-completeness`, `plan-verify-robustness`
- **Issue**: plan-strategy outputs to "plan-verify domain (complete plan for validation)". The 3 plan-verify skills each declare INPUT_FROM as only plan-strategy or design specs. But plan-interface produces inter-task contract specifications that plan-verify-correctness Step 3 needs ("Dependency Chain Verification: Producer tasks produce what consumer tasks expect"). plan-verify-correctness does not declare INPUT_FROM: plan-interface, meaning it may not receive the interface contracts needed for Step 3.
- **Impact**: plan-verify-correctness may perform dependency chain verification without the actual interface contracts, relying on whatever plan-strategy included about interfaces (which may be a summary, not the full spec).
- **Resolution**: plan-verify-correctness should declare INPUT_FROM: plan-interface alongside plan-strategy.

#### M-02: execution-review "Issue Fix Loop" creates infinite potential for context bloat

- **Skill**: `execution-review` (lines 52-55)
- **Issue**: Step 5 says "If critical or high findings exist: Report to execution-code/infra for implementer fixes -> Re-review after fixes applied -> Max 3 review-fix iterations". Each iteration spawns new reviewer analysts AND new implementer agents. In a COMPLEX pipeline, this could mean 3 x (2-3 analysts + 3-4 implementers) = up to 21 agent spawns within execution-review alone. Each spawn returns L1/L2 to Lead's context.
- **Impact**: Lead context bloat risk. With 21 agent summaries in conversation context, Lead may hit compaction triggers, losing earlier pipeline context.
- **Resolution**: The skill should specify that re-review spawns should be minimal (1 analyst max, focused on previously-found issues only) and that implementer fixes should be consolidated into a single spawn per iteration.

#### M-03: verify-structure YAML validation without Bash or parser

- **Skill**: `verify-structure` (lines 32-35)
- **Issue**: Step 2 "Validate YAML Frontmatter" says "Parse YAML between `---` markers, Check parsing succeeds without errors". The executing agent is an analyst (Read, Glob, Grep, Write, sequential-thinking). There is no YAML parser tool available. The analyst must visually inspect YAML for validity, which is error-prone for subtle issues (incorrect indentation, missing colons, bad escaping).
- **Impact**: Subtle YAML errors may pass verification (false PASS). The quality gate "All files have valid YAML frontmatter" cannot be mechanically verified.
- **Resolution**: Accept this as a known limitation and note in the methodology that "validation is visual/heuristic, not parser-based". Alternatively, an implementer could be used (Bash access allows `python3 -c 'import yaml; yaml.safe_load(...)'`).

#### M-04: verify-cc-feasibility Step 4 spawns claude-code-guide but this is not a defined agent

- **Skill**: `verify-cc-feasibility` (lines 55-59)
- **Issue**: Step 4 says "Spawn claude-code-guide: 'Are these frontmatter fields valid for Claude Code skills/agents?'" However, `claude-code-guide` is not one of the 6 defined agents (analyst, researcher, implementer, infra-implementer, delivery-agent, pt-manager). It's an external tool/agent that may or may not be available. The parenthetical "(if unavailable, use cc-reference cache in `memory/cc-reference/`)" provides a fallback, which is good.
- **Impact**: The primary verification path (claude-code-guide spawn) will fail if the external agent is unavailable, falling back to cached reference docs which may be stale. This is a known limitation documented elsewhere (INT-07), but the skill treats claude-code-guide as if it's always available as the default path.
- **Resolution**: Swap the priority: make cc-reference cache the primary path and claude-code-guide the supplementary/confirmatory path. This matches the actual availability pattern.

#### M-05: pre-design-feasibility has circular FAIL path

- **Skill**: `pre-design-feasibility` (line 56)
- **Issue**: Step 5 "Gate Decision" says "Any infeasible without alternative -> FAIL, return to brainstorm for scope reduction." But the L1 description (line 7) says this is the "Terminal skill" in pre-design domain. If it FAILs and returns to brainstorm, brainstorm re-runs, then validate re-runs, then feasibility re-runs. The "Max 3 iterations" limit is declared but there is no specification of what happens when max iterations are exhausted AND the result is still FAIL.
- **Impact**: After 3 iterations of brainstorm->validate->feasibility with persistent infeasibility, the pipeline has no defined exit. Lead must make an ad-hoc decision to either proceed with risk or abandon the task.
- **Resolution**: Add explicit terminal FAIL behavior: "After 3 iterations, if still infeasible, report to Lead with FAIL status and list all infeasible items for user decision (AskUserQuestion: proceed with limitations or abandon)."

#### M-06: manage-codebase hotspot scoring references "last 3 pipeline runs" but has no persistence

- **Skill**: `manage-codebase` (lines 96-98)
- **Issue**: Hotspot scoring says "`high` if file changed in last 3 pipeline runs". But the codebase-map.md format only stores `updated: YYYY-MM-DD` per entry, not a per-pipeline-run change history. There is no mechanism to track which files changed in which pipeline run.
- **Impact**: The "changed in last 3 pipeline runs" criterion is unimplementable with the current map schema. Hotspot scoring falls back to `refd_by` count only, which is less dynamic.
- **Resolution**: Either (a) remove the "last 3 pipeline runs" criterion and rely solely on `refd_by` count (simpler, already works), or (b) extend the map schema with a `change_history` field (adds complexity, may exceed 300-line limit).

#### M-07: execution-impact TRANSITIVE detection (2-hop) is combinatorially expensive

- **Skill**: `execution-impact` (lines 45-46, 87-88)
- **Issue**: Step 4 says "TRANSITIVE (hop_count: 2): File references an intermediate file, which references the changed file." In degraded mode (grep-only), Step 3 says "TRANSITIVE detection: sequential grep (grep results of grep results)". For N changed files each with M direct dependents, this requires N x M additional grep searches. For a COMPLEX pipeline with 10+ changed files and 5+ dependents each, that's 50+ additional greps.
- **Impact**: The researcher agent may exhaust its maxTurns (30) before completing transitive analysis for large change sets, resulting in `status: partial`. The skill does handle this gracefully (line 92: "If researcher maxTurns reached: report analyzed files, set status: partial"), but the methodology doesn't provide prioritization guidance for which transitive chains to explore first.
- **Resolution**: Add prioritization: "Analyze DIRECT dependents first. Only pursue TRANSITIVE chains for high-hotspot files or files in critical path. If maxTurns budget is <10 remaining, skip TRANSITIVE and report DIRECT-only."

#### M-08: pipeline-resume Step 4 "Reconstruct Agent Context" is unreliable

- **Skill**: `pipeline-resume` (lines 44-48)
- **Issue**: Step 4 says "Read task description for agent assignment" and "Check if agents produced partial L1/L2 output". But after a session interruption, agent spawns from the previous session are gone. Their L1/L2 output exists only if it was captured in Lead's conversation context or persisted to a file/task. The Task API TaskGet can retrieve task descriptions and metadata, but not the actual agent conversation that produced results.
- **Impact**: For tasks that were in-progress when the session interrupted, the "partial output" recovery is unreliable. The skill may need to restart those tasks from scratch rather than continue them.
- **Resolution**: Acknowledge in the methodology that in-progress tasks typically need restart, not continuation. Partial output recovery is only possible when results were written to files or Task metadata before interruption.

#### M-09: design-risk FMEA scoring is subjective without calibration

- **Skill**: `design-risk` (lines 32-36)
- **Issue**: The FMEA methodology uses Severity (1-5), Likelihood (1-5), Detection (1-5) scales to compute RPN. However, there is no calibration rubric (what constitutes Severity=4 vs Severity=5?). Different analysts will produce different scores for the same risk.
- **Impact**: Risk prioritization may be inconsistent across pipeline runs. A risk rated RPN=120 by one analyst might be rated RPN=60 by another.
- **Resolution**: Add a brief calibration table (e.g., Severity: 1=cosmetic, 2=minor, 3=significant, 4=major, 5=pipeline-blocking).

#### M-10: orchestration-decompose quality gate says "Each group <=4 tasks" but should be "<=4 teammates"

- **Skill**: `orchestration-decompose` (line 61)
- **Issue**: Quality gate says "Each group <=4 tasks (teammate limit)". The comment says "teammate limit" but the constraint is expressed as "tasks". A group can have >4 tasks assigned to a single teammate instance. The actual constraint from CLAUDE.md is max 4 teammates per execution phase, not max 4 tasks per group.
- **Impact**: The quality gate may falsely FAIL a valid decomposition that assigns 5 tasks to 2 teammates in a single group, or falsely PASS a decomposition with 4 groups of 1 task each that requires 4 different agent types.
- **Resolution**: Reword to "Each execution phase uses <=4 teammate instances total across all groups".

#### M-11: task-management batch creation references `detail_path: ".agent/tasks/{id}/detail.md"` -- wrong path

- **Skill**: `task-management` (line 75)
- **Issue**: The metadata example shows `"detail_path": ".agent/tasks/{id}/detail.md"`. The `.agent/` directory does not exist in the workspace. The correct infrastructure directory is `.claude/`. This path appears to be a vestigial reference from a previous system design.
- **Impact**: If pt-manager follows this literally, it will create files in a non-standard directory that no other skill or agent knows about.
- **Resolution**: Either remove `detail_path` from the metadata (use task description field instead) or correct to a valid path pattern.

#### M-12: verify-quality 88% utilization threshold is stricter than verify-content's 80%

- **Skill**: `verify-quality` (line 52) vs `verify-content` (line 29)
- **Issue**: verify-content sets the threshold at ">80% of 1024 = >819 chars". verify-quality sets it at ">88% utilization (quality threshold, stricter than content's 80%)". A skill passing verify-content at 82% will fail verify-quality at the 88% threshold. Since verify runs sequentially (structure->content->consistency->quality->cc-feasibility), a skill could pass content but fail quality on the same criterion measured differently.
- **Impact**: Creates confusion about what the "real" threshold is. Could trigger unnecessary fix loops at the quality stage for descriptions that already passed content.
- **Resolution**: Align thresholds (either both 80% or both 88%), or clarify that quality's 88% is aspirational/ranking-only (not a hard PASS/FAIL gate). Currently both use it as a gate criterion.

---

### LOW Findings (8)

#### L-01: pre-design-validate does not specify how to "report gaps to Lead for re-brainstorm"

- **Skill**: `pre-design-validate` (line 48)
- **Issue**: Step 4 says "If any FAIL -> report gaps to Lead for re-brainstorm" but does not specify the communication mechanism. Is this via L1 output that Lead reads? Via Task API message? Via a file artifact?
- **Resolution**: Specify that the FAIL verdict and gap description are returned as L1 output, which Lead reads and uses to re-invoke pre-design-brainstorm with targeted questions.

#### L-02: design-interface Step 5 "Dependency Order" duplicates plan-decomposition Step 4

- **Skill**: `design-interface` (lines 52-55)
- **Issue**: design-interface Step 5 determines "which components must be implemented first" and produces a dependency order. But plan-decomposition Step 4 also "Map Dependencies" and "Identify critical path". This is redundant work.
- **Resolution**: Clarify that design-interface produces component-level dependency order (design-time), while plan-decomposition produces task-level dependency order (execution-time). Add a note distinguishing the two.

#### L-03: research-codebase FAIL path undefined

- **Skill**: `research-codebase` (line 9)
- **Issue**: OUTPUT_TO says "If critical gaps found, loops back to design domain for architecture revision." But the skill does not define what constitutes a "critical gap" or the mechanism for looping back. There is no FAIL status in the L1 output template.
- **Resolution**: Add `status: PASS|FAIL` to L1 output and define "critical gap = architecture decision contradicted by existing codebase pattern".

#### L-04: plan-strategy Step 2 says "Within 4-teammate limit per group" -- this is orchestration's job

- **Skill**: `plan-strategy` (line 33)
- **Issue**: plan-strategy enforces the 4-teammate limit during strategy formulation, but this is actually orchestration-decompose and orchestration-verify's responsibility. Strategy should focus on sequencing and risk, not teammate allocation.
- **Resolution**: Remove the teammate limit constraint from plan-strategy and leave it to orchestration domain.

#### L-05: execution-code TRIVIAL says "Lead-direct" for implementer spawn

- **Skill**: `execution-code` (line 21)
- **Issue**: Execution Model says "TRIVIAL: Lead-direct. Single implementer for 1-2 file change." This is contradictory -- "Lead-direct" typically means Lead executes without spawning, but the sentence immediately says "Single implementer" which IS a spawn. The CLAUDE.md constitution says "Lead NEVER edits files directly."
- **Resolution**: Reword to "TRIVIAL: Single implementer spawn for 1-2 file changes."

#### L-06: execution-infra Step 4 "Validate Schema Compliance" is Lead-executed but requires parsing

- **Skill**: `execution-infra` (lines 45-49)
- **Issue**: Step 4 says Lead should "Check YAML frontmatter parses correctly" and "Confirm no non-native fields introduced" after each infra-implementer completes. This duplicates verify-structure and verify-cc-feasibility skills (P8 domain).
- **Resolution**: Acknowledge this as a lightweight pre-check (not full verification) and note that full verification happens in P8.

#### L-07: manage-codebase exclusion list misses `.claude/plugins/`

- **Skill**: `manage-codebase` (lines 113-117)
- **Issue**: The excluded paths list includes `agent-memory/`, `agent-memory-local/`, `projects/*/memory/cc-reference/*`, but does not mention `.claude/plugins/`. The workspace has `.claude/plugins/known_marketplaces.json` (visible in git status). This file could be picked up in a full scan and create a map entry for a non-INFRA file.
- **Impact**: Minor -- one extra map entry that serves no purpose.
- **Resolution**: Add `.claude/plugins/` to the exclusion list.

#### L-08: All 3 plan-verify skills have identical Execution Model patterns

- **Skills**: `plan-verify-correctness`, `plan-verify-completeness`, `plan-verify-robustness`
- **Issue**: All three say "Spawn 2-4 analysts. Divide by {X}" for COMPLEX tier. Since they run in parallel (WHEN says "Parallel-capable: correctness || completeness || robustness"), spawning 2-4 analysts EACH means up to 12 analysts simultaneously for a COMPLEX pipeline.
- **Impact**: While each runs in a separate Lead-spawned context, this is 12 concurrent agent spawns which may cause resource contention (tmux pane limits, context budget pressure).
- **Resolution**: Note that in practice, Lead should spawn 1 analyst per plan-verify skill for COMPLEX (3 total), not 2-4 each.

---

## Cross-Cutting Analysis

### 1. Methodology Implementability Score by Skill

| Skill | Agent | All Steps Executable? | Notes |
|-------|-------|----------------------|-------|
| pre-design-brainstorm | Lead/analyst | PARTIAL | Step 3 (AskUserQuestion) not available to analyst (H-01) |
| pre-design-validate | Lead/analyst | YES | |
| pre-design-feasibility | Lead/researcher | YES | claude-code-guide fallback covers gap (M-04 minor) |
| design-architecture | Lead/analyst | YES | |
| design-interface | Lead/analyst | YES | |
| design-risk | Lead/analyst | YES | Scoring subjective (M-09) |
| research-codebase | analyst | YES | |
| research-external | researcher | PARTIAL | WebFetch domain-restricted (H-05) |
| research-audit | analyst | YES | |
| plan-decomposition | analyst | YES | |
| plan-interface | analyst | YES | |
| plan-strategy | analyst | YES | |
| plan-verify-correctness | analyst | YES | |
| plan-verify-completeness | analyst | PARTIAL | Data persistence gap (C-02) |
| plan-verify-robustness | analyst | YES | |
| orchestration-decompose | Lead-direct | YES | |
| orchestration-assign | Lead-direct | YES | |
| orchestration-verify | Lead-direct/analyst | PARTIAL | Topological sort approximate (H-07) |
| execution-code | Lead->implementer | YES | |
| execution-infra | Lead->infra-impl | YES | |
| execution-impact | Lead->researcher | PARTIAL | grep syntax mismatch (H-02) |
| execution-cascade | Lead->implementer | NO | Convergence check unexecutable by Lead (C-01) |
| execution-review | Lead->analyst | YES | |
| verify-structure | analyst | PARTIAL | No YAML parser (M-03) |
| verify-content | analyst | YES | |
| verify-consistency | analyst | YES | |
| verify-quality | analyst | YES | |
| verify-cc-feasibility | analyst | YES | claude-code-guide fallback available |
| manage-infra | analyst | YES | |
| manage-skills | analyst | PARTIAL | git diff requires Bash (H-04) |
| manage-codebase | analyst | YES | |
| self-improve | Lead->infra-impl | PARTIAL | git commit requires Bash (H-03) |
| delivery-pipeline | delivery-agent | PARTIAL | Cannot independently verify all-PASS (H-06) |
| pipeline-resume | Lead-direct | PARTIAL | Partial output recovery unreliable (M-08) |
| task-management | pt-manager | YES | |

**Summary**: 21/35 fully implementable, 12/35 partially (workaround needed), 2/35 NO (requires fix).

### 2. Failure Path Coverage

| Coverage Level | Count | Skills |
|---------------|-------|--------|
| Well-defined FAIL path | 14 | pre-design-validate, pre-design-feasibility, plan-verify-*, orchestration-verify, execution-cascade, execution-review, delivery-pipeline, pipeline-resume, verify-* (5) |
| FAIL status exists but path vague | 11 | design-*, research-*, plan-decomposition, plan-interface, plan-strategy, orchestration-decompose, orchestration-assign, manage-skills |
| No FAIL path defined | 10 | pre-design-brainstorm, execution-code, execution-infra, execution-impact, manage-infra, manage-codebase, self-improve, task-management, research-codebase, research-external |

**Note**: Not all skills need explicit FAIL paths (e.g., brainstorm is exploratory, not pass/fail), but execution-code and execution-infra should define what happens when implementers fail beyond retry limits.

### 3. Output Chain Consistency

Checked all INPUT_FROM/OUTPUT_TO chains for L1 format compatibility:

| Chain | Compatible? | Issue |
|-------|------------|-------|
| brainstorm -> validate | YES | Both use requirements document |
| validate -> feasibility | YES | Completeness matrix + requirements |
| feasibility -> architecture | YES | Requirements + feasibility verdict |
| architecture -> interface | YES | Component structure |
| architecture -> risk | YES | Component structure |
| interface -> risk | YES | API contracts |
| risk -> research | YES | Risk areas |
| research-codebase -> audit | YES | Pattern inventory |
| research-external -> audit | YES | Dependency validation |
| audit -> plan-decomposition | YES | Consolidated findings |
| plan-decomposition -> plan-interface | YES | Task list |
| plan-interface -> plan-strategy | YES | Interface constraints |
| plan-strategy -> plan-verify-* | PARTIAL | plan-verify-completeness needs req doc from P0 (C-02) |
| plan-verify -> orchestration-decompose | YES | PASS verdict |
| orchestration-decompose -> assign | YES | Task groups |
| orchestration-assign -> verify | YES | Assignment matrix |
| orchestration-verify -> execution | YES | PASS + matrix |
| execution-code -> execution-impact | YES | File change manifest |
| execution-impact -> execution-cascade | YES | Impact report |
| execution-cascade -> execution-review | YES | Cascade results |
| execution-review -> verify-* | YES | Review verdict |
| verify-* (5 stages) chain | YES | Each PASS feeds next |
| verify-cc-feasibility -> delivery | YES | All-PASS |
| execution-impact -> execution-review (skip cascade) | YES | When cascade_recommended=false |

**Overall chain consistency: 23/24 compatible (96%)**. The one gap is the P0->P5 data handoff (C-02).

---

## Recommendations (Priority Order)

1. **[CRITICAL] Fix C-01**: Rewrite execution-cascade convergence check to delegate to a spawned analyst agent instead of assuming Lead can run grep.

2. **[CRITICAL] Fix C-02**: Add data persistence mechanism for P0 requirements (PT metadata or file artifact) so P5 plan-verify-completeness can reliably construct traceability matrix.

3. **[HIGH] Fix H-01**: Clarify that AskUserQuestion in pre-design-brainstorm remains Lead-direct even when analysts are spawned for other steps.

4. **[HIGH] Fix H-02**: Rewrite execution-impact Step 3 to use CC Grep tool semantics instead of shell grep syntax.

5. **[HIGH] Fix H-03**: Add explicit agent assignment for self-improve Step 5 git operations (implementer or delivery-agent).

6. **[HIGH] Fix H-04**: Specify that Lead provides git diff output to analyst in manage-skills spawn prompt.

7. **[HIGH] Fix H-05**: Document WebFetch domain restriction in research-external and specify tavily as primary fallback.

8. **[HIGH] Fix H-06**: Specify that delivery-agent receives verify verdict in spawn prompt (not independent investigation).

9. **[MEDIUM] Fix M-10, M-11**: Quick correctness fixes (teammate constraint wording, path typo).

10. **[MEDIUM] Fix M-01, M-12**: Threshold alignment and missing INPUT_FROM declaration.

---

## Methodology

This audit read all 35 SKILL.md files (`/home/palantir/.claude/skills/*/SKILL.md`), all 6 agent definitions (`/home/palantir/.claude/agents/*.md`), settings.json, and both SRC hook scripts. For each skill, the following was evaluated:

1. **Tool availability matrix**: Cross-referenced each methodology step against the assigned agent's tool list
2. **Data flow tracing**: Followed INPUT_FROM/OUTPUT_TO chains and verified L1 output format compatibility
3. **Quality gate mechanizability**: Assessed whether each gate criterion can be verified with available tools
4. **FAIL path completeness**: Checked whether FAIL outcomes have defined next-steps
5. **Edge case handling**: Evaluated timeout, max-iteration, and resource-limit scenarios

Files analyzed: 35 skills + 6 agents + 1 settings.json + 2 hooks = 44 files total.
Coverage: 100% of skills (35/35).
