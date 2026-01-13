# ODA Execution Flow: Prompt-to-Kernel Trace

## Overview
The execution flow of the Ontology-Driven Architecture (ODA) in the Antigravity system follows a structured 3-phase lifecycle. This trace documents how a raw user prompt is transformed into governed system actions.

## Phase 1: Injection (System Prompt)
When a user provides input, the "Kernel" prepends the **System Directive** (`GEMINI.md`) to the context.

- **Purpose**: Establishes the "Rules of Physics" for the agent (The Constitution).
- **Mechanism**: Context assembly combines the immutable protocol, dynamic environment state (time, open files), and user input.
- **ODA Rule**: The System Prompt is the source of trust for governance and behavioral mandates (e.g., Socratic Method).

## Phase 2: Cognitive (The Plan)
The LLM processes the injected context and produces a structured **Plan**.

- **Thought Process**: The LLM reasons about the user's intent within the constraints of the protocol.
- **Output**: A sequence of **Tool Calls** (e.g., `read_file`, `search_web`, `run_command`).
- **Isomorphism**: This plan is isomorphic to a "Proposal" in the Palantir Foundry Action System.

## Phase 3: Kernel (Execution & Governance)
The Runtime (`kernel.py` and `marshaler.py`) intercepts the tool calls.

- **Marshaling**: Ensures that raw permissions are never exposed directly to the LLM.
- **Governance Gate**:
    - **Safe Actions**: Executed immediately via standard tools.
    - **Hazardous Actions**: (e.g., destructive edits) Trigger a "Proposal" state requiring human/admin approval.
- **Concurrency Control**: Implements optimistic locking via `version` fields in `OntologyObject` to prevent race conditions.

## Palantir Comparison
| ODA Lifecycle | Palantir Foundry Equivalent |
| :--- | :--- |
| **Injection** | Ontology Metadata & Action Definitions |
| **Cognitive Plan** | AIP Logic / Proposed State Mutations |
| **Kernel Execution** | Foundry Action Service Execution |
