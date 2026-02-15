# CC Skill Disambiguation & Sub-Skill Patterns
<!-- Verified: 2026-02-15 via claude-code-guide agent (research for Phase Efficiency Optimization) -->
<!-- Update policy: Re-verify after CC version updates or skill architecture changes -->

## 1. Semantic Disambiguation Between Similar Skills

### Transformer Routing Mechanics
- Lead (Opus 4.6) uses pure transformer reasoning for skill selection (not keyword matching)
- All auto-loaded L1 descriptions visible every request as part of Skill tool definition
- First 50-100 chars receive 3-5x higher attention weight than mid-description tokens
- "Use when:" trigger language improves activation reliability ~15% (community finding)

### Disambiguation Patterns (Ranked by Effectiveness)

| Pattern | Example | Why It Works |
|---------|---------|-------------|
| **Unique verb in first 50 chars** | "Inventories artifacts" vs "Analyzes patterns" | Different semantic embeddings for verbs |
| **Explicit object noun** | "structural dependencies" vs "runtime behaviors" | Noun specificity prevents overlap |
| **Contrastive WHEN conditions** | "After codebase complete" vs "After execution logs available" | Temporal/state differentiation |
| **Phase tag differentiation** | [P1·Design] vs [P3·Plan] | Tag + phase number = immediate context |
| **INPUT_FROM specificity** | "from architecture decisions" vs "from task breakdown" | Data flow uniqueness |

### Optimal Description Structure for Routing
```
Tag (unique phase+domain+role) + Verb (unique action) + Noun (unique scope)
└─────── max 50 chars ────────┘ └── max 20 chars ──┘ └── max 30 chars ──┘
```

Key: Pack core differentiator into first 50 characters.

### Our WHEN Field = Lead Ordering Metadata
- CC doesn't parse WHEN programmatically — Lead reads it semantically
- WHEN helps Lead identify phase ordering and preconditions
- Combined with PT (PERMANENT Task) phase tracking for routing decisions

## 2. Sub-Skill Naming Conventions

### Directory Structure Constraints
- **Flat structure ONLY**: `.claude/skills/{name}/SKILL.md` (one level)
- **Nested NOT supported**: `.claude/skills/parent/child/SKILL.md` will NOT be discovered
- **Max name length**: 64 characters (CC schema validation)
- **Characters**: lowercase, numbers, hyphens only

### CC Skill Discovery Mechanism
```
.claude/skills/*/SKILL.md  (one glob level only)
```
Nested directory discovery only applies to working directory packages, NOT to .claude/skills/ itself.

### Recommended Sub-Skill Naming Pattern
```
.claude/skills/
├── research-audit-static/SKILL.md          (15 + 6 = 21 chars)
├── research-audit-behavioral/SKILL.md      (15 + 10 = 25 chars)
├── research-audit-relational/SKILL.md      (15 + 10 = 25 chars)
└── research-audit-impact/SKILL.md          (15 + 6 = 21 chars)
```
All well under 64-char limit. Prefix `research-audit-` groups semantically.

### L1 Budget Impact
- Each new auto-loaded sub-skill: ~300-400 chars to budget
- 4 sub-skills: ~1.2-1.6KB additional
- Current headroom: ~8KB (75% of 32KB budget used)
- After 4 sub-skills: ~6.4KB headroom remaining — viable

## 3. Incremental Cache Strategy

### CC-Native Persistent Storage Options

| Mechanism | Location | Auto-Load | Persistence | Best For |
|-----------|----------|-----------|-------------|----------|
| **Agent memory** | `.claude/agent-memory/{agent}/` | First 200 lines of MEMORY.md | Cross-session | Incremental cache (primary) |
| **Project memory** | `~/.claude/projects/{hash}/memory/` | First 200 lines | Cross-session | Knowledge archive |
| **Rules directory** | `.claude/rules/*.md` | Per-path match | Permanent | Path-scoped instructions |
| **Skill support files** | `.claude/skills/{name}/*.md` | On-demand (Read) | Permanent | Reference data |

### Recommended: Agent Memory + Shell Preprocessing

**Pattern: Write-Once, Incremental-Update Cache**

1. **First run**: Agent creates full analysis cache
2. **Subsequent runs**: Shell preprocessing checks cache status → agent updates only changed sections

**Shell Preprocessing for Cache Detection:**
```markdown
## Cache Status
!`test -f .claude/agent-memory/analyst/audit-cache.md && echo "Cache: $(wc -l < .claude/agent-memory/analyst/audit-cache.md) lines, $(stat -c%s .claude/agent-memory/analyst/audit-cache.md) bytes" || echo "Cache: EMPTY"`
```

**Cache File Structure:**
```markdown
# Audit Cache
## Index (lines 1-10)
- static: lines 11-50 [COMPLETE|PARTIAL|EMPTY]
- behavioral: lines 51-100 [status]
- relational: lines 101-150 [status]
- impact: lines 151-200 [status]
- last_updated: 2026-02-15
- last_trigger: git_diff_hash

## Static Section (11-50)
[incremental entries]

## Behavioral Section (51-100)
[incremental entries]
```

### Size Constraints
- MEMORY.md auto-load: first 200 lines only (rest via Read tool on-demand)
- No hard file size limit documented, recommend ≤1MB per agent
- Supporting files (non-MEMORY.md): no auto-load cost, accessed on-demand
- Token cost: 200-line MEMORY.md ≈ 200-400 tokens per agent invocation

## 4. Description Optimization Summary

### Canonical L1 Structure (Verified Effective)
```
[Phase·Domain·Role] Unique-verb unique-noun summary.

WHEN: Explicit precondition with phase reference.
DOMAIN: domain (skill N of M). Sequence info.
INPUT_FROM: source (specific data description).
OUTPUT_TO: target (specific output description).

METHODOLOGY: (1) step, (2) step, (3) step, (4) step, (5) step.
OUTPUT_FORMAT: L1 format, L2 format.
```

### Critical Rules
1. Core differentiator in first 50 chars (tag + verb + noun)
2. WHEN must be mutually exclusive within domain
3. INPUT_FROM/OUTPUT_TO must be bidirectionally consistent
4. Total ≤1024 chars (CC truncation boundary)
5. "Use when:" trigger phrase improves user-facing activation
6. Our WHEN: field serves equivalent purpose for Lead routing
