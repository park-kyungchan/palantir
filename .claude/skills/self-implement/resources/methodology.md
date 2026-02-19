# Self Implement — Detailed Methodology

> On-demand reference. Contains implementation wave DPS templates, verification checklist, memory update DPS, and commit procedure.

---

## Step 2 — Wave DPS Construction

Construct each infra-implementer delegation prompt with:

### CONTEXT field (D11 priority: cognitive focus > token efficiency)

```
INCLUDE:
  - Specific findings for this wave with severity, category, and file:line evidence
  - CC native field reference from cc-reference cache
  - For description edits: current character count and the 1024-char limit

EXCLUDE:
  - Other waves' findings
  - Pipeline state and manage-infra internal data
  - Historical rationale for existing field values

Budget: context ≤ 30% of implementer context window
```

### TASK field

For each file, specify the exact change:
- "Remove field `X` from `path/to/file.md`"
- "Change value `A` to `B` in `path/SKILL.md line N`"
- "Add field `X: value` after field `Y` in `path/agent.md`"

Provide target value wherever possible. Never use vague instructions like "fix the description".

### CONSTRAINTS field

- Write and Edit tools only — no Bash
- Files in this wave must not overlap with other concurrent infra-implementers
- Only modify files listed in this wave's findings
- Do not restructure sections not mentioned in findings

### EXPECTED OUTPUT field

L1 YAML with: `files_changed`, `findings_fixed`, `status`.
L2 with per-file change log: finding ID, what changed, before→after.

### DELIVERY field

Write full result to `tasks/{team}/homeostasis-self-implement.md`.
Send micro-signal to Lead via SendMessage:
`{STATUS}|fixed:{N}|deferred:{N}|ref:tasks/{team}/homeostasis-self-implement.md`

If wave fails: re-spawn with corrected instructions (max 1 retry per wave).

---

## Step 3 — Verification Checklist

Post-implementation verification checklist (re-run diagnostic categories for modified files only):

- **Non-native fields**: Re-scan modified files — zero non-native fields (CRITICAL)
- **Routing integrity**: All auto-loaded skills visible, no `disable-model-invocation: true` on pipeline skills
- **Budget compliance**: Total description chars within 32,000
- **Cross-reference consistency**: INPUT_FROM/OUTPUT_TO bidirectionality intact
- **Hook script validity**: Shebang present, exit codes correct, JSON output format valid

---

## Step 4 — Memory Update DPS

Spawn infra-implementer for memory updates after convergence:

### CONTEXT

Improvement cycle findings, files changed, cc-reference updates from the completed wave(s).

### TASK

- Update `memory/context-engineering.md` with new findings from this cycle
- Update `MEMORY.md` session history with cycle summary (commit hash, finding counts, files changed)

### CONSTRAINTS

- Edit tool only — modify existing sections, do not restructure
- MEMORY.md must stay ≤200 lines (move detailed content to topic files if needed)

### EXPECTED OUTPUT

L1 YAML with: `files_updated`, `status`.
L2 with change summary per file.

### DELIVERY

Write full result to `tasks/{team}/homeostasis-self-implement-records.md`.
Send micro-signal to Lead via SendMessage:
`PASS|files:{N}|ref:tasks/{team}/homeostasis-self-implement-records.md`

---

## Step 5 — Commit Procedure

Lead-direct via Bash tool, or route to delivery-pipeline:

1. Stage changed files: `git add <specific files>` — never `git add -A`
2. Commit message format: `feat(infra): RSI [scope] -- [summary]`
3. Commit body: include finding categories (CRITICAL/HIGH/MEDIUM counts) and deferred items
4. Report ASCII status visualization after commit

Example commit message:
```
feat(infra): RSI fields-routing -- remove 3 non-native fields + fix 2 routing breaks

Categories: CRITICAL:3 HIGH:2 MEDIUM:1 LOW:0
Deferred: 0
Files: 6 changed
```

---

## Finding-to-Task Mapping

Group findings into waves by non-overlapping file sets:

| Wave Criteria | Assignment Rule |
|---|---|
| ≤5 findings, all separate files | Single infra-implementer wave |
| 6+ findings, same category | Group by category (field removal, routing fix, etc.) |
| Findings in overlapping files | Sequential (not parallel) — assign to same implementer |
| CRITICAL + HIGH mixed | Separate wave from MEDIUM/LOW to prevent deferred contamination |

Wave size target: 3-8 findings per implementer. Fewer = underutilized. More = context overload risk.
