# Issue Resolution Workflow

This document defines the standardized workflow for resolving technical issues using Gemini 3.0 Pro's active toolchain.

## 1. Detection
- **Trigger:** Shell command failure (exit code != 0), unexpected exception, or implementation blocker.
- **Immediate Action:** STOP execution. Do not guess.

## 2. Investigation (Mandatory)
Before proposing a fix, you MUST use the following tools to gather context:

### A. Context7 (Documentation & Libraries)
- **Tool:** `resolve-library-id` -> `get-library-docs`
- **Purpose:** Verify correct usage, check for breaking changes (e.g., Tailwind v4 vs v3), find official workarounds.
- **Query:** "error message" or "library name + issue description".

### B. GitHub (Code & Issues)
- **Tool:** `search_issues` or `search_code`
- **Purpose:** Find if others have faced this specific error.
- **Query:** "repo:owner/name error message" or generic error search.

## 3. Resolution
- **Formulate Hypothesis:** Based on search results (not hallucinations).
- **Deep Think:** Use `sequentialthinking` to validate the fix against the project context.
- **Implement:** Apply the fix using `run_shell_command` or `write_file`.

## 4. Verification
- **Verify:** Run the failed command again or add a test case.
- **Document:** If the issue was non-trivial, add a "Lesson Learned" to `GEMINI.md`.
