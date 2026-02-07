# File Change Mapping — DIA v3.1 → v4.0

**Author:** architect-1 | **Date:** 2026-02-07

---

## 1. CLAUDE.md (v3.1 → v4.0)

### §3 Role Protocol

**§3 Lead subsection — MODIFY:**
| Location | Action | Content |
|----------|--------|---------|
| After "Sole writer of Task API" | ADD bullet | "Creates TEAM-MEMORY.md at TeamCreate, curates at Gate time (see §6)" |
| After CIP bullet | ADD bullet | "Context Delta: sends structured delta for GC updates; full fallback for 5 conditions (see §4)" |

**§3 Teammates subsection — MODIFY:**
| Location | Action | Content |
|----------|--------|---------|
| After "Reference injected task-context.md" | ADD bullet | "Read TEAM-MEMORY.md before starting work. Agents with Edit: write to own section. Others: report via SendMessage to Lead." |
| After "Write L1/L2/L3 files at ~75%" | ADD bullet | "Process [CONTEXT-UPDATE] delta format; respond with enhanced [ACK-UPDATE] (delta items count + action taken)" |

### §4 Communication Protocol

**§4 Table — MODIFY:**
| Location | Action | Content |
|----------|--------|---------|
| After "Update ACK" row | ADD row | "Team Memory Update | Teammate → File | During work (Edit own section with discoveries)" |
| "Context Update" row | CHANGE | Direction: "Lead → Teammate" remains; When: ADD "(delta or full)" |

**§4 Formats — MODIFY:**
| Location | Action | Content |
|----------|--------|---------|
| [CONTEXT-UPDATE] format | REPLACE | `[CONTEXT-UPDATE] GC-v{old} → GC-v{new} | Delta: ADDED/CHANGED/REMOVED items | Impact: {affected list}` |
| [ACK-UPDATE] format | REPLACE | `[ACK-UPDATE] GC-v{new} received. Items: {applied}/{total}. Impact: {NONE\|desc}. Action: {CONTINUE\|PAUSE\|NEED_CLARIFICATION}` |

### §6 Orchestrator Decision Framework

**§6 DIA Engine subsection — MODIFY:**
| Location | Action | Content |
|----------|--------|---------|
| After "Context Injection" bullet | ADD sub-bullet | "Delta injection when version_gap==1 and no fallback condition. Full injection for 5 fallback conditions (FC-1~FC-5)." |
| After "Propagation" bullet | ADD sub-bullet | "Delta calculation: note ADDED/CHANGED/REMOVED sections when editing GC file" |

**§6 — NEW subsection "### Team Memory" after "### L1/L2/L3 Handoff":**
```markdown
### Team Memory
- Location: `.agent/teams/{session-id}/TEAM-MEMORY.md`
- Created by Lead at TeamCreate (Write tool, once)
- Structure: Section-per-role (## Lead, ## {role-id})
- Access: Edit only (own section). Write forbidden after creation.
- Tags: [Finding], [Pattern], [Decision], [Warning], [Dependency], [Conflict], [Question]
- Direct Edit: implementer, integrator (have Edit tool)
- Lead relay: researcher, architect, tester, devils-advocate (no Edit tool)
- Curation: Lead at Gate time (ARCHIVED stale items), 500-line trim
```

**§6 Output Directory tree — MODIFY:**
| Location | Action | Content |
|----------|--------|---------|
| Under session-id root | ADD line | `├── TEAM-MEMORY.md` |

