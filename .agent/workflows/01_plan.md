---
description: Define the Ontology and Pipeline Architecture (AIP Style)
---
# 🏗️ Workflow: Ontology & Pipeline Definition

## 🎯 Objective
Transform a raw "User Request" into a validated **Implementation Blueprint**.
This workflow ensures that no code is written without a clear understanding of the **System Ontology**.

## 🔄 Algorithmic Steps

### Phase 1: Context & Ontology Mapping
1.  **Trigger:** User Request received.
2.  **Action:** Use `codebase_investigator` or `grep` to map the **Dependency Graph**.
    - Identify **Source Nodes** (Existing files).
    - Identify **Target Nodes** (New/Modified files).
    - Identify **Edges** (Imports, Calls, API dependencies).

### Phase 2: Deep Research & Architecture Design
1.  **Action:** Use `sequential-thinking` to perform **Deep Research**.
    - **Tech Stack Verification:** Is the request compatible with the current stack (e.g., React 19)?
    - **Pattern Matching:** Are there existing patterns (e.g., AIP Logic) to reuse?
    - **Security Audit:** Does this introduce vulnerabilities?

### Phase 3: Blueprint Generation (JSON)
1.  **Action:** Generate a **JSON Blueprint** defining the pipeline.
    - **Schema:**
      ```json
      {
        "blueprint_version": "1.0",
        "target_ontology": "uclp",
        "changes": [
          { "type": "CREATE", "path": "src/agents/Orion.ts", "desc": "..." },
          { "type": "MODIFY", "path": "src/config.ts", "desc": "..." }
        ],
        "validation_steps": ["npm test", "lint"]
      }
      ```

### Phase 4: Governance Review
1.  **Action:** Self-Critique the Blueprint.
    - **Check:** Does it violate Layer 0 constraints (e.g., Absolute Paths)?
    - **Check:** Is it scalable?
    - **Check:** Is it maintainable?

### Phase 5: Commit & Dispatch
1.  **Action:** Save the Blueprint to `.agent/tasks/task_{uuid}.json`.
2.  **Action:** Dispatch execution jobs using `scripts/orion dispatch`.
