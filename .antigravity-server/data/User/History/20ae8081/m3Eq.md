# Implementation Plan - Socratic Agile Learning Mode

## Goal Description
Align the codebase with the "STRICT SOCRATIC METHOD" and "COMPLETELY AGILE" directive. This involves injecting the new system prompt into `GEMINI.md` and implementing the "Codebase-as-Curriculum" engine (`learning.py`) to enable reflective analysis of user code against Palantir FDE Knowledge Bases.

## User Review Required
> [!IMPORTANT]
> **GEMINI.md Update**: I will be appending a large XML block (`<palantir_fde_learning_protocol>`) to your primary system prompt. This fundamentally changes how the AI behaves, enforcing the 7-component response structure.

> [!WARNING]
> **Missing Script**: The directive references `scripts/ontology/learning.py` as an executable analysis tool, but it currently only exists as a data model. I will create the executable logic.

## Proposed Changes

### System Configuration
#### [MODIFY] [GEMINI.md](file:///home/palantir/.gemini/GEMINI.md)
- Inject `<palantir_fde_learning_protocol>` from `SYSTEM_DIRECTIVE.md`.
- Ensure it is placed correctly (e.g., after `<orion_framework_directives>`).

### Ontology & Learning Engine
#### [NEW] [learning.py](file:///home/palantir/scripts/ontology/learning.py)
- Create a new Python script (alongside `scripts/ontology/objects/learning.py` or replacing it if it was meant to be the script - actually, `objects/learning.py` is a class, so I should keep it and make `scripts/ontology/learning.py` the CLI entry point).
- **Features**:
    - **Context Ingestion**: Read file structure.
    - **Pattern Matching**: Map file types/names to KB tiers (e.g., `*.ts` -> KB 01, `*.tsx` -> KB 02).
    - **Isomorphic Analysis**: Generate the JSON mapping.
    - **Gap Analysis**: Identify missing patterns.
- **Dependencies**: `typer` or `argparse`, `pathlib`.

### Workflows
#### [MODIFY] [fde_learn.md](file:///home/palantir/.agent/workflows/fde_learn.md)
- Ensure the workflow invokes the new `learning.py` script for "Codebase-as-Curriculum" phase.

## Verification Plan

### Automated Tests
1. **Script Execution**: Run `python scripts/ontology/learning.py --target /home/palantir/coding --mode concept` and verify it generates a valid JSON in `.agent/learning/`.
2. **Prompt Check**: Verification that `GEMINI.md` contains the protocol.

### Manual Verification
1. Activate mode via `[SYSTEM MODE: Palantir FDE Learning]`.
2. Ask "What is a closure?" and verify the 7-component response logic.
