# Phase 2: 개념별 통합 KB 구조 설계

> **Version:** 1.0 | **Status:** IN_PROGRESS | **Date:** 2026-01-18
> **Auto-Compact Safe:** This file persists across context compaction
> **Parent Plan:** `.agent/plans/palantir_dev_delta_coding_kb_enhancement.md`

## Overview
| Item | Value |
|------|-------|
| Complexity | medium |
| Languages | 7 (Java, Python, TypeScript, Go, SQL, C++, Spark) |
| Deliverables | KB_TEMPLATE.md, STRUCTURE.md |
| Files Affected | 2 new + 2 existing modifications |

---

## Dual-Path Analysis Summary

### Explore Agent (aff9307) Findings
- **28 existing KB files** identified (00a-00e foundation, 01-18 domain, 19-22 backend)
- **Current 7-9 Component Structure** found in existing KBs
- **Naming Pattern**: `NN[letter]_descriptive_name.md` (e.g., `00a_programming_fundamentals`)
- **Cross-Stack Comparison**: Already exists in tables (JS/TS, Python, Go, Java)
- **Tier System**: Tier 1 (25-35min), Tier 2 (45min), Tier 3 (45-60min)

### Plan Agent (a3c0399) Findings
- **Naming Convention**: `F{NN}_{concept}.md` prefix for new concept KBs
- **Domain Groups**: F01-F09 (Binding), F10-F19 (Scope), F20-F29 (Types), F30-F39 (Memory/Concurrency), F40-F49 (Functions), F50-F59 (Data Structures)
- **Backward Compatibility**: Never delete/rename existing KBs; F-series supplements
- **7-Component Cross-Language Format**: Complete template designed

---

## Synthesized Design Decision

| Aspect | Explore Finding | Plan Proposal | **Final Decision** |
|--------|-----------------|---------------|--------------------|
| Naming | `NN[letter]_name.md` | `F{NN}_{concept}.md` | **`F{NN}_{concept}.md`** (clear distinction) |
| Existing KBs | Keep as-is | Add cross-references | **Add pointers only** |
| Components | 7-9 variable | Strict 7 | **Standardize to 7** |
| Languages | 3-4 per KB | All 7 | **7 with P0/P1/P2 priority** |

---

## Implementation Tasks

| # | Task | Status |
|---|------|--------|
| 1 | Create KB_TEMPLATE.md with 7-Component Cross-Language format | pending |
| 2 | Create STRUCTURE.md (navigation guide) | pending |
| 3 | Define Semantic Comparison Matrix 5-dimension standard | pending |
| 4 | Document integration strategy with existing KBs | pending |

---

## 1. KB Naming Convention (Final)

### Format: `F{NN}_{concept}.md`

| Component | Format | Example |
|-----------|--------|---------|
| Prefix | `F` | Foundational concept marker |
| Number | `{NN}` | 01-99, grouped by domain |
| Concept | `_{concept}` | snake_case English |

### Domain Groups

```
F01-F09: Binding & Variables
  F01_variable_binding.md
  F02_mutability_patterns.md
  F03_constant_semantics.md

F10-F19: Scope & Lifetime
  F10_lexical_scope.md
  F11_closure_capture.md
  F12_resource_lifetime.md

F20-F29: Type Systems
  F20_static_vs_dynamic_typing.md
  F21_type_inference.md
  F22_generics_parametric_polymorphism.md
  F23_null_safety.md

F30-F39: Memory & Concurrency
  F30_memory_models.md
  F31_concurrency_primitives.md
  F32_async_patterns.md

F40-F49: Functions & Control Flow
  F40_function_first_class.md
  F41_error_handling_patterns.md

F50-F59: Data Structures
  F50_collections_overview.md
  F51_hash_maps.md
```

---

## 2. KB_TEMPLATE.md Structure (7-Component)

