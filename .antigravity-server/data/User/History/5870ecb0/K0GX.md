# Codex ODA Review: Findings & Path Discrepancy (Jan 2026)

## 1. Overview
In January 2026, a "Codex" agent performed an automated audit of the Orion ODA architecture. While the findings were technically specific, local verification revealed a significant discrepancy in search paths.

---

## 2. Technical Findings (Codex Report)

| Severity | Finding | Evidence (Referenced Paths) |
|----------|---------|-----------------------------|
| **CRITICAL** | AIP-Free (Antigravity) runtime is NOT wired into the LLM path. Core logic still hard-codes OpenAI/Ollama. | `scripts/llm/instructor_client.py:18-48`, `scripts/aip_logic/function.py:40-43`, `scripts/ontology/actions/llm_actions.py:28-50` |
| **HIGH** | Audit-before-execution requirement is contradicted by implementation; `ActionRunner` does not persist logs before mutation. | `README.md:8-11`, `scripts/simulation/core.py:81-97` |
| **HIGH** | `ExecuteLogicAction` is a placeholder that never calls the `LogicEngine` or any registry. | `scripts/ontology/actions/logic_actions.py:16-63` |
| **MEDIUM** | Async actions perform synchronous LLM calls, blocking the event loop. | `scripts/ontology/actions/llm_actions.py:23-50` |
| **MEDIUM** | Model defaults are inconsistent (gpt-4o vs llama3.2). | `scripts/aip_logic/function.py:40-43` |
| **LOW** | MCP registry initialization swallows exceptions for Antigravity/Claude config load. | `scripts/mcp_manager.py:326-370` |

---

## 3. Verification Report (January 7, 2026)

### Status: BLOCKED / INCONSISTENT
Local verification of the Codex findings was attempted using the `/deep-audit` protocol but failed at **Stage A (Surface Scan)**.

### Findings:
- **Missing Root Directory**: The `scripts/` directory referenced by Codex does not exist in `/home/palantir/`.
- **Search Scope Discrepancy**: Codex referenced absolute-looking paths like `scripts/llm/...` but `find_by_name` on `/home/palantir` returned no results for these patterns.
- **Potential Reason**: Codex may have been analyzing a nested project directory (e.g., within `park-kyungchan/`) or a previous volume mount that is no longer mapped to the expected root.

### Next Steps for Remediation:
1. Locate the actual project root containing the listed python files.
2. Verify if the logic gaps (AIP-Free wiring, placeholder actions) persist in the local version.
3. Align the LLM adapter to use the Antigravity subscription as intended.
