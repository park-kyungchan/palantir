# audit-impact — Detailed Methodology Reference

Loaded on-demand from SKILL.md. Contains full algorithm detail, DPS templates, severity tables, and failure protocols.

---

## Propagation Trace Algorithm

### Step 1: Ingest Input Sources

Read **research-codebase** L1/L2 to extract:
- File inventory with roles and module boundaries
- Existing dependency patterns (import chains, config references)
- Component interaction patterns

Read **research-external** L2 for:
- Known constraints on change propagation (breaking change rules, semver implications)
- Community-reported cascading failure patterns

Read **design-risk** L1/L2 for:
- Risk matrix with identified risk items ranked by level
- Architecture decisions with change scope boundaries
- (Optional for STANDARD: fall back to design-architecture component scope if absent)

### Step 2: Trace Change Propagation Paths

Starting from each design change point (component being added/modified/removed):

**DIRECT Impact (1 hop):**
- Files that directly import or reference the changed component
- Configuration files that directly configure the changed component
- Test files that directly test the changed component
- Record: `changed_file -> affected_file` with reference type and `file:line`

**TRANSITIVE Impact (2+ hops):**
- Files that depend on directly affected files (second-order effects)
- Follow chains up to 3 hops maximum (beyond 3 hops: speculative, do not trace)
- Record: `changed_file -> hop1 -> hop2 [-> hop3]` with per-hop chain evidence

For each path, document:
- Change origin (which design decision triggers this path)
- Each hop with `file:line` evidence of the dependency
- Terminal node (the final affected file in the chain)

### Step 3: Propagation Depth Decision Table

| Change Scope | Strategy | maxTurns |
|---|---|---|
| Isolated (≤3 change points, ≤2 direct dependents each) | DIRECT only — skip transitive | 20 |
| Moderate (4–8 change points) | DIRECT + TRANSITIVE up to 2 hops | 25 |
| Broad (>8 change points or hub-touching) | Full 3-hop TRANSITIVE — spawn 2 analysts | 25 each |
| Default (STANDARD tier) | DIRECT + 2-hop TRANSITIVE | 25 |

**4+ hop boundary**: Chains exceeding 3 hops are flagged as "potential deep impact" in the output without further tracing. This is a hard cap — do not speculate beyond it.

**1-hop example**: `auth.service.ts` changes → `user.controller.ts` imports auth service directly → DIRECT.

**2-hop chain example**: `auth.service.ts` → `user.controller.ts` → `api.router.ts` (router imports controller) → TRANSITIVE (2-hop).

**3-hop chain example**: `auth.service.ts` → `user.controller.ts` → `api.router.ts` → `app.ts` (app mounts router) → TRANSITIVE (3-hop, cap reached).

---

## Severity Classification

### Per-Path Severity Criteria

| Severity | Criteria | Example |
|---|---|---|
| CRITICAL | Change breaks existing interface contract, no backward compatibility | Removing a function called by 5+ files |
| HIGH | Change requires modifications in dependent files, significant rework | Changing a function signature used by 3+ callers |
| MEDIUM | Change requires minor updates in dependents, backward-compatible approach exists | Adding optional parameter to existing function |
| LOW | Change is self-contained, dependents unaffected | Internal refactor with stable public interface |

### Severity Escalators (apply after base classification)

- Path crosses module boundaries: +1 severity level
- No test coverage for affected files: +1 severity level
- Multiple design decisions converge on the same propagation path: +1 severity level

Maximum after escalation: CRITICAL (capped, cannot escalate above CRITICAL).

---

## Maintenance and Scalability Risk Assessment

### Maintenance Risk (per affected module)

- Does this change increase coupling? (more edges in dependency graph)
- Does it create new single points of failure? (new hotspot nodes)
- Does it increase the blast radius of future changes?

Rate each dimension as HIGH/MEDIUM/LOW with one-sentence justification.

### Scalability Risk (per architecture decision)

- Will this change pattern work if the codebase grows 2x? 5x?
- Are the propagation paths manageable at scale?
- Does the architecture decision create linear or exponential dependency growth?

Rate each dimension as HIGH/MEDIUM/LOW with one-sentence justification.

