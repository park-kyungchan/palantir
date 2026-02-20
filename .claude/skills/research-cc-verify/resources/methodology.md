# CC-Verify Methodology Reference

Loaded on-demand by research-cc-verify skill. Contains path lookup tables, evidence templates, inspection checklists, and test patterns.

---

## 1. Filesystem Path Lookup Tables

### FILESYSTEM claims — paths to inspect

| What to find | Path pattern | Tool |
|---|---|---|
| Subagent output files | `tasks/{work_dir}/*.md` | Glob + Read |
| Task files | `~/.claude/tasks/{name}/*.json` | Glob |
| Task file lock | `~/.claude/tasks/{name}/.lock` | Glob |
| Skill files | `.claude/skills/{skill}/SKILL.md` | Glob |
| Agent profiles | `.claude/agents/{agent}.md` | Glob |
| Shared resources | `.claude/resources/{name}.md` | Glob |
| Ref cache files | `.claude/projects/-home-palantir/memory/ref_*.md` | Glob |
| Global claude dir | `~/.claude/` | Glob |
| Project memory | `.claude/projects/-home-palantir/memory/` | Glob |

### PERSISTENCE claims — paths to inspect

| What survives | Files to check | Verification method |
|---|---|---|
| Subagent output after completion | `tasks/{work_dir}/*.md` | Read → check file presence and content |
| Task state after compaction | `~/.claude/tasks/{name}/*.json` | Read → check status + metadata fields |
| PT metadata after compaction | Task JSON with `[PERMANENT]` tag | Read → check metadata.phase_signals |
| Hook output after session | Hook output logs (if configured) | Read hook script + check output destination |

### STRUCTURE claims — directory layout to verify

| Claimed layout element | Verification glob | Expected result |
|---|---|---|
| Work dir structure | `tasks/{work_dir}/` | Output files from subagents |
| Skills dir structure | `.claude/skills/*/SKILL.md` | One SKILL.md per skill dir |
| Agent profiles dir | `.claude/agents/*.md` | All 7 profiles present |
| Resources dir | `.claude/resources/*.md` | 6 shared resource files |
| Ref cache layout | `memory/ref_*.md` | Per-section ref files |
| Rules dir | `.claude/rules/common/*.md` | Common rule files |

### CONFIG claims — settings fields to inspect

| Setting | File | Field path | Valid values |
|---|---|---|---|
| MCP servers | `.claude.json` | `mcpServers` | Object with server configs |
| Task list ID | `~/.claude/settings.json` | `env.CLAUDE_CODE_TASK_LIST_ID` | string (team name) |
| Skill budget | `~/.claude/settings.json` | `env.SLASH_COMMAND_TOOL_CHAR_BUDGET` | integer (chars) |
| Attribution | `~/.claude/settings.json` | `includeCoAuthoredBy` | boolean |
| permissionMode | `.claude/agents/{agent}.md` | `permissionMode:` frontmatter field | `default`, `plan` |

### BEHAVIORAL claims — artifacts to inspect

| Claimed behavior | Files to check | What to look for |
|---|---|---|
| Hook fires on event | `~/.claude/settings.json` hooks field | Hook type + matcher + command |
| Agent has tool set | `.claude/agents/{agent}.md` | `tools:` frontmatter field |
| Skill routing active | `.claude/skills/{skill}/SKILL.md` | `description:` frontmatter (L1 routing) |
| Memory auto-tool | `.claude/agents/{agent}.md` | `memory:` field presence |
| Session-id guard | Hook script source | `CLAUDE_SESSION_ID` check in script |

---

## 2. Claim Evidence Template

Use this table for each claim being verified:

| Field | Content |
|---|---|
| **Claim text** | Exact wording of the CC-native claim |
| **Category** | FILESYSTEM / PERSISTENCE / STRUCTURE / CONFIG / BEHAVIORAL / BUG |
| **Expected path** | File or glob pattern to inspect |
| **Verification method** | Read / Glob / Grep + what to look for |
| **Evidence found** | Actual file content or glob results (file:line) |
| **Verdict** | PASS / FAIL / NEEDS-REVIEW |
| **Notes** | Contradicting evidence (FAIL) or why inconclusive (NEEDS-REVIEW) |

---

