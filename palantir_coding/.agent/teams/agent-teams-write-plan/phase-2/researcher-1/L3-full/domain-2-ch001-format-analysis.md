# Domain 2: CH-001 Plan Format Detailed Analysis

## Source File
`docs/plans/2026-02-07-ch001-ldap-implementation.md` (757 lines, 10 sections)

## Section-by-Section Deep Dive

### §1 Orchestration Overview (lines 1-67)

**Structure:**
1. Plan header (Goal, Architecture, Design Source, Pipeline)
2. Pipeline Structure diagram (ASCII)
3. Teammate Allocation table (Role, Count, Agent Type, File Ownership, Phase)
4. WHY justification for teammate count
5. Execution Sequence diagram (step-by-step with DIA protocol inset)

**Universal elements:**
- Pipeline structure diagram pattern — customizable phase list
- Teammate allocation table — standard columns
- Execution sequence with DIA protocol inline — always needed
- WHY justification pattern — architect must justify decisions

**CH-001-specific:**
- "Simplified Infrastructure (Phase 1→6→6.V→9)" — parameterize to any phase subset
- "Single implementer... WHY: tight cross-references" — instance of count justification
- DIA protocol box shows "v2.0" — parameterize to current version

**Template pattern:**
```markdown
## 1. Orchestration Overview

### Pipeline Structure
{Variable: which phases used, ASCII diagram}

### Teammate Allocation
| Role | Count | Agent Type | File Ownership | Phase |
{Variable: rows per teammate type}

**WHY {count} {role}:** {justification for allocation decision}

### Execution Sequence
{Standard DIA-integrated sequence with parameterized protocol version}
```

---

### §2 global-context.md Template (lines 68-127)

**Structure:**
- YAML frontmatter (version, project, pipeline, current_phase)
- Project Summary
- Design Reference
- Key Design Decisions
- Scope (files modified/created, version changes)
- Cross-Reference Integrity Requirement [CRITICAL]
- Active Teammates
- Phase Status

**Universal elements:** ALL sections are universal. GC is the Agent Teams coordination mechanism.

**CH-001-specific:** Content within sections (LDAP-specific decisions, category IDs, etc.)

**Template pattern:** GC-v{N-1} → GC-v{N} delta specification. The template shows what to ADD to GC-v3 to produce GC-v4.

---

### §3 File Ownership Assignment (lines 128-144)

**Structure:**
- Table: File | Ownership | Operation (MODIFY/CREATE/DELETE/READ-ONLY)
- Note about inclusion in task-context.md

**Universal elements:** Entire structure. Becomes more critical with multiple implementers.

**CH-001-specific:** Single implementer owns all files — simplest case.

**Template pattern for multi-implementer:**
```markdown
## 3. File Ownership Assignment

### implementer-1: {responsibility domain}
| File | Operation | Notes |
{files owned by implementer-1}

### implementer-2: {responsibility domain}
| File | Operation | Notes |
{files owned by implementer-2}

### Interface Contracts
| Interface | Provider (implementer) | Consumer (implementer) | Contract |
{shared interfaces between implementer scopes}

### Read-Only References
| File | Referenced By |
{files that implementers need to read but not modify}
```

---

### §4 TaskCreate Definitions (lines 145-272)

**Structure per task:**
```yaml
subject: "descriptive title"
description: |
  ## Objective
  ## Context in Global Pipeline
  - Phase / Upstream / Downstream
  ## Detailed Requirements
  - Reference to §5/§6 in plan
  ## File Ownership
  ## Dependency Chain
  - blockedBy / blocks
  ## Acceptance Criteria
  1. (numbered, specific, verifiable)
activeForm: "present progressive description"
```

**Universal elements:** ALL 6 fields. The 6-subsection description structure (Objective, Context, Requirements, Ownership, Dependencies, Acceptance) is universal.

**CH-001-specific:** 3 tasks (A: core files, B: agent files, C: validation). Any feature will have different task decomposition.

**Key patterns:**
- Acceptance criteria are numbered, specific, verifiable (not vague)
- Context section links task to pipeline position (upstream/downstream)
- Detailed Requirements reference separate section (§5/§6) — avoids duplicating long content in TaskCreate
- Dependencies are explicit (blockedBy/blocks)

---

### §5-§6 Edit Specifications (lines 273-486)

**Structure per edit:**
```markdown
### A{N}: {target file} — {description}

**Location:** After line {content} (line {number}), BEFORE {content} (line {number}).

**Insert:** / **Change from:** / **Change to:**
{exact content block with markdown code fence}
```

**Universal pattern:** Location → Action (Insert/Change/Remove) → Exact Content

**For CREATE operations (not in CH-001):**
```markdown
### A{N}: {new file path} — {description}

**Purpose:** {why this file exists}
**Scaffold:**
{exact initial content}

**Import Relationships:**
- Imports from: {list}
- Imported by: {list}
```

---

### §7 Validation Checklist (lines 487-681)

**Structure:**
- V1: Format Consistency (string match across files)
- V2: Matrix Consistency (table value match across files)
- V3: Assignment Consistency (role-specific values match)
- V4: Version Numbers (version string match)
- V5: Definition Consistency (semantic definition match across files)

**Universal pattern:** 5 validation categories. Each category has:
- Description of what to check
- Expected value
- Locations to check (file + section)
- Checkbox format for implementer

**CH-001-specific:** All specific items (message format strings, category IDs, intensity levels, etc.)

---

### §8 Commit Strategy (lines 682-719)

**Structure:**
- Option 1 (Recommended): Single commit with exact command
- Option 2 (Alternative): Per-task commits with exact commands
- Recommendation with justification

**Universal:** Entire pattern. Architect chooses based on task coupling.

---

### §9 Gate Criteria (lines 720-740)

**Structure:**
- Numbered criteria table (7 items)
- Result thresholds (ALL PASS / 1-2 FAIL / 3+ FAIL)
- Actions per threshold

**CH-001's 7 criteria:**
1. All files modified correctly
2. Cross-references pass V1-V5
3. No broken formatting
4. Version numbers updated
5. Unchanged files verified
6. L1/L2/L3 handoff files written
7. Git commit clean

**Universal:** Items 1, 2, 6, 7 are universal. Items 3-5 are feature-type dependent.

---

### §10 Summary (lines 741-757)

**Structure:**
- Metadata table (Pipeline, Teammates, Tasks, Files, Hooks, Lines, DIA, Commits, Gates)

**Universal:** Entire structure. Values are instance-specific.

---

## Generalized Template Design Rationale

The proposed 10-section template reorganizes CH-001's structure:

1. **§5/§6 merged → §5 Change Specifications**: CH-001 split by task (A vs B). Generalized version groups by task but includes CREATE/MODIFY/DELETE operations.
2. **§6 Test Strategy added**: CH-001 had no testing (infrastructure change). New features need Phase 7 integration.
3. **§7 Validation Checklist**: Preserved from CH-001 §7 with category pattern.
4. **§8-§10**: Direct carry-over from CH-001 §8-§10.

The template is designed so the architect fills in parametric values while the structural skeleton remains constant across all features.
