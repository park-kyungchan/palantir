# Palantir Foundry & AIP Core Architecture
> **Status**: Auto-Generated Context from Deep Research
> **Source**: Public Technical Whitepapers, Dev Docs, Engineering Blogs (2024-2025)

## 1. The Ontology (Semantic Layer)
The Ontology is the "Digital Twin" of the organization, decoupling data integration from data consumption.

*   **Structural Isomorphism**:
    *   **Objects**: Rough equivalent to SQL Rows or NoSQL Documents, but with enforced schemas and comprehensive lineage.
    *   **Links**: Directed edges between objects ($Object A \xrightarrow{Link} Object B$). Unlike SQL Foreign Keys, these are first-class citizens optimized for graph traversal.
    *   **Properties**: Strongly typed attributes. OSDK maps these to native language types (e.g., `TS: string`, `Python: str`).

*   **Kinetic Layer (Write Path)**:
    *   **Actions**: The ONLY way to mutate the Ontology from the frontend.
        *   *Analogy*: Redux Actions. You dispatch an Action, the backend verifies permissions/logic, and the state updates.
        *   *Validation*: All edits are transactional and validated against business rules (Functions) before commit.
    *   **Functions**: Logic stored in the Ontology (Code Repos). Can be triggered by Actions or used for derived properties.

## 2. AIP Architecture (The Brain)
AIP (Artificial Intelligence Platform) injects LLM reasoning into the Ontology.

*   **AIP Logic**: A "Serverless LLM Runtime".
    *   **Blocks**: Composable units (Prompt, Tool, Splitter).
    *   **Tool Usage**: LLMs do not "hallucinate" DB queries. They request to use an "Ontology Tool" (e.g., `get_object(id)`), which the system executes securely.
*   **RAG Pattern**:
    *   Foundry does not just "chunk text". It uses **GraphRAG**.
    *   Context is retrieved by traversing the Ontology (Object $\rightarrow$ Link $\rightarrow$ Linked Object) to provide high-fidelity context window to the LLM.

## 3. Apollo (The Nervous System)
Continuous Delivery and Orchestration for the decentralized era.

*   **Constraint-Based Deployment**:
    *   Instead of "Deploy v2 to Prod", Apollo says "Deploy v2 where `constraint: compliance_level >= high`".
    *   **Relevance to FDE**: Frontend assets are versioned and deployed just like backend services. A "Application" in Foundry is a versioned artifact managed by Apollo.

## 4. OSDK (The Bridge)
The Ontology Software Development Kit is the "Compiler" that turns Schema into Code.

*   **Generation Pipeline**:
    *   Ontology Metadata Service (OMS) $\rightarrow$ OSDK Generator $\rightarrow$ `npm/@osdk/client` or `pypi/palantir-osdk`.
*   **Type Safety**:
    *   Changes in Foundry Schema = Compile Error in VS Code.
    *   This "Contract-First" development is the hallmark of Palantir engineering.

## 5. Architectural Isomorphisms for Reflective Analysis
When analyzing user code, map these patterns:

| User Code Pattern | Palantir Isomorphism | Why? |
| :--- | :--- | :--- |
| **Pydantic Models** | **Ontology Object Types** | Both enforce strict schema at the boundary. |
| **Redux/State Actions** | **Ontology Actions** | Both use the Command Pattern to mutate state safely. |
| **Graph/Tree Structures** | **Ontology Links** | Both model connectivity and traversal. |
| **Async Tasks/Queues** | **Apollo/Job Sets** | Both manage asynchronous execution constraints. |
| **Utility Functions** | **Foundry Functions** | Pure logic units operating on data entities. |
