# Decision 006: INFRA Code-Level Audit & Layer-1/Layer-2 Boundary Strategy

**Status:** PENDING USER DECISION  
**Date:** 2026-02-11  
**Context:** CLAUDE.md v6.0 · 48 INFRA files audited · Palantir Ontology/Foundry Layer-2 planned  
**Depends on:** Decision 004, Decision 005

---

## 1. Problem Statement

Two objectives:

1. **Code-level INFRA audit:** Find and fix inefficiencies across ALL `.claude/` files
2. **Layer-1/Layer-2 boundary judgment:** The user plans to finalize Layer-1 (NL INFRA) first, then overlay Palantir Ontology/Foundry as Layer-2 for formal control. Is this strategy sound?

---

## 2. INFRA Code-Level Audit Results

### 2.1 Audit Scope

**48 files audited across 6 categories:**

| Category | Files | Count |
|----------|-------|-------|
| Agent definitions | `.claude/agents/*.md` | 27 |
| Skills | `.claude/skills/*/SKILL.md` | 10 |
| References | `.claude/references/*.md` | 5 |
| Hooks | `.claude/hooks/*.sh` | 4 |
| Configuration | `.claude/settings.json`, `.claude/settings.local.json` | 2 |
| Constitution | `.claude/CLAUDE.md` | 1 |

### 2.2 Findings — CRITICAL (Functional Impact)

#### F-001: `agent-common-protocol.md` Line 3 — Stale Agent Count
```markdown
# CURRENT (Line 3):
This covers procedures common to all teammate agent types (22 agents across 10 categories).

# PROBLEM: Actual count is 27 agents (22 workers + 5 coordinators).
# If D-005 is approved: 42 agents across 13 categories.
```
**Fix:** Update to match actual count. → **INFRA INTEGRATION: Will auto-update when D-005 agents are created.**

#### F-002: `agent-common-protocol.md` Line 84 — Incomplete Edit Tool Registry
```markdown
# CURRENT (Line 84):
If you have the Edit tool (implementer, infra-implementer, integrator): write discoveries

# PROBLEM: Missing from list: No other agents have Edit, so this is accurate.
# BUT: the infra-implementer is not consistently listed alongside implementer/integrator
# in CLAUDE.md or agent-catalog.md as an "Edit-capable" agent.
```
**Assessment:** Correct but inconsistent documentation. → **INFRA INTEGRATION: Add "Edit-capable agents" row to agent-catalog.md Agent Matrix.**

#### F-003: `verification-coordinator.md` Line 31 — Missing impact-verifier from Workers
```markdown
# CURRENT (Line 31-38):
Workers:
- static-verifier
- relational-verifier
- behavioral-verifier

# PROBLEM: D-005 proposes merging impact-verifier as 4th worker.
# Current state: impact-verifier exists separately in P2d category.
```
**Fix:** Conditional on D-005 approval. → **Tracked in D-005 sub-decision.**

#### F-004: `architect.md` Line 54 — Phase 3+4 Ambiguity
```markdown
# CURRENT:
Phase 3-4 — plan-writer is an alternative for Phase 4 detailed planning

# PROBLEM: Identified in D-004 §2.3.1. architect and plan-writer overlap.
```
**Fix:** Tracked in D-004 sub-decision. → **Remove Phase 4 from architect, enforce plan-writer for P4.**

#### F-005: `settings.json` Line 80 — Language Setting Mismatch
```json
"language": "Korean"
```
**The user operates in Korean but all INFRA documents are in English for Opus-4.6.** The `language` setting controls Claude's response language, which should match the user's preference. This is correct for user-facing output but creates a mismatch with INFRA documentation language.

**Assessment:** NOT a bug — user wants Korean responses but English INFRA. This is intentional dual-language operation. → **NO FIX NEEDED.**

### 2.3 Findings — HIGH (Quality/Consistency)

