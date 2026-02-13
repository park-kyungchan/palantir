# Coordinator Body Content Analysis (Raw)

## Per-Coordinator Detail

### 1. research-coordinator.md (105 total lines, 80 body lines)

**Sections:**
1. `# Research Coordinator` (header + protocol ref)
2. `## Role` — 3 lines
3. `## Workers` — 5 lines (3 bullets + context)
4. `## Before Starting Work` — 5 lines
5. `## Worker Management` → `### Research Distribution` — 7 lines
6. `## Communication Protocol` → `### With Lead` + `### With Workers` — 10 lines
7. `## Understanding Verification (AD-11)` — 5 lines
8. `## Failure Handling` — 5 lines
9. `## Coordinator Recovery` — 6 lines
10. `## Output Format` — 4 lines
11. `## Constraints` — 8 lines

**Protocol references:** `agent-common-protocol.md` (line 28). Does NOT reference `coordinator-shared-protocol.md`.
**CLAUDE.md duplication:** Recovery section duplicates coordinator-shared-protocol.md §7 concepts.
**Unique logic:** Research distribution rules (codebase vs external vs audit), timeout thresholds (20/30 min).

### 2. verification-coordinator.md (107 total lines, 82 body lines)

**Sections:**
1. `# Verification Coordinator` (header + protocol ref)
2. `## Role` — 3 lines
3. `## Workers` — 5 lines
4. `## Before Starting Work` — 5 lines
5. `## Worker Management` → `### Dimension Distribution` + `### Cross-Dimension Synthesis` — 10 lines
6. `## Communication Protocol` → `### With Lead` + `### With Workers` — 9 lines
7. `## Understanding Verification (AD-11)` — 5 lines
8. `## Failure Handling` — 4 lines
9. `## Coordinator Recovery` — 6 lines
10. `## Output Format` — 4 lines
11. `## Constraints` — 8 lines

**Protocol references:** `agent-common-protocol.md` (line 28). Does NOT reference `coordinator-shared-protocol.md`.
**CLAUDE.md duplication:** Recovery section duplicates coordinator-shared-protocol.md §7.
**Unique logic:** Cross-dimension synthesis rules (structural→relational→behavioral cascade), timeout thresholds (15/25 min).

### 3. architecture-coordinator.md (61 total lines, 39 body lines)

**Sections:**
1. `# Architecture Coordinator` (header + 2 protocol refs)
2. `## Role` — 4 lines
3. `## Before Starting Work` — 5 lines
4. `## How to Work` — 8 lines
5. `## Output Format` — 5 lines
6. `## Constraints` — 6 lines

**Protocol references:** `agent-common-protocol.md` AND `coordinator-shared-protocol.md` (both on lines 25-26).
**CLAUDE.md duplication:** Minimal — most content delegated to shared protocols.
**Unique logic:** None significant — purely delegates to protocols.
**MISSING sections:** Workers list, Communication Protocol, Understanding Verification, Failure Handling, Coordinator Recovery.

### 4. planning-coordinator.md (61 total lines, 39 body lines)

**Sections:**
1. `# Planning Coordinator` (header + 2 protocol refs)
2. `## Role` — 4 lines
3. `## Before Starting Work` — 5 lines
4. `## How to Work` — 8 lines
5. `## Output Format` — 5 lines
6. `## Constraints` — 5 lines

**Protocol references:** `agent-common-protocol.md` AND `coordinator-shared-protocol.md`.
**CLAUDE.md duplication:** Minimal.
**Unique logic:** Non-overlapping file assignment constraint, architecture handoff (P3→P4).
**MISSING sections:** Workers list, Communication Protocol, Understanding Verification, Failure Handling, Coordinator Recovery.

### 5. validation-coordinator.md (61 total lines, 39 body lines)

**Sections:**
1. `# Validation Coordinator` (header + 2 protocol refs)
2. `## Role` — 4 lines
3. `## Before Starting Work` — 5 lines
4. `## How to Work` — 8 lines
5. `## Output Format` — 5 lines
6. `## Constraints` — 5 lines

**Protocol references:** `agent-common-protocol.md` AND `coordinator-shared-protocol.md`.
**CLAUDE.md duplication:** Minimal.
**Unique logic:** Challengers don't need understanding verification (critical analysis = comprehension), unified verdict (PASS/CONDITIONAL_PASS/FAIL).
**MISSING sections:** Workers list, Communication Protocol, Understanding Verification, Failure Handling, Coordinator Recovery.

### 6. execution-coordinator.md (151 total lines, 125 body lines)

**Sections:**
1. `# Execution Coordinator` (header + protocol ref)
2. `## Role` — 3 lines
3. `## Workers` — 5 lines
4. `## Before Starting Work` — 6 lines
5. `## Worker Management` → `### Task Distribution` + `### Review Dispatch Protocol (AD-9)` + `### Fix Loop Rules` — 28 lines
6. `## Communication Protocol` → `### With Lead` + `### Consolidated Report Format` + `### With Workers` — 22 lines
7. `## Understanding Verification (AD-11)` — 6 lines
8. `## Failure Handling` → `### Mode 3 Fallback` — 10 lines
9. `## Coordinator Recovery` — 6 lines
10. `## Output Format` — 4 lines
11. `## Constraints` — 13 lines

**Protocol references:** `agent-common-protocol.md` (line 29). Does NOT reference `coordinator-shared-protocol.md`.
**CLAUDE.md duplication:** Recovery section, Mode 3 explanation (exists in coordinator-shared-protocol.md).
**Unique logic:** Two-stage review dispatch protocol (AD-9), fix loop rules (3x max), consolidated report format, cross-boundary escalation rules.

