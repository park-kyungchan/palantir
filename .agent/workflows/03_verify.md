---
description: Verify the implementation through testing and security scanning
---
1. Inject the latest context to ensure tests run against the new code.
// turbo
2. Run `python3 scripts/inject_context.py`
3. Run the backend test suite.
// turbo
4. Run `cd math/backend && .venv/bin/uv run pytest`
5. Run the frontend test suite.
// turbo
6. Run `cd math/frontend && pnpm test`
7. Perform a security scan on dependencies.
// turbo
8. Run `cd math/frontend && pnpm audit` and `pip-audit` (in backend if available, otherwise skip).
9. If any tests fail, analyze the logs and propose fixes.
