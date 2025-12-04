---
description: Investigate the codebase and gather context for a new task
---
1. Run the compliance audit to ensure system integrity.
// turbo
2. Run `make audit-compliance`
3. Inject the latest project context into memory.
// turbo
4. Run `python3 scripts/inject_context.py`
5. **[Environment Detection]**:
    - Check for `pnpm-lock.yaml`, `uv.lock`, `poetry.lock`.
    - Determine the correct package manager commands (e.g., `pnpm` vs `npm`, `uv` vs `pip`).
6. **[Architecture Alignment]**:
    - Read `refactoring_plan.json` and `CONTEXT_LOG.md`.
    - Ensure you understand the "Big Picture" goals before diving into details.
7. Analyze the codebase to understand the current state and dependencies.
8. Use `codebase_investigator` to explore relevant files and directories based on the user's request.
9. Identify any potential conflicts or architectural constraints.