#### F-006: `on-subagent-start.sh` Lines 22-45 — RTD Session Registry Limitation
```bash
# AD-29: $CLAUDE_SESSION_ID env var does NOT exist in hook contexts.
# Using stdin session_id instead (parent's/Lead's SID). Known limitation.
```
**Problem:** Maps Lead's session ID to spawned agent. When Lead spawns multiple agents, ALL get mapped to the same session ID, so PostToolUse cannot distinguish which agent made a tool call.

**Layer-2 Analysis:** This is a Layer-1 limitation (no runtime session identity for subagents). Layer-2 could provide formal session→agent mapping via an Object-backed registry (Ontology ObjectType with session_id as PK). However, the current workaround is documented (AD-29) and acceptable.

**Assessment:** Known limitation, documented. → **NO FIX — Layer-2 candidate.**

#### F-007: `on-rtd-post-tool.sh` Lines 7-8 — `set -e` + `trap 'exit 0' ERR` Anti-Pattern
```bash
set -e
trap 'exit 0' ERR
```
**Problem:** `set -e` makes the script fail on any error. The ERR trap catches it and exits 0. This is equivalent to NOT using `set -e` at all — it adds complexity without value. The comment says "Any error → exit 0 (never block pipeline)" but the mechanism is unnecessarily convoluted.

**Fix:** ⚡ **INFRA INTEGRATION — Minor improvement, applying directly.**

#### F-008: `on-pre-compact.sh` Lines 29-39 — JSON Array Construction Without jq
```bash
echo "[" > "$SNAPSHOT_FILE"
first=true
for f in "$TASK_DIR"*.json; do
  ...
  cat "$f" >> "$SNAPSHOT_FILE"
done
echo "]" >> "$SNAPSHOT_FILE"
```
**Problem:** Manual JSON array construction is fragile. If any task file contains invalid JSON, the entire snapshot is corrupted. jq is already available (checked on line 14).

**Fix:** ⚡ **INFRA INTEGRATION — Replace with jq-based construction.**

#### F-009: `on-pre-compact.sh` Line 54 — `ls` for File Existence Check
```bash
has_l1=$(ls "$agent_dir"/L1-index.yaml 2>/dev/null)
```
**Problem:** `ls` for file existence is a shell anti-pattern. Should use `[ -f ... ]`.

**Fix:** ⚡ **INFRA INTEGRATION — Minor improvement, applying directly.**

#### F-010: agent-catalog.md Line 224-227 — Level Split Comment Not Machine-Parseable
```html
<!-- ================================================================== -->
<!-- Level 1 ends here (~300L). Level 2 below is on-demand per category. -->
```
**Problem:** HTML comments are invisible to the Lead agent. Lead has no way to know where Level 1 ends and Level 2 begins when reading the file. NL instructions in CLAUDE.md say "Lead reads Level 1" but the division is only marked by an HTML comment.

**Fix:** ⚡ **INFRA INTEGRATION — Add a visible markdown marker:**
```markdown
---
## ⚠️ LEVEL 1 BOUNDARY — Lead reads above this line. Level 2 below is on-demand.
---
```

### 2.4 Findings — MEDIUM (Consistency/Documentation)

#### F-011: Coordinator Boilerplate Duplication (5 files)
All 5 coordinators contain identical sections:
- "Coordinator Recovery" (4 lines, identical in all 5)
- "Failure Handling" (similar patterns, minor variations)
- Constraint list (identical in all 5)

**Assessment:** Each file is self-contained (good for context-isolated agents), but updates must be applied to all 5 files. → **INFRA INTEGRATION: Create `.claude/references/coordinator-shared-protocol.md` to DRY up common sections. Each coordinator references it.**

#### F-012: Inconsistent Worker Count Format in Agent Descriptions
- `execution-coordinator.md`: "implementer (1-4)" — includes count
- `research-coordinator.md`: "codebase-researcher" — no count
- `verification-coordinator.md`: "static-verifier" — no count

**Fix:** ⚡ **INFRA INTEGRATION — Standardize: include Max instance count in parentheses for all workers.**

