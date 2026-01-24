# Task #2: /collect Skill Implementation

> **Worker:** terminal-b
> **Task ID:** #2
> **Completed:** 2026-01-24T18:20:00Z
> **Status:** ✅ Completed

---

## L1 Summary

Implemented the `/collect` skill that aggregates worker results and verifies task completion. The skill provides a bridge between worker outputs and the `/synthesis` stage in the E2E pipeline.

---

## Deliverables

- `.claude/skills/collect/SKILL.md` - Full skill documentation (V2.1.19 compliant)

---

## Implementation Details

### Core Functions Implemented

1. **verifyAllComplete()** - TaskList integration to check all task statuses
2. **aggregateOutputs()** - Glob Worker outputs and parse L1 summaries
3. **detectBlockers()** - Identify stuck, unstarted, or ready-but-pending tasks
4. **generateReport()** - Create collection_report.md for /synthesis

### Key Features

- Completion rate calculation with stats breakdown
- Multi-status task categorization (completed/in_progress/pending)
- Blocker detection with actionable recommendations
- Partial collection support via `--force` flag
- Phase-specific collection via `--phase` flag

### Output Format

Generated report at `.agent/outputs/collection_report.md` includes:
- Summary statistics table
- Task status breakdown
- Aggregated worker outputs with L1 summaries
- Blocker list with recommendations
- Next action suggestion

---

## Integration Points

| Upstream | This Skill | Downstream |
|----------|-----------|------------|
| /assign → Workers | /collect | /synthesis |

---

## Testing Notes

- Follows same documentation pattern as /assign skill
- V2.1.19 frontmatter compliant
- Error handling section included
- Comprehensive testing checklist provided

---

## Files Changed

| Action | Path |
|--------|------|
| Created | `.claude/skills/collect/SKILL.md` |
| Created | `.agent/outputs/Worker/task2-collect-skill.md` (this file) |

---

**End of Worker Output**