## 3. Category-Specific Inspection Checklist

### FILESYSTEM
- [ ] File exists at claimed path (Glob → non-empty result)
- [ ] File is readable (Read → no access error)
- [ ] File format matches claim (JSON, YAML, Markdown)
- [ ] File contains expected top-level fields or sections

### PERSISTENCE
- [ ] File exists after the claimed event (termination / compaction)
- [ ] File timestamps predate or postdate the event as expected
- [ ] Message count / entry count is non-zero
- [ ] No content was wiped or reset

### STRUCTURE
- [ ] Directory tree matches claimed layout (Glob tree)
- [ ] All expected subdirectories present
- [ ] All expected files present at each level
- [ ] No extra unexpected directories that would invalidate claim

### CONFIG
- [ ] Field is present in the correct file (not settings.json when it should be .claude.json)
- [ ] Field accepts the claimed value type (string / boolean / integer / object)
- [ ] Current value is one of the documented options
- [ ] Field absence is documented if optional

### BEHAVIORAL
- [ ] Artifacts exist that would produce the claimed behavior (hook scripts, agent profiles)
- [ ] Hook event type matches what's claimed to fire
- [ ] Agent `tools:` field matches claimed tool set
- [ ] No conflicting configuration that would suppress the claimed behavior

### BUG
- [ ] Symptoms described in claim are reproducible from file state
- [ ] Workaround configuration (if any) is present and correct
- [ ] Bug ID matches known-bugs list in ref cache

---

## 4. Verification Test Patterns

### FILESYSTEM test
```
Claim: "Subagent output files written to tasks/{work_dir}/*.md"
Test:  Glob("tasks/{work_dir}/*.md")
Check: Files matching pattern exist after subagent completes
PASS:  ≥1 file found at pattern
FAIL:  No files found → claim may be wrong path or subagent failed to write
NEEDS-REVIEW: No completed subagents to generate output files
```

### PERSISTENCE test
```
Claim: "PT metadata persists after compaction"
Test:  Read task JSON with [PERMANENT] tag → check metadata.phase_signals
Check: metadata fields present and non-empty after compaction event
PASS:  metadata.phase_signals populated with phase results
FAIL:  metadata missing or empty → persistence claim false
NEEDS-REVIEW: Cannot determine if compaction occurred; no PT present
```

### STRUCTURE test
```
Claim: "Tasks use file locking via .lock file"
Test:  Glob("~/.claude/tasks/*/.lock")
Check: .lock file exists in active task directories
PASS:  .lock found in ≥1 task directory
NEEDS-REVIEW: No active tasks at time of verification (transient state)
FAIL:  .lock never found even with active tasks → locking mechanism differs
```

### CONFIG test
```
Claim: "MCP servers must be configured in .claude.json, not settings.json"
Test:  Read .claude.json → check mcpServers field
       Read ~/.claude/settings.json → check if mcpServers field present
Check: .claude.json has mcpServers; settings.json does NOT have mcpServers
PASS:  .claude.json has field; settings.json does not
FAIL:  settings.json has mcpServers → claim may be wrong (or both files checked)
NEEDS-REVIEW: Neither file has mcpServers (no MCP configured yet)
```

### BEHAVIORAL test
```
Claim: "PostToolUse hook fires for all file writes by all subagents"
Test:  Read ~/.claude/settings.json → hooks section
       Check hook event type: "PostToolUse"
       Check matcher: includes Write/Edit tools
       Check command: script path exists
Check: Hook is registered with correct event + matcher + executable script
PASS:  All three checks pass
FAIL:  Hook missing, wrong event type, or script not executable
NEEDS-REVIEW: Hook present but cannot verify "all subagents" without live execution
```

### BUG test
```
Claim: "BUG-005: MEMORY.md double-injection causes 2× token cost"
Test:  Read ~/.claude/settings.json → check if MEMORY.md in additionalContext
       Read MEMORY.md → count lines (>200 line limit means double-cost is amplified)
       Check: Is bug ID in memory/pipeline-bugs.md?
Check: Bug exists as documented, workaround (200-line limit) is enforced
PASS:  MEMORY.md ≤200 lines; bug ID in bugs file
NEEDS-REVIEW: Cannot verify token cost empirically without runtime measurement
```
