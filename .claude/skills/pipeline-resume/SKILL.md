---
name: pipeline-resume
description: |
  [X-Cut·Resume·Recovery] Pipeline resume after session interruption. Reads RTD (Real-Time Documentation) to identify last completed domain and decision point, reconstructs pipeline state, and resumes from the interrupted domain.

  WHEN: Session continuation after interruption. Previous pipeline active but not completed. User invokes /pipeline-resume or Lead detects incomplete pipeline state.
  DOMAIN: Cross-cutting (session recovery). Independent of pipeline sequence.

  METHODOLOGY: (1) Read .agent/observability/{slug}/rtd-index.md for decision history, (2) Identify last completed domain and decision point, (3) Read orchestration-plan.md for teammate status, (4) TaskGet PERMANENT Task for full context, (5) Determine resume point (which domain to restart), (6) Re-spawn agents with fresh context from PT, (7) Resume pipeline from interrupted domain.
  PREREQUISITE: RTD data exists (.agent/observability/ directory). Falls back to manual recovery if absent.
  OUTPUT_FORMAT: L1 YAML resume state (last domain, resume domain, active teammates), L2 markdown recovery report with context reconstruction.
user-invocable: true
disable-model-invocation: true
input_schema:
  type: object
  properties:
    session_id:
      type: string
      description: "Session ID to resume (default: most recent)"
    resume_from:
      type: string
      description: "Domain to resume from (default: auto-detect from RTD)"
  required: []
---

# Pipeline — Resume

## Output

### L1
```yaml
domain: cross-cutting
skill: pipeline-resume
last_completed_domain: ""
resume_domain: ""
decision_point: ""
teammates_restored: 0
```

### L2
- RTD recovery summary
- Pipeline state reconstruction
- Resume point with rationale