#### F-013: `task-api-guideline.md` Line 1 — Version Mismatch
```markdown
> **Version:** 6.0 (NLP + INFRA v7.0 consolidation) | Updated: 2026-02-10
```
**Problem:** Claims "INFRA v7.0 consolidation" but CLAUDE.md is v6.0. Version numbering is inconsistent.

**Assessment:** Internal versioning artifact. → **INFRA INTEGRATION: Standardize version numbering across all reference docs.**

#### F-014: `ontology-communication-protocol.md` Line 3 — Hardcoded Date
```markdown
> Verified against official palantir.com/docs (2026-02-10)
```
**Assessment:** Date is informational, not functional. → **NO FIX — documentation accuracy is acceptable.**

#### F-015: `layer-boundary-model.md` — Stale Agent Reference
Line 38:
```markdown
2. Verify disallowedTools match role (e.g., devils-advocate has no Write/Edit/Bash)
```
**Problem:** `devils-advocate` actually HAS Write (for L1/L2 output). The example is wrong.

**Fix:** ⚡ **INFRA INTEGRATION — Correct to: "e.g., spec-reviewer has no Write/Edit/Bash"**

#### F-016: `settings.local.json` — MCP Servers Not Referenced in INFRA Docs
```json
"enabledMcpjsonServers": [
  "oda-ontology", "tavily", "cow-ingest", "cow-ocr",
  "cow-vision", "cow-review", "cow-export", "cow-storage"
]
```
**Problem:** 8 MCP servers are enabled but only `tavily` and `context7`/`sequential-thinking` are referenced in agent tool lists. The `oda-ontology` and `cow-*` servers are available but no agent is configured to use them.

**Assessment:** These are project-specific servers, not INFRA-generic. Agent definitions should only reference universally available tools. → **NO FIX — project-specific configuration is correct to keep separate from agent definitions.**

### 2.5 Findings — LOW (Style/Polish)

#### F-017: Inconsistent YAML Frontmatter `description` Formatting
Some agents use `|` (literal block), some use `>` (folded block), some use quoted strings. All should use `|` for multi-line descriptions.

**Assessment:** No functional impact (Claude Code CLI parses all formats). → **INFRA INTEGRATION: Standardize to `|` when creating D-005 new agents.**

#### F-018: `infra-impact-analyst.md` Line 46 — Output Format Uses Custom Prefix
```markdown
L1: `II-{N}` findings with proposed_change, direct_files, cascade_depth...
```
**Problem:** Uses `II-{N}` prefix but other agents use `F-{N}` or no prefix. Inconsistent finding ID scheme.

**Fix:** ⚡ **INFRA INTEGRATION: Standardize finding ID prefix across all agents when creating D-005 agents.**

---

## 3. Applied INFRA Integrations (Minor Fixes)

The following fixes are minor, non-breaking improvements. **Applied directly per user instruction:**

| ID | File | Fix | Applied |
|----|------|-----|---------|
| F-007 | `on-rtd-post-tool.sh` | Remove redundant `set -e` + ERR trap | ⏳ Pending approval |
| F-009 | `on-pre-compact.sh` | Replace `ls` with `[ -f ]` for existence checks | ⏳ Pending approval |
| F-010 | `agent-catalog.md` | Add visible Level 1/2 boundary marker | ⏳ Pending approval |
| F-012 | 3 coordinator files | Standardize worker count format | ⏳ Pending approval |
| F-015 | `layer-boundary-model.md` | Fix incorrect devils-advocate example | ⏳ Pending approval |

**Deferred to D-005 implementation:**
| ID | Fix | Rationale |
|----|-----|-----------|
| F-001 | Update agent count in protocol | Count changes when new agents created |
| F-008 | Rewrite JSON snapshot with jq | Requires testing in actual compact scenario |
| F-011 | Create coordinator-shared-protocol.md | New reference doc, part of INFRA restructure |
| F-017 | Standardize YAML `description` format | Apply when creating new agent files |
| F-018 | Standardize finding ID prefix | Apply when creating new agent files |