```markdown
# F{NN}: {Concept Name}

> **Concept ID**: `F{NN}_{concept}`
> **Universal Principle**: {One-line language-agnostic definition}
> **Tier**: 1-3 (Beginner/Intermediate/Advanced)
> **Prerequisites**: F{XX}, F{YY} (optional)

---

## 1. Universal Concept
{2-3 paragraphs explaining the language-agnostic principle}
**Mental Model**: {Analogy or diagram}

---

## 2. Semantic Comparison Matrix

### 2.1 Quick Reference Table
| Dimension | Java | Python | TypeScript | Go | SQL | C++ | Spark |
|-----------|------|--------|------------|----|----|-----|-------|
| **Binding/Mutation** | | | | | | | |
| **Scope/Lifetime** | | | | | | | |
| **Type Enforcement** | | | | | | | |
| **Memory/Concurrency** | | | | | | | |
| **Interview Pitfalls** | | | | | | | |

### 2.2 Semantic Notes (3-5 bullets per dimension)
{Bullet point explanations}

---

## 3. Code Examples (Per Language)

### 3.1 Java
```java
// Working, syntax-correct example
```
**Key Insight**: {What Java emphasizes}

### 3.2 Python
```python
# Working, syntax-correct example
```
**Key Insight**: {What Python emphasizes}

### 3.3 TypeScript
```typescript
// Working, syntax-correct example
```
**Key Insight**: {What TypeScript emphasizes}

### 3.4 Go
```go
// Working, syntax-correct example
```
**Key Insight**: {What Go emphasizes}

### 3.5 SQL
```sql
-- Working, syntax-correct example
```
**Key Insight**: {What SQL emphasizes}

### 3.6 C++
```cpp
// Working, syntax-correct example
```
**Key Insight**: {What C++ emphasizes}

### 3.7 Spark (PySpark)
```python
# Working, syntax-correct example
```
**Key Insight**: {What Spark emphasizes}

---

## 4. Palantir Context
**Foundry Usage**: {How this concept manifests in Palantir stack}
**Interview Relevance**: {What interviewers probe}
**Source**: {Blueprint/OSDK/Foundry docs reference}

---

## 5. Design Philosophy

### 5.1 Primary Sources
| Language | Creator/Source | Quote |
|----------|----------------|-------|
| Java | James Gosling / JLS | "{quote}" |
| Python | Guido van Rossum / PEP | "{quote}" |
| TypeScript | Anders Hejlsberg | "{quote}" |
| Go | Rob Pike / Effective Go | "{quote}" |

### 5.2 Trade-off Analysis
{What problem this concept solves vs. what it costs}

---

## 6. Practice Exercise

### 6.1 Socratic Level Check (Protocol A)
> 1) Definition: {concept definition question}
> 2) Application: {code application question}
> 3) Boundary: {edge case question}

### 6.2 Multi-Language Challenge (Protocol B)
**Goal**: Implement {X} in 3+ languages, compare behavior.
**Time Options**: 10-min micro | 30-min standard
**Acceptance Criteria**: {specific testable outcomes}

---

## 7. Cross-References
- **Existing KBs**: → 00a, 01_language_foundation
- **Related Concepts**: → F{XX}, F{YY}
- **Interview Patterns**: → {specific interview types}
```

---

## 3. Semantic Comparison Matrix (5 Dimensions)

| Dimension | Definition | Interview Focus |
|-----------|------------|-----------------|
| **Binding/Mutation** | Name rebinding vs value mutation | `const` ≠ immutability |
| **Scope/Lifetime** | Block/function/module; closure capture | Memory leaks, stale closures |
| **Type Enforcement** | Compile-time vs runtime; nominal vs structural | TypeScript structural typing |
| **Memory/Concurrency** | GC vs manual; threads vs async | Performance, race conditions |
| **Pitfalls** | Common beginner mistakes | Interview trick questions |

---

## 4. Language Priority

| Priority | Languages | Coverage Rule |
|----------|-----------|---------------|
| **P0** | Java, Python, TypeScript | MUST have complete sections |
| **P1** | Go, SQL | Should have complete sections |
| **P2** | Spark, C++ | Can have "See Also" pointers |

---

## 5. Integration Strategy

### Existing KB Updates (Minimal)
Add footer to relevant KBs (00a, 00b, etc.):

```markdown
---
## Cross-Language Reference
For cross-language comparison, see:
- F01_variable_binding.md
- F10_lexical_scope.md
```

### SYSTEM_DIRECTIVE.md Updates
Add Tier 0 (Cross-Language) routing:

```xml
<tier id="0" name="Cross-Language" signals="['비교', '차이', 'vs', '면접', 'interview']">
    - Variable binding → F01_variable_binding.md
    - Scope/closure → F10_lexical_scope.md
    - Type systems → F20_static_vs_dynamic_typing.md
</tier>
```

---

## Agent Registry

| Task | Agent ID | Status |
|------|----------|--------|
| Explore existing KB | aff9307 | completed |
| Plan KB structure | a3c0399 | completed |

---

## Quick Resume After Auto-Compact

1. Read this file: `.agent/plans/phase2_kb_structure_design.md`
2. Continue from first pending task in Implementation Tasks
3. Reference synthesized design decisions above

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Template too complex | Medium | Medium | Start with F01 pilot |
| Cross-language coverage gaps | Medium | High | Use context7 for verification |
| Integration confusion | Low | Medium | Clear linking documentation |

---

## Approval Gate

- [ ] KB_TEMPLATE.md structure approved
- [ ] Naming convention (F{NN}_concept) approved
- [ ] 5-Dimension Matrix format approved
- [ ] Integration strategy approved
- [ ] Ready for /execute