### §9 Compact Recovery — No changes needed
(Context Delta's fallback conditions FC-2 are already covered by existing compact recovery protocol)

### [PERMANENT] Semantic Integrity Guard

**Lead — Enforcement Duties — MODIFY:**
| Location | Action | Content |
|----------|--------|---------|
| CIP (#2) | ADD sub-bullet | "Delta mode: When version_gap==1, send structured delta (ADDED/CHANGED/REMOVED). Full mode: For FC-1~FC-5 (gap>1, compact, initial, >50%, explicit request)." |
| After LDAP (#7) | ADD new duty #8 | "**Team Memory:** Create TEAM-MEMORY.md at TeamCreate. Write teammate sections on behalf of non-Edit agents. Curate at Gate time." |

**Teammates — Compliance Duties — MODIFY:**
| Location | Action | Content |
|----------|--------|---------|
| Context Updates (#4) | CHANGE ACK format | "On [CONTEXT-UPDATE] → [ACK-UPDATE] with delta items applied count, impact, and action (CONTINUE/PAUSE/NEED_CLARIFICATION)." |
| After #4 | ADD new duty #4a | "**Team Memory:** Read TEAM-MEMORY.md before work. Agents with Edit: write discoveries to own section. Others: report via SendMessage to Lead for relay." |

---

## 2. task-api-guideline.md (v3.0 → v4.0)

### §11 DIA Enforcement Protocol — CIP subsection — MODIFY

**Injection Points table — MODIFY:**
| Location | Action | Content |
|----------|--------|---------|
| IP-003 row | ADD column note | "Delta if version_gap==1, else Full" |
| IP-004 row | ADD column note | "Always Full (architecture change = major restructure)" |
| After IP-009 | ADD IP-010 | "IP-010 | Team Memory Relay | Teammate findings (non-Edit agents) | Edit tool on TEAM-MEMORY.md" |

**After LDAP section — ADD new block:**
```markdown
### Context Delta Protocol
- Delta format: ADDED/CHANGED/REMOVED + §section reference
- Full fallback: FC-1 (gap>1), FC-2 (compact), FC-3 (initial), FC-4 (>50%), FC-5 (explicit)
- Enhanced ACK: items applied count + impact + action
- Lead generates delta from awareness of GC changes (not mechanical diff)
```

### NEW §13: Team Memory Protocol — ADD

```markdown
## 13. Team Memory Protocol

### TEAM-MEMORY.md
- Location: `.agent/teams/{session-id}/TEAM-MEMORY.md`
- Purpose: Real-time knowledge sharing within team session
- Created by Lead at TeamCreate time (Write tool, once)
- Deleted with team directory at TeamDelete

### Access Rules
| Agent Type | Has Edit? | Access Method |
|-----------|-----------|---------------|
| implementer | Yes | Direct Edit (own section) |
| integrator | Yes | Direct Edit (own section) |
| Others | No | Lead relay (SendMessage → Lead Edit) |
| Lead | N/A | Full (Write initial, Edit curation) |

### Rules
1. Edit only — Write forbidden after initial creation
2. old_string MUST include section header (## {role-id}) for uniqueness
3. Edit own section only — cross-section edit is protocol violation
4. Tags: [Finding], [Pattern], [Decision], [Warning], [Dependency], [Conflict], [Question]

### vs L1/L2/L3
| Aspect | Team Memory | L1/L2/L3 |
|--------|-------------|----------|
| Purpose | Real-time sharing | Task output handoff |
| Lifetime | Session-scoped | May persist |
| Owner | Section-per-role | Teammate-specific dir |
```

### NEW §14: Context Delta Protocol — ADD

```markdown
## 14. Context Delta Protocol

### Delta Format
[CONTEXT-UPDATE] GC-v{old} → GC-v{new}
- ADDED §{section}: {key}: {value}
- CHANGED §{section}: {key}: {old} → {new}
- REMOVED §{section}: {key}
- REPLACED §{section}: (full content)

### Fallback Decision Tree
FC-1: version_gap > 1 → FULL
FC-2: CONTEXT_LOST → FULL
FC-3: Initial spawn → FULL
FC-4: Delta > 50% of GC → FULL
FC-5: Explicit request → FULL
Else → DELTA

### Enhanced ACK
[ACK-UPDATE] GC-v{new}. Items: {N}/{M}. Impact: {desc}. Action: {CONTINUE|PAUSE|NEED_CLARIFICATION}
```

---

## 3. Agent .md Files (6 files)

### Common Changes (ALL 6 agents)

**Mid-Execution Updates section — MODIFY:**
| Location | Action | Content |
|----------|--------|---------|
| ACK-UPDATE line | CHANGE | "Send: `[ACK-UPDATE] GC-v{ver} received. Items: {N}/{M}. Impact: {assessment}. Action: {CONTINUE\|PAUSE\|NEED_CLARIFICATION}`" |

### implementer.md — Additional Changes

**Phase 3: Execution section — MODIFY:**
| Location | Action | Content |
|----------|--------|---------|
| Before "Only modify files..." | ADD step | "Read TEAM-MEMORY.md before starting implementation work" |
| After "Run self-tests" | ADD step | "Write discoveries to own TEAM-MEMORY.md section using Edit tool (include section header in old_string)" |

**Constraints section — MODIFY:**
| Location | Action | Content |
|----------|--------|---------|
| After "Self-test is MANDATORY" | ADD bullet | "TEAM-MEMORY.md: Edit own section only. Write tool forbidden. Include `## {your-role-id}` in old_string." |

### integrator.md — Additional Changes

(Same pattern as implementer.md — Read TEAM-MEMORY + Write own section via Edit)

### architect.md — Additional Changes

**Phase 2: Execution section — MODIFY:**
| Location | Action | Content |
|----------|--------|---------|
| Before "Produce Architecture Decision Records" | ADD step | "Read TEAM-MEMORY.md for context from prior phases" |
| After "Write L1/L2/L3" | ADD step | "Report key design decisions to Lead via SendMessage for TEAM-MEMORY.md relay" |

### researcher.md — Additional Changes

(Same pattern as architect — Read TEAM-MEMORY + report via SendMessage for relay)

### tester.md — Additional Changes

(Same pattern as architect — Read TEAM-MEMORY + report via SendMessage for relay)

### devils-advocate.md — Additional Changes

**Phase 1: Execution section — MODIFY:**
| Location | Action | Content |
|----------|--------|---------|
| Before "Challenge EVERY assumption" | ADD step | "Read TEAM-MEMORY.md for context from design phases" |

(No write/relay needed — devils-advocate critiques but doesn't produce findings for sharing)

---

## 4. settings.json — MODIFY

**hooks section — ADD 2 entries:**
```json
"TeammateIdle": [{
  "matcher": "",
  "hooks": [{
    "type": "command",
    "command": "/home/palantir/.claude/hooks/on-teammate-idle.sh",
    "timeout": 10,
    "statusMessage": "Verifying teammate output before idle"
  }]
}],
"TaskCompleted": [{
  "matcher": "",
  "hooks": [{
    "type": "command",
    "command": "/home/palantir/.claude/hooks/on-task-completed.sh",
    "timeout": 10,
    "statusMessage": "Verifying task completion criteria"
  }]
}]
```

---

## 5. Hook Scripts — .claude/hooks/

| Script | Action | Lines (est.) |
|--------|--------|-------------|
| on-subagent-start.sh | MODIFY (enhance) | ~35 (+18 from current 17) |
| on-teammate-idle.sh | CREATE (new) | ~30 |
| on-task-completed.sh | CREATE (new) | ~35 |
| on-subagent-stop.sh | NO CHANGE | — |
| on-task-update.sh | NO CHANGE | — |
| on-pre-compact.sh | NO CHANGE | — |
| on-session-compact.sh | NO CHANGE | — |

---

## Summary — Change Count

| File | Action | Sections Affected |
|------|--------|-------------------|
| CLAUDE.md | MODIFY | §3, §4, §6, [PERMANENT] |
| task-api-guideline.md | MODIFY + ADD | §11, NEW §13, NEW §14 |
| implementer.md | MODIFY | Execution, Constraints, Mid-Execution |
| integrator.md | MODIFY | Execution, Constraints, Mid-Execution |
| architect.md | MODIFY | Execution, Mid-Execution |
| researcher.md | MODIFY | Execution, Mid-Execution |
| tester.md | MODIFY | Execution, Mid-Execution |
| devils-advocate.md | MODIFY | Execution |
| settings.json | MODIFY | hooks section |
| on-subagent-start.sh | MODIFY | GC version injection logic |
| on-teammate-idle.sh | CREATE | Full script |
| on-task-completed.sh | CREATE | Full script |
| **Total** | **12 files** | — |