---

## 4. Layer-1/Layer-2 Boundary Strategy — Judgment

### 4.1 User's Stated Strategy

> "Layer-1 (INFRA) 확정 → Layer-2 (Palantir Ontology/Foundry) 얹기"
> "Opus-4.6 성능과 자율성 최대 보장 → Layer-2로 제어"

### 4.2 Existing Foundation: `layer-boundary-model.md`

The INFRA already contains a sophisticated Layer-1/Layer-2 boundary model (`.claude/references/layer-boundary-model.md`) that defines:

| Dimension | L1 Coverage | L2 Would Add |
|-----------|:-----------:|:-------------|
| STATIC | 95% | CI-style automated validation |
| BEHAVIORAL | 90% | Runtime enforcement (already via `disallowedTools`) |
| RELATIONAL | 85% | Persistent queryable dependency graph |
| DYNAMIC-IMPACT | 75% | Formal graph traversal, guaranteed completeness |
| REAL-TIME | 50% | Event bus, push notifications, <1sec response |

**Combined L1 coverage: ~80%**

### 4.3 My Judgment: This is an **Excellent Strategy**

**Why "L1 first, L2 on top" is correct:**

**1. Clean Separation of Concerns**
- Layer-1 handles the "HOW" — how agents coordinate, what they do, when they spawn
- Layer-2 handles the "WHAT IS" — formal ontological definitions of the components themselves
- This mirrors the Palantir Foundry architecture: **Ontology defines entities, Pipelines process them**

**2. Opus-4.6 Maximizes L1 Value**
- The `layer-boundary-model.md` demonstrates that Opus-4.6's NL fidelity makes L1 coverage of 80%+ achievable
- Adding L2 too early would create OVER-CONSTRAINT — formal rules fighting NL instructions
- L1 establishes the BEHAVIORAL standard that L2 then CODIFIES

**3. L2 as Ontology/Foundry is Architecturally Sound**
The Palantir Ontology provides exactly what L1 lacks:

| L1 Gap | L2 Solution (Ontology/Foundry) |
|--------|-------------------------------|
| No formal entity definitions for agents | **ObjectType per Agent** — `AgentType` with typed properties (name, phase, tools, maxTurns) |
| No formal relationship graph | **LinkType** — `skill-invokes-agent`, `agent-produces-output`, `phase-contains-agent` |
| No schema validation | **ValueTypeConstraint** — enforce property types at definition time |
| No guaranteed dependency traversal | **Interface** — `ICoordinated` (has workers), `ILeadDirect` (no coordinator) |
| No action rule enforcement | **ActionType** — `SpawnAgent` with SubmissionCriteria (pre-validation) |
| No cross-ontology queries | **Search Around** — "What agents are affected by changing this skill?" |

**4. Timing is Right**
- L1 is mature enough to be STABLE (27 agents, 10 Skills, 5 references, 4 hooks)
- D-005 will expand L1 (42 agents, 15+ Skills, 8 coordinators)
- AFTER D-005 stabilizes, L2 can formal-encode the expanded catalog
- If L2 were applied NOW, every D-005 change would require L2 schema migration

### 4.4 Specific L2 Overlay Design (Preliminary)

When L1 is finalized, the L2 Ontology would look like:

