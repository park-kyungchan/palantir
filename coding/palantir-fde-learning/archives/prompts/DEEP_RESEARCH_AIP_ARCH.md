# Deep Research Prompt: Palantir AIP & OSDK Architecture Validation (v2)

**Role**: You are a Principal Software Architect specializing in the **Palantir Foundry Core** and **AIP (Artificial Intelligence Platform)** ecosystem.

**Objective**:
Critique the attached `CODEBASE_DUMP_ODA.txt` (Orion ODA V3) against the *ground truth* of Palantir's actual architecture (OSDK 2.0, AIP Runtime, Apollo Product Spec). Identify where our implementation is "Marketing Fluff" vs. "Engineering Reality."

**Resources**:
You have access to `tavily`, `github`, and `context7`. USE THEM AGGRESSIVELY.
*   **Target Repo for Ground Truth**: `palantir/foundry-platform-python`, `palantir/osdk-ts`.
*   **Key Search Terms**: `Palantir OSDK Client`, `AIP Logic Runtime`, `Apollo manifest.yml`, `Phonograph write-back`.

---

## Part 1: The "Phonograph" vs. OSDK Client (Manager Validation)
**Context**: Our `scripts/ontology/manager.py` implements a complex "Write-Back Caching" mechanism we call "Phonograph Pattern."
**Research Question**:
1.  Does the modern **Foundry Python SDK (`foundry-platform-python`)** actually perform client-side caching like this? Or is it a thin wrapper around APIs?
2.  *Hypothesis:* The `OsdkProvider` in React does caching, but the Python SDK might be stateless.
3.  **Task**: Compare our stateful `ObjectManager` against the actual `foundry.Client` implementation. Are we over-engineering?

## Part 2: AIP Logic & Tool Marshaling (Runtime Validation)
**Context**: Our `scripts/runtime/kernel.py` acts as an "Active Poller" executing Plans.
**Research Question**:
1.  How does the real **AIP Logic Runtime** (the "Blocks" architecture) execute Python code?
2.  Is it a persistent process (like our Kernel) or ephemeral "Serverless Functions" (FaaS)?
3.  **Task**: Determine if our "Long-Running Kernel" is valid for an "AIP Agent," or if we should be simulating "Compute Modules" (short-lived containers).

## Part 3: Apollo Manifesto (Governance Validation)
**Context**: We use `scripts/governance.py` to enforce rules.
**Research Question**:
1.  Search for **"Apollo Product Specification" (manifest.yml)** structure.
2.  Does Apollo use "Starlark" for constraints, or simple YAML?
3.  **Task**: Draft a valid `product-manifest.yml` snippet that *would* theoretically fulfill the governance roles we are simulating in Python.

## Part 4: The "Isomorphism" Table
Create a table comparing **Orion ODA Concepts** vs. **Real Palantir Concepts**:

| Orion ODA Component | Implemented As (Current) | Palantir Real Equivalent | Verdict (Valid/Invalid/Overkill) |
| :--- | :--- | :--- | :--- |
| `ObjectManager` | Write-Back Cache Class | `foundry.Client` (?) | ? |
| `ActionType` | Python Decorator | Ontology Action / Function | ? |
| `ProposalRepository` | SQLite DB | Phonograph / Object Storage | ? |
| `Kernel` | Active Loop | AIP Runtime / Compute Module | ? |

## Deliverable
Produce a markdown report `00_palantir_core_architecture_v2.md`:
1.  **Architecture Diagram Description**: How AIP *actually* works vs. how we built it.
2.  **Code Correction Requests**: Specific refactoring advice (e.g., "Delete `ObjectManager` caching, use standard `lru_cache` because OSDK is stateless").
3.  **Final Verdict**: A 1-10 score on "Architectural Accuracy."

**Input Attachment**: `CODEBASE_DUMP_ODA.txt` (The User will provide this).
