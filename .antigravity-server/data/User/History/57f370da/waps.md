# Deep Audit Protocol v5.0: Mandatory Rigor

## Overview
The Deep Audit workflow (`/deep-audit`) has been enhanced at the ODA constitutional level to mandate high-fidelity reasoning and external verification. This ensures that audits are grounded in real-time verified data and rigorous architectural analysis.

## 1. Constitutional Mandate (Rule #9)
Rule #9 in `GEMINI.md` (Deep Audit Rigor) strictly enforces the following triggers for any `/deep-audit` execution:

- **Mandate 1: External Verification**: Meticulously use `search_web` (Tavily) to verify internal assumptions against external documentation.
- **Mandate 2: Reasoning Chain**: Use `task_boundary` (Sequential Thinking) to explicitly document the reasoning chain before generating the final report.
- **Constraint**: Report generation is **FORBIDDEN** until these steps are logged.

## 2. Script-Level Enforcement: Audit Guard
Beyond the system prompt, a physical guardrail is implemented via `scripts/governance/audit_guard.py`.

- **Function**: Scans action logs/environment for compliance.
- **Intervention**: Halts execution with a `SystemExit` if the mandatory tools haven't been invoked.
- **Override**: Requires a specific flag (`--verify-override`) to proceed to report generation, ensuring the agent consciously confirms compliance.

## 3. Workflow Phase Enhancements
The `.agent/workflows/deep_audit.md` file includes the following mandatory checkpoints:

### Phase 0: Script-Level Governance
- **Action**: Run Enforcer (`python scripts/governance/audit_guard.py`).
- **Goal**: Immediate physical check of protocol adherence.

### Phase 2.5: External Verification (Tavily)
- **Action**: Use `search_web` tool.
- **Goal**: Research typical folder structures, deprecation status, and best practices for the target stack.
- **Output**: `[TAVILY] Verified {X} patterns against {Source}`.

### Phase 3.5: Reasoning Checkpoint (Sequential Thinking)
- **Action**: Use `task_boundary` update.
- **Goal**: Summarize findings, identify logic gaps, and plan specific code-level checks.
- **Condition**: If logic gaps exist, the audit MUST NOT proceed to Phase 4 (Atomic Quality Audit).

## 4. Rationale
By mandating these tools, the ODA minimizes "probabilistic drift"—the tendency of LLMs to hallucinate or default to generic patterns without verifying the specific codebase state or modern standards.
