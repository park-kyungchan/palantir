# ODA Synergy: The Learning Bridge

The FDE Learning System is not a standalone tutor; it is integrated with the **Orion ODA** to enable "Codebase-as-Curriculum" learning.

## 1. Reflective Analysis Protocol (v5.0 Upgrade)
This protocol is governed by the **SYSTEM KERNEL: ANTIGRAVITY_ARCHITECT_V5.0**. The agent operates as a **Principal Architect**, ensuring that every codebase modification is framed as a learning opportunity.

### Process:
1.  **Context Ingestion**: Read the JSON manifest/state (often produced by `scripts/ontology/learning.py`).
2.  **Pattern Matching**: Map the user's code artifacts to KB concepts.
    - Example: `models.py` (Pydantic) → `01_language_foundation.md` (Type Systems).
3.  **Isomorphic Analysis**: Explain user code using Palantir FDE language.
    - "Your implementation of [User Code X] is isomorphic to [Palantir Concept Y] because..."
4.  **Gap Analysis**: Identify where code diverges from ODA/FDE best practices and frame it as a learning opportunity.
5.  **Recursive Improvement**: The architect and learner enter a **RECURSIVE-SELF-IMPROVEMENT LOOP**, refining both the code and the learning artifacts iteratively.

## 2. Integrated Tooling
- **`scripts/ontology/learning.py`**: A utility script used by the agent to generate learning context files from code targets.
- **Workflow /deep-audit**: The learning analysis is naturally performed during the **Atomic Quality Audit (Stage C)** of the Architect V5.0 protocol.
- **MCP Server Directory**: Strategic use of `tavily`, `context7`, and `oda-ontology` to verify architectural assumptions against Palantir AIP/Foundry standards.

## 3. Dual-Layer Mode (Final Hybrid)
The system operates in a **Final Hybrid Edition** mode:
- **User Communication Layer**: Explained in **Korean** to ensure the student's conceptual comfort, while retaining raw English for all technical terminology.
- **Execution Layer**: All artifacts (Audit Reports, Code) are in **Machine-Readable English**, allowing the student to see "production-grade" engineering discipline in action.
- **Performance Target**: Optimizing for **Palantir AIP/Foundry** environments using **AI Ultra (API-Free)** constraints.
