# Coding Style

## Immutability (CRITICAL)
ALWAYS create new objects, NEVER mutate existing ones.
Rationale: prevents hidden side effects, enables safe concurrency.

## Size Constraints
- Functions: <50 lines
- Files: <800 lines (800 = hard cap, 400 = target)

## File Organization
- Many small files > few large files
- 200-400 lines typical
- Organize by feature/domain, not by type