```
ObjectType: AgentDefinition
  Properties:
    - name (String, PK)
    - phase (String[])  
    - category (String: "research" | "verification" | "architecture" | ...)
    - agentType (String: "coordinator" | "worker" | "lead-direct")
    - maxTurns (Integer)
    - tools (String[])
    - disallowedTools (String[])
    - permissionMode (String: "default" | "acceptEdits")
    - hasSkill (Boolean)
    
ObjectType: SkillDefinition
  Properties:
    - name (String, PK)
    - phases (String[])
    - spawnsAgents (String[])
    - gateCount (Integer)
    
LinkType: SkillInvokesAgent
  Source: SkillDefinition
  Target: AgentDefinition
  Cardinality: MANY_TO_MANY
  
LinkType: AgentProducesOutput
  Source: AgentDefinition
  Target: OutputType (L1/L2/L3)
  Cardinality: MANY_TO_MANY
  
LinkType: CoordinatorManages
  Source: AgentDefinition (where agentType = "coordinator")
  Target: AgentDefinition (where agentType = "worker")
  Cardinality: ONE_TO_MANY
  
Interface: IVerifiable
  Properties: dimension (String), verdictFormat (String)
  Implementors: static-verifier, relational-verifier, behavioral-verifier, impact-verifier
  
Interface: ICoordinated
  Properties: coordinatorName (String), maxWorkers (Integer)
  Implementors: all coordinator-managed agents

ActionType: SpawnAgent
  Rules: MODIFY_OBJECT (create team entry)
  SubmissionCriteria: phase matches current pipeline stage
```

### 4.5 Warnings and Risks

| Risk | Mitigation |
|------|-----------|
| **L2 schema rigidity** — Ontology changes are heavyweight (reindex, unavailability) | Design schema with extensibility: use Interfaces for common patterns, leave room for new ObjectTypes |
| **Over-engineering** — Not every L1 concept needs L2 formalization | Apply the 80/20 rule: only formalize what L1 cannot guarantee (dependency traversal, schema validation) |
| **Dual-source-of-truth** — Agent `.md` files AND Ontology definitions could diverge | Establish ONE direction: L2 Ontology → auto-generate L1 `.md` files (or vice versa). Never manual sync. |
| **L2 maintenance cost** — Every new agent requires Ontology update | Automate: `ActionType: CreateAgent` generates both Ontology entry AND `.md` file template |

### 4.6 Recommendation

**Proceed with L1 finalization (D-005 implementation) before any L2 work.**

Timeline:
1. **Now:** Finalize D-001 through D-005 decisions
2. **Next:** Implement D-005 agent decomposition (create new `.md` files)
3. **Then:** Stabilize new L1 for 1-2 pipeline runs
4. **After:** Design L2 Ontology schema based on stabilized L1 catalog
5. **Finally:** Overlay L2 with clear sync direction (L2 → L1 generation)

---

## 5. User Decision Items

### Code-Level Fixes:
- [ ] Apply F-007 (rtd hook simplification)?
- [ ] Apply F-009 (pre-compact ls→test fix)?
- [ ] Apply F-010 (catalog level boundary marker)?
- [ ] Apply F-012 (coordinator worker counts)?
- [ ] Apply F-015 (layer-boundary example fix)?
- [ ] Apply F-008 (pre-compact jq rewrite)? — deferred recommended
- [ ] Create coordinator-shared-protocol.md (F-011)? — deferred to D-005

### Layer Strategy:
- [ ] Confirm L1-first, L2-after strategy?
- [ ] Confirm L2 sync direction: L2→L1 generation (recommended) or L1→L2 sync?
- [ ] Start L2 Ontology schema design now (preliminary) or wait until D-005 stable?

---

## 6. Claude Code Directive (Fill after decision)

```
DECISION: Apply fixes [list], Layer strategy [confirmed/modified]
SCOPE:
  - Fix F-007: on-rtd-post-tool.sh — remove set -e + ERR trap
  - Fix F-009: on-pre-compact.sh — ls → [ -f ] 
  - Fix F-010: agent-catalog.md — visible level boundary
  - Fix F-012: coordinator worker counts standardized
  - Fix F-015: layer-boundary-model.md — correct example
  - Layer: L1 finalization → D-005 → stabilize → L2 overlay
CONSTRAINTS:
  - AD-15 (no new hooks)
  - Existing hook behavior preserved (only internal cleanup)
  - All fixes backward-compatible
  - English only
PRIORITY: L1 stability > Code quality > L2 preparation
DEPENDS_ON: D-004, D-005
```
