# ODA Refactoring Mandate: Architecture Alignment (Orion -> Palantir FDE)

## 1. Context & Objective
We have completed a **Deep Research** phase (`docs/Palantir_Deep_Dive.md`) which revealed significant gaps between our current `orion-orchestrator-v2` implementation and the actual Palantir Foundry Architecture.

**Your Goal:** Analyze the **FULL ROOT CODEBASE DUMP (3.4GB)** and the research findings to propose a concrete **Refactoring Plan** that aligns Orion with the Ground Truth.

## 2. Input Artifacts (CRITICAL)
You must read these two files first:
1.  **Ground Truth**: `orion-orchestrator-v2/docs/Palantir_Deep_Dive.md`
    *   *Key Insight*: OSDK is Stateless/SWR, NOT Write-Back Caching.
2.  **Full Codebase Dump**: `orion-orchestrator-v2/coding/palantir-fde-learning/archives/prompts/CODEBASE_DUMP_FULL.txt`
    *   *Scope*: This now includes the ENTIRE `/home/palantir/` workspace (including all hidden configs, history logs, and system files potentially).
    *   *Warning*: The file is extremely large (3.4GB). **DO NOT READ THE WHOLE FILE AT ONCE.** Use `grep` or read specific sections (slices) to verify logic.
    *   *Why*: To ensure zero legacy logic remains, spanning across any config or hidden file.

## 3. Analysis Tasks
1.  **Gap Identification**:
    *   Compare `ObjectManager` (Code) vs `Object Set Service` (Research).
    *   Compare `ActionType` (Code) vs `OntologyEditFunction` (Research).
    *   **Agent Protocols**: Check `GEMINI.md`, `CLAUDE.md`, `.bash_history`, and hidden configs (`.local/`, `.config/`) for any anti-patterns.
2.  **Isomorphism Roadmap**:
    *   How do we refactor `scripts/ontology/manager.py` to mimic the **Stateless SWR** pattern while keeping SQLite persistence?
    *   *Proposal*: Move from `session.commit()` to an explicit `ActionService.execute()` model that invalidates the local cache.

## 4. Output Deliverable
Create a new design document: `orion-orchestrator-v2/docs/design/REF_ARCH_ALIGNMENT_PLAN.md`
*   **Section 1**: The Gap (Code vs Reality).
*   **Section 2**: Refactoring Steps (Phase 1: Deprecate Phonograph, Phase 2: Implement SWR).
*   **Section 3**: Educational value (How this teaches the user about *actual* Palantir Engineering).

**Constraint**: Do NOT start coding yet. We need a solid Plan first.
