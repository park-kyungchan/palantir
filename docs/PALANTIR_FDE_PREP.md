# Palantir FDE/PhD Interview Prep: Orion ODA Architecture

> **Focus**: Demonstrating System Design, Distributed Systems Safety, and "Ontology-First" Thinking.
> **Project**: Orion Orchestrator V3 (Refactored ODA Kernel)

---

## 1. The "Elevator Pitch" (Introduction)
"I built **Orion**, an Ontology-Driven Operating System for AI Agents. Unlike typical chatbot backends, Orion uses a **Schema-First Kernel** that decouples 'Planning' (LLM) from 'Execution' (Code). It prevents AI hallucinations from causing real-world damage by enforcing a strict **Metadata-Driven Governance Layer** (Human-in-the-loop) for all hazardous actions."

---

## 2. Key Architectural Patterns (The "Why")

### A. Ontology Supremacy ("Schema is Law")
*   **Problem**: Most AI agents output unstructured text or loose JSON, leading to "Dictionary-Driven" chaos and type errors.
*   **My Solution**: Implemented strict **Pydantic Models (`Plan`, `Proposal`)** as the contract. The Kernel rejects anything that doesn't validate against the schema.
*   **Palantir Mapping**: Similar to how **Foundry Ontology** forces data to match a rigid schema before it can be used in logic.
*   **Keywords**: *Type Safety, Contract-First Design, Serialization Isolation.*

### B. Governance by Design (Not "If-Statements")
*   **Problem**: Legacy code handled safety via hardcoded checks (`if action == "deploy"...`). This is brittle; adding a new dangerous action requires modifying the kernel core.
*   **My Solution**: Created a **Generic Governance Engine**.
    *   Actions carry metadata (`is_hazardous=True`).
    *   The Engine checks metadata dynamically: `policy = engine.evaluate(action_type)`.
    *   Result: `ALLOW_IMMEDIATE` vs `REQUIRE_PROPOSAL`.
*   **Palantir Mapping**: **AIP Logic & Actions**. Permissions are attached to the Object/Action definition, not the UI code.
*   **Keywords**: *Decoupling, Metadata-Driven Logic, Policy Enforcement Point (PEP).*

### C. Optimistic Locking & ACID Transactions
*   **Problem**: In an async multi-agent environment (Kernel + Human Admin), race conditions occur (e.g., executing a proposal that was just cancelled).
*   **My Solution**: Implemented **Version Control (Optimistic Locking)** in SQLite.
    *   `UPDATE proposals SET status=... WHERE id=? AND version=?`
    *   If `rows_affected == 0`, throw `StaleObjectError` and retry.
*   **Palantir Mapping**: Foundry's **Object Storage V2 (Phonograph)** handling concurrent edits.
*   **Keywords**: *Concurrency Control, Data Integrity, CAS (Compare-And-Swap).*

### D. The "Disconnected Kernel" Refactor (Legacy -> Modern)
*   **Story**: "The system started as a 'Potemkin Village'—hardcoded fake actions. I refactored it into a **Dynamic Registry** system."
*   **Impact**:
    *   Removed `if/else` chains in `OrionRuntime`.
    *   Introduced `ActionRegistry` as the Source of Truth.
    *   Enabled **Plugin Architecture** (new actions can be added without touching the Kernel).
*   **Keywords**: *Refactoring, Technical Debt, Open-Closed Principle.*

---

## 3. Anticipated Interview Questions & Answers

**Q: Why didn't you use an ORM directly?**
> **A**: "I prioritized **transparency and control**. Handling `Proposal` state transitions requires strict logic (State Machine) that I wanted to test explicitly. I implemented a Repository pattern with raw SQL to ensure I fully understood the transaction boundaries and locking mechanisms before abstracting them away with SQLAlchemy. It was a conscious choice to minimize dependencies during the core architectural validation."

**Q: How does this scale to 1000 agents?**
> **A**: "Currently, it uses SQLite WAL mode which handles concurrency well for a single node. For horizontal scaling, I would:
> 1. Move `ProposalRepository` to Postgres/CockroachDB.
> 2. Replace the in-memory `RelayQueue` with Redis/Kafka.
> 3. The **Kernel is stateless** (except for the loop), so we can spin up multiple Kernel workers consuming from the same queue."

**Q: How do you handle AI safety?**
> **A**: "Trust, but Verify. The LLM is **never** given direct execute permission on hazardous tools. It generates a `Plan` (Intent). The Kernel converts this Intent into a `Proposal` object. A Human (or high-level Supervisor Agent) must sign that object (`approve()`) before the Kernel's Execution Loop touches the real world system."

---

## 4. Diagram Concepts (for Whiteboarding)

1.  **The Intake Pipeline**:
    `User Prompt` -> `LLM` -> `JSON(Plan)` -> `Pydantic Validation` -> `Jobs`

2.  **The Governance Gate**:
    `Job` -> `GovernanceEngine(Metadata)` -> `Decision(Safe?)`
    *   If Safe -> `Execute()`
    *   If Hazardous -> `DB(Proposal: PENDING)` -> `Human Approval` -> `DB(Proposal: APPROVED)`

3.  **The Execution Loop**:
    `Kernel(Poller)` -> `DB(Query APPROVED)` -> `ActionRegistry(Lookup)` -> `Execute()`
