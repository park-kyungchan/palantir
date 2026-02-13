# T-4: NL-MIGRATE + H-1 — Implementation Detail

## Agent .md L1/L2 Reminder (CS-6)

Added identical line to end of each agent's Constraints section:
```
- Write L1/L2/L3 files proactively throughout your work — they are your only recovery mechanism if your session compacts. Do not wait until the end.
```

### Edit Locations
| File | Anchor (last Constraints line before insertion) |
|------|------------------------------------------------|
| implementer.md | "- If you need files outside your boundary..." |
| integrator.md | "- If conflicts can't be resolved..." |
| architect.md | "- You can write new design documents..." |
| tester.md | "- If fixes are needed, message Lead..." |
| researcher.md | "- You can spawn subagents via Task tool..." |
| devils-advocate.md | "- Always reference specific design sections..." |

### Triple Reinforcement
1. agent-common-protocol.md §"Saving Your Work" (lines 57-64) — already exists
2. CLAUDE.md §10 "Save work to L1/L2/L3 files proactively" — already exists
3. Agent .md Constraints section — NEW (this task)

### Verification
```
$ grep -r "Write L1/L2/L3 files proactively" .claude/agents/ → 6 files match
```

## H-1 Mitigation on CLAUDE.md

### Line 160 Change
Before: "- Hooks verify L1/L2 file existence automatically."
After: "- L1/L2/L3 file creation is reinforced through natural language instructions in each agent's Constraints section and in agent-common-protocol.md."

Rationale: The old text was now false — the 3 hooks that verified L1/L2 (on-subagent-stop,
on-teammate-idle, on-task-completed) were deleted in T-2. The new text accurately describes
the NL replacement mechanism.

### Line 172 Change
Before: 'hook scripts in `.claude/hooks/` (automated enforcement)'
After: 'hook scripts in `.claude/hooks/` (session lifecycle support)'

Rationale: The 3 remaining hooks serve session lifecycle functions (spawn context,
pre-compact snapshot, post-compact recovery), not enforcement. The label now
accurately reflects their purpose.
