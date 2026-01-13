# Agent Handoff & Job Orchestration (ODA Phase 2)

## 1. Concept
In the Orion ODA, complex architectural shifts or large-scale automations are managed via **Job-based Handoffs**. This pattern allows a high-level Orchestrator to delegate atomic, low-level execution tasks to specialized agents (e.g., an "Automation Specialist").

## 2. Handoff Artifacts

### 2.1 Job Manifest (.md)
A human-readable briefing that defines the mission, constraints, and success criteria.
- **Path Pattern**: `.agent/handoffs/pending/job_{id}.md`
- **Sections**: Mission Briefing, Execution Protocol, Input Context, Action Manifest, Handback Instructions.

### 2.2 Plan Document (.json)
A machine-readable specification of the plan, including job IDs, action arguments, and ontology impact.
- **Path Pattern**: `.agent/plans/plan_{timestamp}.json`

## 3. Execution Relay Flow
1. **Orchestration**: Agent A (Orchestrator) identifies a task requiring specialized execution (e.g., Docling fix).
2. **Dispatch**: Agent A generates a Job Manifest and Plan.
3. **Receipt**: Agent B (Specialist) reads the Manifest and Plan as part of a `deep-audit`.
4. **Execution**: Agent B performs the atomic actions described in the manifest.
5. **Confirmation**: Agent B generates a "Job Result" artifact starting with "MISSION ACCOMPLISHED".

## 4. Example: Docling/Mathpix Resolution
- **Job ID**: `job_hwpx_docling_mathpix_01`
- **Objective**: Resolve UTF-8 decode errors in Docling and define a Mathpix fallback strategy.
- **Constraints**: OWPML-only, No HAction (native generation only).

---
**Status**: ACTIVE. This pattern ensures modularity and traceability across multi-agent sessions.
