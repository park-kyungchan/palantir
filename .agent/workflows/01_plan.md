---
description: Transform User Intent into a Governed Ontology Plan (Adaptive V2)
---

# 01_plan: TDD-Enhanced Ontology Planning

> **Source**: Merged from Claude `feature-planner` + ODA Handoff Protocol

---

## Phase 1: Intent Analysis

### Goal
Understand user request and codebase state.

### Actions
1. Use `tavily` for external context if needed
2. Use `read_file` to understand codebase architecture
3. Identify dependencies and integration points
4. Assess complexity: Small (2-3 phases) / Medium (4-5) / Large (6-7)

---

## Phase 2: TDD Phase Breakdown

### Goal
Create structured phases with Test-First methodology.

### Phase Structure (per phase)

```markdown
### Phase N: [Deliverable Name]
- **Goal**: What working functionality this produces
- **Test Strategy**: 
  - [ ] RED: Write failing tests first
  - [ ] GREEN: Minimal code to pass
  - [ ] REFACTOR: Improve quality
- **Coverage Target**: ≥80% business logic
- **Quality Gate**: Build + Lint + Tests pass
- **Rollback**: How to revert if issues
```

---

## Phase 3: Quality Gates

### Checklist (validate before next phase)

**Build & Tests**:
- [ ] Project builds without errors
- [ ] All existing tests pass
- [ ] New tests added for new functionality
- [ ] Coverage maintained or improved

**Code Quality**:
- [ ] Linting passes
- [ ] Type checking passes (if applicable)

**Functionality**:
- [ ] Manual testing confirms feature works
- [ ] No regressions

---

## Phase 4: Risk Assessment

| Risk Type | Probability | Impact | Mitigation |
|-----------|-------------|--------|------------|
| Technical | Low/Med/High | Low/Med/High | Action |
| Dependency | Low/Med/High | Low/Med/High | Action |
| Timeline | Low/Med/High | Low/Med/High | Action |

---

## Phase 5: Ontology Plan Definition (ODA)

### Goal
Create structured `Plan` object for Ontology.

### Actions
1. Define `Objective` from user intent
2. Break down into `Jobs`
3. Assign `Role`: Architect (Claude) / Automation (GPT)

---

## Phase 6: Handoff Artifact Generation

### Goal
Create files for manual agent routing.

### Command
```bash
python -m scripts.ontology.handoff --plan .agent/plans/plan_[ID].json --job [INDEX]
```

### Verify
Check `.agent/handoffs/pending/` for new file.

---

## Phase 7: User Notification

> "Handoff File Created: `.agent/handoffs/pending/job_[ID]_claude.md`"
> "Please switch to Claude and ask it to read this file."

---

## Progress Tracking

**After completing each phase**:
1. ✅ Check off completed tasks
2. 🧪 Run quality gate validation
3. ⚠️ Verify ALL gates pass
4. 📝 Document learnings
5. ➡️ Then proceed to next phase

⛔ **DO NOT skip quality gates**
