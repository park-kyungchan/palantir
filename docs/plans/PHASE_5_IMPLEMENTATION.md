# Orion Phase 5 Implementation Plan: Adaptive Tutoring Engine

**Status**: DRAFT
**Target**: `scripts/ontology/learning/`
**Objective**: Transition from Prompt-based Learning to Engine-backed Adaptive Tutoring.

---

## 🏗️ Architectural Restructuring

We will create a new package `scripts/ontology/learning/` to house the tutoring engine. The existing `learning.py` will be refactored into a CLI entry point that invokes this new engine.

### Directory Structure

```text
scripts/ontology/learning/
├── __init__.py
├── types.py            # Pydantic models (LearnerState, FileMetrics, TCScore)
├── metrics.py          # AST Visitors for Cognitive Complexity & Novelty
├── graph.py            # Dependency Graph Builder (Import Analysis)
├── scoping.py          # ZPD Calculation & File Selection
├── persistence.py      # Async SQLite adapter for Learner State
└── engine.py           # Main Orchestrator (TCS Calculation + Curriculum Gen)
```

---

## 📅 Phased Execution Roadmap

### Phase 5.1: The Metric Engine (Foundations) [COMPLETED]
**Goal**: Enable mathematical quantification of code complexity (TCS).

1.  **Define Domain Models (`types.py`)** [x]
    *   `CodeMetric`: Dataclass for raw counts (loops, nesting, imports).
    *   `TeachingComplexityScore`: Composite score model.
    
2.  **Implement AST Analysis (`metrics.py`)** [x]
    *   `ComplexityVisitor(ast.NodeVisitor)`: Traverse AST to count control flow & nesting.
    *   `ConceptVisitor(ast.NodeVisitor)`: Detect specific patterns (Async, Pydantic, Decorators).

3.  **Implement Dependency Analysis (`graph.py`)** [x]
    *   `ImportParser`: Extract local vs. 3rd-party imports.
    *   `DependencyGraph`: Build DAG and calculate "Depth" score for each file.

4.  **TCS Aggregator (`engine.py`)** [x]
    *   Implement the Phase 5 composite formula:
        `TCS = 0.3*CC + 0.25*DD + 0.2*NC + 0.15*DP + 0.1*HD`

### Phase 5.2: State & Persistence [COMPLETED]
**Goal**: Track learner progress over time.

1.  **Schema Design** [x]
    *   Table `learner_state`: `user_id`, `theta` (ability scope).
    *   Table `knowledge_component`: `component_id`, `p_mastery`, `last_assessed`.

2.  **Persistence Layer (`persistence.py`)** [x]
    *   Async SQLite implementation using `aiosqlite`.
    *   Methods: `get_learner_state()`, `update_mastery()`.

### Phase 5.3: Scoping & Curriculum [COMPLETED]
**Goal**: Select the right content for the learner.

1.  **ZPD Algorithm (`scoping.py`)** [x]
    *   Implement `calculate_zpd_suitability(tcs, user_theta)`.
    *   Implement `topological_sort` to respect dependencies.

2.  **Prompt Engineering (`prompts.py`)** [x]
    *   Migrated templates into `learning.py` context generation.

### Phase 5.4: Integration [COMPLETED]
**Goal**: Wire everything into the CLI.

1.  **Entry Point (`learning.py`)** [x]
    *   Replaced legacy scanner with `TutoringEngine` + `ScopingEngine`.
