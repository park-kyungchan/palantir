# Pipeline Rollback Protocol v1.0

> Referenced by: plan-validation-pipeline, verification-pipeline, agent-teams-execution-plan
> Source: GAP-5 (Pipeline Rollback Protocol Absent)

## 1. Supported Rollback Paths

| From | To | Trigger |
|------|----|---------|
| P5 | P4 | Validation FAIL — critical design flaws |
| P6 | P4 | Implementation reveals design inadequacy |
| P6 | P3 | Architecture fundamentally insufficient |
| P7 | P6 | Test failures requiring code changes |
| P7 | P4 | Test failures revealing design flaws |
| P8 | P6 | Integration failures requiring implementation fixes |

Rolling back >2 phases (e.g., P7→P3) requires explicit user confirmation via AskUserQuestion.

## 2. Rollback Procedure

### Step 1: Freeze

All active agents save their current state:
1. Each agent writes L1/L2/L3 with current progress (even if incomplete)
2. Coordinator writes `progress-state.yaml` (if applicable)
3. Lead creates `rollback-record.yaml` in the current phase directory:

```yaml
rollback:
  from_phase: P{N}
  to_phase: P{M}
  reason: "{specific reason for rollback}"
  trigger: "{gate FAIL | user request | blocker escalation}"
  timestamp: {ISO 8601}
  pt_version: PT-v{N}
  gc_version: GC-v{N}
  artifacts_preserved:
    - path: "{L1/L2/L3 paths from current phase}"
  revision_targets:
    - "{specific section or component that needs revision}"
```

4. Lead shuts down all active agents (SendMessage type: shutdown_request)
5. Lead calls TeamDelete to clean up team resources

### Step 2: Invalidate Downstream

Update PERMANENT Task phase status:
- Mark rolled-back phases as `ROLLED_BACK` (not deleted)
- Preserve all artifacts — do NOT delete any phase directories
- Example: P7→P4 rollback marks P5, P6, P7 as `ROLLED_BACK`

### Step 3: Prepare Re-Entry

Create rollback context for the target phase:
1. Read `rollback-record.yaml` for revision targets
2. Read prior-attempt artifacts (L2 summaries from rolled-back phases)
3. Construct re-entry directive with:
   - Original PT context (via TaskGet)
   - Specific revision targets from rollback record
   - Prior-attempt lessons (what failed and why)
   - Preserved artifacts as reference (not starting point)

### Step 4: Re-Invoke Target Phase

1. Create new session directory (new team via TeamCreate)
2. PT remains the authority — read via TaskGet
3. Invoke the appropriate skill for the target phase
4. The skill detects rollback context via `rollback-record.yaml` presence
5. Agents receive prior-attempt context in their directives

## 3. Rollback Detection (Input Discovery)

All pipeline skills should check for rollback context during input discovery:

```
Check for rollback-record.yaml in downstream phase directories.
If found:
  1. Read rollback-record.yaml for revision targets and reason
  2. Read prior-attempt L2 summaries for lessons learned
  3. Include rollback context in agent directives:
     - What was attempted previously
     - Why it was rolled back
     - Specific revision targets
  4. Proceed with phase execution using enriched context
```

## 4. Constraints

- **Never delete artifacts** — rolled-back phase outputs are learning material
- **Always preserve PT** — rollback updates PT status but never removes content
- **User confirmation required** for >2 phase rollback distance
- **Max 2 rollbacks** to the same phase before escalating to user for fundamental reassessment
- **RTD logging** — record rollback as a Decision Point in rtd-index.md
