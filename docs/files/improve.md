---
name: improve
description: Execute codebase improvement with analysis, planning, and implementation
argument-hint: [scope: full|security|performance|quality|tests|docs]
allowed-tools:
  - Read
  - Edit
  - Write
  - Grep
  - Glob
  - Bash
  - Task
---

# Codebase Improvement Execution

Scope: $1 (default: full)
Session: ${CLAUDE_SESSION_ID}
Started: !`date -Iseconds`

---

## Pre-Execution Context

### Current State
- Git Branch: !`git branch --show-current 2>/dev/null || echo "not a git repo"`
- Git Status: !`git status --short 2>/dev/null | head -10`
- Last Commit: !`git log -1 --oneline 2>/dev/null || echo "no commits"`

### Project Info
- Working Directory: !`pwd`
- Project Type: !`ls package.json pyproject.toml Cargo.toml go.mod 2>/dev/null | head -1 || echo "unknown"`

---

## Execution Plan

Based on scope "$1", execute the following:

### Scope: full
Execute all improvement categories in order:
1. Security fixes (P0)
2. Critical bug fixes (P0)
3. Test coverage improvements (P1)
4. Performance optimizations (P1)
5. Code quality improvements (P2)
6. Documentation updates (P3)

### Scope: security
Focus on:
- Credential exposure
- Input validation
- Dependency vulnerabilities
- Authentication/authorization issues

### Scope: performance
Focus on:
- Database query optimization
- Memory usage
- Bundle size reduction
- Caching implementation

### Scope: quality
Focus on:
- Code duplication removal
- SOLID principle adherence
- Error handling improvement
- Naming conventions

### Scope: tests
Focus on:
- Missing unit tests
- Integration test gaps
- E2E test coverage
- Test quality improvements

### Scope: docs
Focus on:
- README updates
- API documentation
- Code comments
- Architecture documentation

---

## Execution Protocol

### Step 1: Create Checkpoint
```bash
git stash push -m "pre-improvement-checkpoint-${CLAUDE_SESSION_ID}"
```

### Step 2: Create Improvement Branch
```bash
git checkout -b improvement/${CLAUDE_SESSION_ID}
```

### Step 3: Execute Improvements
For each identified issue:
1. Analyze current state
2. Plan minimal change
3. Implement fix
4. Verify with tests
5. Commit atomically

### Step 4: Validation
```bash
# Run tests
npm test 2>/dev/null || pytest 2>/dev/null || cargo test 2>/dev/null || echo "No test command found"

# Run linter
npm run lint 2>/dev/null || echo "No lint command"

# Type check
npm run typecheck 2>/dev/null || mypy . 2>/dev/null || echo "No type check"
```

### Step 5: Generate Report
Save improvement report to `.claude/reports/improvement-${CLAUDE_SESSION_ID}.md`

---

## Commit Convention

Use conventional commits:
- `fix(scope): description` for bug fixes
- `perf(scope): description` for performance improvements
- `refactor(scope): description` for code quality
- `test(scope): description` for test additions
- `docs(scope): description` for documentation
- `security(scope): description` for security fixes

---

## Post-Execution

### Success Path
1. Review all changes: `git diff main`
2. Create PR if satisfied
3. Update task list status

### Rollback Path
If issues found:
```bash
git checkout main
git stash pop
```

---

## Notes
- Each improvement should be independently verifiable
- Prefer small, focused commits over large changes
- Always maintain backward compatibility unless explicitly breaking
- Document any breaking changes in CHANGELOG