---

## Shift-Left Prediction Format

This output is consumed directly by **execution-impact** (P6) via `$ARGUMENTS` referencing `tasks/{team}/p2-audit-impact.md`.

The Shift-Left section in the L2 output must be structured as follows:

```yaml
shift_left:
  baseline_paths:
    - origin: "<changed_file>"
      type: DIRECT|TRANSITIVE
      hops: 1|2|3
      terminal: "<affected_file>"
      severity: CRITICAL|HIGH|MEDIUM|LOW
      evidence: "<file:line>"
  high_risk_modules:
    - module: "<module_name>"
      maintenance_risk: HIGH|MEDIUM|LOW
      scalability_risk: HIGH|MEDIUM|LOW
  validation_instructions: |
    P6 execution-impact should verify these predicted paths against actual
    code changes. Paths that do not materialize → document as false positives.
    New paths not in this baseline → document as scope expansion.
```

P2 predicts; P6 validates predictions against real changes. This avoids redundant re-analysis at execution time.

---

## DPS Template — Impact Analysts

### COMPLEX Tier (2 Sequential Analysts)

**Context (D11 priority: cognitive focus > token efficiency)**:
- INCLUDE: research-codebase L1 file inventory + dependency patterns; research-external L2 change propagation constraints; design-risk L1 risk matrix with change points.
- EXCLUDE: Other audit dimensions' results (static/behavioral/relational); pre-design conversation history; full pipeline state (P2 phase only).
- Budget: Context field ≤ 30% of teammate effective context.

**Analyst-1 (DIRECT)**:
- Task: "From each design change point, trace all 1-hop DIRECT impacts: files that import, reference, or configure the changed component. Record each path with `file:line` evidence. Output edge list to `tasks/{team}/p2-audit-impact-direct.md`."
- Constraints: Read-only analysis (analyst agent, no Bash). No recommendations. maxTurns: 25.
- COMM_PROTOCOL NOTIFY: Analyst-2 — signal `"READY|path:tasks/{team}/p2-audit-impact-direct.md|fields:direct_edges"`

**Analyst-2 (TRANSITIVE)**:
- Task: "Read Analyst-1 DIRECT edge list from `tasks/{team}/p2-audit-impact-direct.md`. Trace 2-3 hop TRANSITIVE chains from each directly impacted file. Cap at 3 hops. Record full chain with per-hop evidence."
- AWAIT: Analyst-1 input-ready signal.
- Constraints: Read-only. Cap at 3 hops. maxTurns: 25.
- Delivery: Write consolidated output to `tasks/{team}/p2-audit-impact.md`. Send Ch3 micro-signal to Lead: `"PASS|direct:{N}|transitive:{N}|ref:tasks/{team}/p2-audit-impact.md"`. Send Ch4 P2P to research-coordinator.

### STANDARD Tier (Single Analyst)

Single analyst traces both DIRECT and TRANSITIVE in one pass. maxTurns: 25.
- Output: `tasks/{team}/p2-audit-impact.md`
- Delivery: Ch3 micro-signal + Ch4 P2P to research-coordinator.

### TRIVIAL Tier

Lead-direct inline. Check 1-2 change points for obvious direct dependents. No formal DPS. No agent spawn.

---

## Failure Protocols

### No Propagation Paths Found

- **Cause**: Design changes are entirely self-contained with no external dependencies.
- **Action**: Report `direct: 0, transitive: 0`. This is valid for isolated additions.
- **Route**: research-coordinator with empty impact set and explanation.

### Design-Risk Input Missing

- **Cause**: P1 design-risk did not produce a risk matrix (TRIVIAL/STANDARD tier may skip P1 risk).
- **Action**: Proceed without risk matrix. Use design-architecture component scope as fallback for change points.
- **Route**: Continue normally. Note reduced confidence in risk assessment in L1 YAML (`confidence: reduced`).

### Propagation Chain Too Deep

- **Cause**: Transitive chains would exceed 3 hops; further analysis becomes speculative.
- **Action**: Cap at 3 hops. Report deeper chains as "potential deep impact" without tracing further.
- **Route**: research-coordinator with depth cap noted in L1 signal.
