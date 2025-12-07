
# Orion: Ontology-Driven Architecture (ODA) Refactoring Master Plan

> **Synthesis of Deep Research from Palantir Foundry & AIP Architecture**
> **Sources**: Gemini Advanced (Web/App) & Claude 3.5 Sonnet
> **Date**: 2025-12-07

---

## 1. Executive Summary: The "Living Object" Paradigm

The objective is to pivot Orion from a **Plan-Centric Execution Engine** to an **Object-Centric Semantic Operating System**.
Currently, Orion treats data as passive JSON passed through ephemeral task pipelines. The target architecture transforms data into **Living Objects**—persistent Digital Twins that possess identity, maintain history, enforce governance (Actions), and react to the environment (Rules).

We will bridge the "Logic Gap" by implementing a **Phonograph-inspired Object Kernel**, enabling:
1.  **Strict Write-Back**: No more direct DB mutations. All edits go through a Staging/Validation layer.
2.  **Kinetic Actions**: Operations are transactional units with "Submission Criteria" and "Side Effect Isolation".
3.  **Simulation (What-If)**: Leveraging SQLite Savepoints to allow agents to "predict" outcomes before committing.
4.  **Neuro-Symbolic Logic**: An Event-Driven Rule Engine (ORE) connecting Object States to LLM reasoning.

---

## 2. Core Architecture: The 4 Pillars

### Pillar I: The Object Kernel (Phonograph)
*   **Concept**: The Source of Truth. Replaces raw Pydantic models with "Active Records".
*   **Implementation**:
    *   **Identity**: `UUIDv7` (Time-sorted, Collision-free) for all objects.
    *   **Management**: `ObjectManager` Singleton. Acts as the write-back cache and query engine.
    *   **State Tracking**: Pydantic models with `PrivateAttr` (`_is_dirty`, `_original_state`) to track deltas.
    *   **Persistence**: `SQLAlchemy Core` (High-perf) over `SQLite`.
    *   **Synthesis**: Use **Adjacency List** in SQL for storage, but **NetworkX** in memory for graph traversal (`object.links.path_to(target)`).

### Pillar II: The Kinetic Action Framework
*   **Concept**: Governed Mutation. "You don't edit a row; you submit an Action."
*   **Structure**:
    1.  **Validation (Submission Criteria)**: Pure logic checks (e.g., "Is Server locked?"). Returns Pass/Fail.
    2.  **Staging (EditStore)**: Captures proposed changes (Create, Update, Link) in memory.
    3.  **Atomic Commit (UnitOfWork)**: Applies changes to DB within a Transaction.
    4.  **Side Effects**: External calls (Slack, Git Push) executed *only* after successful Commit.
*   **Refactoring**: Decorators (`@action`) become `ActionType` classes.

### Pillar III: Simulation Substrate (Scenario Fork)
*   **Concept**: Safe Experimentation. "Try before you buy."
*   **Mechanism**:
    *   **SQLite SAVEPOINT**: The low-level isolation mechanism. Creates a named transaction checkpoint.
    *   **ScenarioFork**: The high-level abstraction. Agents "fork" the universe, apply actions, inspect the "Diff", and then `RELEASE` (Commit) or `ROLLBACK` (Discard).
*   **Synthesis**: Gemini's `SAVEPOINT` is the *mechanism*, Claude's `ScenarioFork` is the *interface*.

### Pillar IV: Reactive Logic Engine (ORE)
*   **Concept**: Nervous System. "When X happens, trigger Y."
*   **Implementation**:
    *   **Event Bus**: `ObjectManager` emits `ObjectChanged` events on commit.
    *   **Observer**: `AutomationLayer` listens for events (e.g., `Server.status == 'Down'`).
    *   **AIP Logic**: Connects specific events to LLM Routines (e.g., "Analyze Error Log").
    *   **Library**: `pyventus` or custom `Observer` implementation.

---

## 3. Implementation Roadmap

### Phase 1: The Object Kernel Foundation (Weeks 1-2)
**Goal**: Establish the "Living Object" and persistence layer.
1.  **Dependency Injection**: Install `sqlalchemy`, `networkx`, `uuid6` (for v7).
2.  **Schema Definition**: Create `scripts/ontology/core.py`.
    *   `OrionObject` base class (Pydantic v2 + UUIDv7).
    *   `LinkType` definitions.
3.  **ObjectManager**: Implement `scripts/ontology/manager.py`.
    *   CRUD operations.
    *   Write-Back Buffer logic.

### Phase 2: Transaction & Action Layer (Weeks 3-4)
**Goal**: Governance and isolated side effects.
1.  **Action Framework**: Create `scripts/action/core.py`.
    *   `ActionDefinition` ABC (Abstract Base Class).
    *   `EditStore` for staging changes.
2.  **Registry Migration**: Refactor `action_registry.py` to use `ActionDefinition`.
3.  **Execution Engine**: Update `engine.py` to use `UnitOfWork` pattern.

### Phase 3: Simulation & Logic (Weeks 5-6)
**Goal**: Dynamic Impact Analysis and Automation.
1.  **Simulation Engine**: Implement `scripts/simulation/core.py`.
    *   `ScenarioFork` using `con.savepoint()`.
    *   Exposure of "Diff Views" to the Agent.
2.  **Rules Engine**: Create `scripts/automation/core.py`.
    *   Event Emitter in `ObjectManager`.
    *   Simple declarative rule registration.

### Phase 4: Migration (Week 7)
**Goal**: Port existing data structures.
1.  **Migrate Plans**: Convert `Plan/Job` (from `plan.py`) into `Intents` and `Operations` (Ontology Objects).
2.  **Migrate Memory**: Convert `Insight/Pattern` (from `memory/`) into Ontology Objects.

---

## 4. Conflict Resolution & Design Decisions

| Decision Point | Claude's Proposal | Gemini's Proposal | **Final Decision** |
|:---:|:---:|:---:|:---:|
| **Identity** | Pydantic default | UUIDv7 (Time-ordered) | **UUIDv7**: Critical for distributed merging and consistent sorting. |
| **Logic Layer** | `Experta` (RETE Engine) | `pyventus` (Event Bus) | **Event Bus (Custom)**: Start simple. RETE is overkill for current scale. |
| **Simulation** | In-Memory Copy | SQLite Savepoints | **SQLite Savepoints**: True ACID guarantee for Data; In-Memory overlay for Objects. |
| **Storage** | NetworkX Graph | Relational Adjacency | **Hybrid**: SQL for persistence ("Truth"), NetworkX for runtime analysis ("Reasoning"). |
