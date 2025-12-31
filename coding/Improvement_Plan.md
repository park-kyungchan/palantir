# Improvement Plan: `/coding` Directory & FDE Protocol
> **Goal**: Align the `coding/` directory with the **Palantir FDE Learning Protocol (Agile Student-Driven)** and clean up technical debt.

## 1. Requirement Analysis (Gap Analysis)
| Component | Requirement | Current State | Gap |
|:--- |:--- |:--- |:--- |
| **Knowledge Bases** | Must follow **7-component** structure (Concept, Code, Comparison, Foundry Context, Philosophy, Exercise, Next Steps). | High-level architectural overviews (e.g., `00_palantir_core_architecture.md`). | **CRITICAL**: Content does not support "Agile Learning" format. Missing concrete code and exercises. |
| **Tutor Engine** | `run_tutor.py` + `AdaptiveTutoringEngine` must function. | Scripts exist (`run_tutor.py`, `engine.py`). | **VERIFY**: Needs functional testing to ensure it actually generates valid JSON outputs. |
| **Workspace Hygiene** | Clean, unified structure. | ✅ RESOLVED (2025-12-30): `hwp_automation/` removed. | **DONE**: Workspace consolidated. |

## 2. Proposed Improvements

### Phase 1: Protocol Alignment (Refactor KBs)
**Objective**: Rewrite core KBs (`00` to `09`) to match the learning protocol.
- **Action**: For each KB, restructure into:
    1.  **Universal Concept** (The "What")
    2.  **Technical Explanation** (The "How" - Snippets)
    3.  **Cross-Stack Comparison** (TS/Java/Python Table)
    4.  **Palantir Context** (Foundry/Blueprint/OSDK specific connection)
    5.  **Design Philosophy** (Quotes from internal/external authorities)
    6.  **Practice Exercise** (Interview-style coding question)
    7.  **Adaptive Next Steps** (Links to next modules)

### Phase 2: Workspace Consolidation ✅ COMPLETED
**Objective**: Eliminate ambiguity.
- ✅ **DONE (2025-12-30)**: Removed `coding/hwp_automation/` entirely (no archive needed - git history preserves if needed).
- **Action**: `LEARNING_INDEX.md` remains focused on FDE Learning Protocol (no hwp references).

### Phase 3: Tutor Activation
**Objective**: Verify the AI Tutor "Phase 5".
- **Action**: Run `python scripts/ontology/run_tutor.py --target scripts/ontology --user test_user`.
- **Action**: Inspect `.agent/learning/*.json` output.
- **Action**: If successful, document usage in `README.md`.

## 3. Execution Priority
1.  ✅ **Consolidate**: ~~Remove `hwp_automation`~~ DONE (2025-12-30)
2.  **Refactor**: Start with `00_palantir_core_architecture.md` as the "Gold Standard" example.
3.  **Verify**: Test the Tutor.