### 7. testing-coordinator.md (118 total lines, 93 body lines)

**Sections:**
1. `# Testing Coordinator` (header + protocol ref)
2. `## Role` — 3 lines
3. `## Workers` — 4 lines
4. `## Before Starting Work` — 5 lines
5. `## Worker Management` → `### Phase 7: Testing` + `### Phase 8: Integration` + `### Sequential Lifecycle` — 20 lines
6. `## Communication Protocol` → `### With Lead` + `### With Workers` — 11 lines
7. `## Understanding Verification (AD-11)` — 7 lines
8. `## Failure Handling` — 5 lines
9. `## Coordinator Recovery` — 6 lines
10. `## Output Format` — 4 lines
11. `## Constraints` — 8 lines

**Protocol references:** `agent-common-protocol.md` (line 28). Does NOT reference `coordinator-shared-protocol.md`.
**CLAUDE.md duplication:** Recovery section, coordinator fallback concept.
**Unique logic:** Sequential Phase 7→8 lifecycle enforcement, conditional Phase 8 (2+ implementers), per-worker verification examples.

### 8. infra-quality-coordinator.md (113 total lines, 88 body lines)

**Sections:**
1. `# INFRA Quality Coordinator` (header + protocol ref)
2. `## Role` — 3 lines
3. `## Workers` — 5 lines
4. `## Before Starting Work` — 5 lines
5. `## Worker Management` → `### Dimension Distribution` + `### Score Aggregation` + `### Cross-Dimension Synthesis` — 18 lines
6. `## Communication Protocol` → `### With Lead` + `### With Workers` — 8 lines
7. `## Understanding Verification (AD-11)` — 5 lines
8. `## Failure Handling` — 4 lines
9. `## Coordinator Recovery` — 6 lines
10. `## Output Format` — 4 lines
11. `## Constraints` — 8 lines

**Protocol references:** `agent-common-protocol.md` (line 29). Does NOT reference `coordinator-shared-protocol.md`.
**CLAUDE.md duplication:** Recovery section.
**Unique logic:** Score aggregation formula (weighted average with 4 weights), cross-dimension synthesis rules.

## Cross-Coordinator Section Inventory

| Section | research | verific. | archit. | planning | valid. | exec. | testing | infra-q |
|---------|:--------:|:--------:|:-------:|:--------:|:------:|:-----:|:-------:|:-------:|
| Role | Y | Y | Y | Y | Y | Y | Y | Y |
| Workers | Y | Y | — | — | — | Y | Y | Y |
| Before Starting | Y | Y | Y | Y | Y | Y | Y | Y |
| Worker Management | Y | Y | — | — | — | Y | Y | Y |
| Communication Protocol | Y | Y | — | — | — | Y | Y | Y |
| Understanding Verification | Y | Y | — | — | — | Y | Y | Y |
| Failure Handling | Y | Y | — | — | — | Y | Y | Y |
| Coordinator Recovery | Y | Y | — | — | — | Y | Y | Y |
| Output Format | Y | Y | Y | Y | Y | Y | Y | Y |
| Constraints | Y | Y | Y | Y | Y | Y | Y | Y |
| How to Work | — | — | Y | Y | Y | — | — | — |
| Refs shared-protocol | — | — | Y | Y | Y | — | — | — |

**Two distinct templates identified:**
- **Template A (verbose, 80-125 body lines):** research, verification, execution, testing, infra-quality (5 coordinators)
  - All sections spelled out explicitly
  - Only references agent-common-protocol.md (NOT coordinator-shared-protocol.md)
  - Has color: and memory: fields in frontmatter
  - Full disallowedTools list (4 items)
- **Template B (lean, 39 body lines):** architecture, planning, validation (3 coordinators)
  - Minimal sections (Role, Before Starting, How to Work, Output, Constraints)
  - References BOTH protocols
  - Missing color: and memory: fields
  - Partial disallowedTools list (2 items)

## Duplication Analysis

### Sections duplicated from coordinator-shared-protocol.md (Template A only)

| Section | Lines per coordinator | Total across 5 | Already in shared protocol? |
|---------|----------------------|----------------|-----------------------------|
| Coordinator Recovery | 6L | 30L | Yes (§7 Progress State) |
| Worker Management patterns | ~8L avg | ~40L | Yes (§2 Worker Management) |
| Communication Protocol patterns | ~10L avg | ~50L | Partially (§2.2, §2.3) |
| Understanding Verification boilerplate | 3L | 15L | Yes (§2.2, §2.3) |
| Failure Handling boilerplate | 3L | 15L | Yes (§6 Error Matrix) |
| Constraints boilerplate | 5L | 25L | Yes (§1 + agent-common) |
| **Total boilerplate** | **~35L** | **~175L** | |

**Unique content per coordinator (Template A):** 45-90L (varies)

### Template B — Minimal duplication
Architecture, planning, validation delegate to shared protocols effectively.
~39L body with almost no duplication.

## Protocol Reference Gap

| Coordinator | agent-common-protocol | coordinator-shared-protocol |
|-------------|:---------------------:|:---------------------------:|
| research | YES | NO |
| verification | YES | NO |
| architecture | YES | YES |
| planning | YES | YES |
| validation | YES | YES |
| execution | YES | NO |
| testing | YES | NO |
| infra-quality | YES | NO |

**GAP:** 5/8 coordinators do NOT reference coordinator-shared-protocol.md.
These are the Template A coordinators — they inline the shared protocol content instead.
