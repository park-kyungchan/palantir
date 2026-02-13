# T-3: Hook NLP Conversion + H-2 — Implementation Detail

## on-session-compact.sh Changes (CS-4)

| Location | Before | After |
|----------|--------|-------|
| Line 3 comment | "DIA Enforcement: Lead must..." | "Recovery: Lead must..." |
| Line 10 log | "DIA re-injection required" | "re-injection required" |
| Line 17 jq additionalContext | "[DIA-RECOVERY] Context was compacted..." with [DIRECTIVE]+[INJECTION], [STATUS] | "Your session was compacted..." with NL instructions |
| Line 22 fallback | Same protocol markers | Same NL replacement |

Both jq path and fallback path produce identical additionalContext text.

## on-subagent-start.sh Changes (CS-5)

Used `replace_all: true` to replace all 3 occurrences of `"[DIA-HOOK] Active team: "`
with `"Active team: "` in a single Edit operation.

Affected paths:
1. Line 35 — GC legacy path
2. Line 46 — PT path
3. Line 60 — no-team fallback

Note: `[PERMANENT]` on line 46 is NOT a protocol marker — it's the literal text used
to find the PERMANENT Task via TaskGet subject search. Correctly preserved.

## on-pre-compact.sh H-2 Mitigation

Added after the existing task snapshot logic (after line 40):
- Uses CLAUDE_CODE_TASK_LIST_ID env var (already used in the file) to find team dir
- Falls back to most recent team dir if env var not set
- Scans all `phase-*/*/` directories for missing L1-index.yaml or L2-summary.md
- Logs WARNING with agent names to compact-events.log
- Always exits 0 — purely informational

Also updated line 3 comment: "for DIA recovery" → "for recovery"

## Protocol Marker Verification
```
$ grep -r "\[DIA-" .claude/hooks/     → No matches found
$ grep -rE "\[DIRECTIVE\]|\[INJECTION\]|\[STATUS\]" .claude/hooks/ → No matches found
```
