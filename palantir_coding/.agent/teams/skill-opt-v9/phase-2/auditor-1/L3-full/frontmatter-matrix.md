# Coordinator Frontmatter Field Matrix (Raw Extraction)

## Field-by-Field Comparison (8 Coordinators)

### name
| Coordinator | Value |
|-------------|-------|
| research-coordinator | `research-coordinator` |
| verification-coordinator | `verification-coordinator` |
| architecture-coordinator | `architecture-coordinator` |
| planning-coordinator | `planning-coordinator` |
| validation-coordinator | `validation-coordinator` |
| execution-coordinator | `execution-coordinator` |
| testing-coordinator | `testing-coordinator` |
| infra-quality-coordinator | `infra-quality-coordinator` |

**Finding:** All consistent. No optimization target.

### description
| Coordinator | Lines | Content Pattern |
|-------------|-------|-----------------|
| research | 3L | Role + workers + phase + max instances |
| verification | 3L | Role + workers + phase + max instances |
| architecture | 3L | Role + workers + phase + max instances |
| planning | 3L | Role + workers + phase + max instances |
| validation | 3L | Role + workers + phase + max instances |
| execution | 3L | Role + workers + phase + max instances |
| testing | 3L | Role + workers + lifecycle constraint + max instances |
| infra-quality | 3L | Role + dimension count + phase + max instances |

**Finding:** Consistent format. All include `Max 1 instance`. All describe workers managed.

### model
| Coordinator | Value |
|-------------|-------|
| All 8 | `opus` |

**Finding:** All `opus`. Correct per CLAUDE.md spec.

### permissionMode
| Coordinator | Value |
|-------------|-------|
| All 8 | `default` |

**Finding:** All `default`. Correct per BUG-001 workaround.

### memory
| Coordinator | Value | Has `memory:` field? |
|-------------|-------|---------------------|
| research | `user` | YES |
| verification | `user` | YES |
| architecture | — | NO |
| planning | — | NO |
| validation | — | NO |
| execution | `user` | YES |
| testing | `user` | YES |
| infra-quality | `user` | YES |

**Finding:** 5/8 have `memory: user`. 3 MISSING: architecture, planning, validation.
GAP: All coordinators should have `memory: project` for cross-session learning per design.
NOTE: The 5 that have it use `user` scope, not `project`. This is a scope question.

### color
| Coordinator | Value | Has `color:` field? |
|-------------|-------|---------------------|
| research | `cyan` | YES |
| verification | `yellow` | YES |
| architecture | — | NO |
| planning | — | NO |
| validation | — | NO |
| execution | `green` | YES |
| testing | `magenta` | YES |
| infra-quality | `white` | YES |

**Finding:** 5/8 have `color:`. 3 MISSING: architecture, planning, validation.
These are the same 3 missing `memory:`.

### maxTurns
| Coordinator | Value |
|-------------|-------|
| research | 50 |
| verification | 40 |
| architecture | 40 |
| planning | 40 |
| validation | 40 |
| execution | 80 |
| testing | 50 |
| infra-quality | 40 |

**Finding:** 3 tiers: 40 (5), 50 (2), 80 (1 — execution).
Execution has 2x most others — justified by complex two-stage review + fix loop lifecycle.
Research/testing at 50 — moderate workload.

### tools
| Coordinator | Tools List | Count |
|-------------|-----------|-------|
| All 8 | Read, Glob, Grep, Write, TaskList, TaskGet, mcp__sequential-thinking__sequentialthinking | 7 |

**Finding:** Identical across all 8. No variation.

### disallowedTools
| Coordinator | Disallowed List |
|-------------|----------------|
| research | TaskCreate, TaskUpdate, Edit, Bash |
| verification | TaskCreate, TaskUpdate, Edit, Bash |
| architecture | TaskCreate, TaskUpdate |
| planning | TaskCreate, TaskUpdate |
| validation | TaskCreate, TaskUpdate |
| execution | TaskCreate, TaskUpdate, Edit, Bash |
| testing | TaskCreate, TaskUpdate, Edit, Bash |
| infra-quality | TaskCreate, TaskUpdate, Edit, Bash |

**Finding:** All block TaskCreate + TaskUpdate. 5/8 also block Edit + Bash.
3 MISSING Edit/Bash blockers: architecture, planning, validation.
These are the same 3 that lack memory and color. Pattern: these 3 appear to be
from a different generation/template.

### skills (preloaded)
| Coordinator | Value | Has `skills:` field? |
|-------------|-------|---------------------|
| All 8 | — | NO |

**Finding:** 0/8 have `skills:` preloaded. MAJOR GAP.
Potential skills preload candidates per coordinator:
- research-coordinator → `/brainstorming-pipeline` (P1-3 overlap)
- execution-coordinator → `/agent-teams-execution-plan` (P6)
- testing-coordinator → `/verification-pipeline` (P7-8)
- planning-coordinator → `/agent-teams-write-plan` (P4)
- validation-coordinator → `/plan-validation-pipeline` (P5)

### mcpServers
| Coordinator | Value | Has `mcpServers:` field? |
|-------------|-------|--------------------------|
| All 8 | — | NO |

**Finding:** 0/8 have `mcpServers:`. sequential-thinking is already in tools list.
No obvious MCP server needs for coordinators (they don't do web research or external fetch).

### hooks (agent-scoped)
| Coordinator | Value | Has `hooks:` field? |
|-------------|-------|---------------------|
| All 8 | — | NO |

**Finding:** 0/8 have agent-scoped hooks.
Potential hook candidates: L1 auto-write on tool completion, progress-state.yaml auto-update.

## Summary Statistics

| Field | Present | Missing | Consistency |
|-------|---------|---------|-------------|
| name | 8/8 | 0 | 100% |
| description | 8/8 | 0 | 100% |
| model | 8/8 | 0 | 100% (opus) |
| permissionMode | 8/8 | 0 | 100% (default) |
| memory | 5/8 | 3 | 62.5% |
| color | 5/8 | 3 | 62.5% |
| maxTurns | 8/8 | 0 | 100% (varied) |
| tools | 8/8 | 0 | 100% (identical) |
| disallowedTools | 8/8 | 0 | 62.5% (5 full, 3 partial) |
| skills | 0/8 | 8 | 0% (none have) |
| mcpServers | 0/8 | 8 | 0% (none have) |
| hooks | 0/8 | 8 | 0% (none have) |

**Total gaps:** 3 missing memory + 3 missing color + 3 incomplete disallowedTools + 8 missing skills + 8 missing hooks = 25 field-level gaps
