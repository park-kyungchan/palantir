# Codex ODA Audit & Remediation Master (Jan 2026)

## 1. Initial Findings (Codex Report)
In January 2026, an automated audit by Codex identified several architectural gaps in the Orion ODA system.

| Severity | Finding | Evidence |
|----------|---------|----------|
| **CRITICAL** | Antigravity runtime is NOT wired into the LLM path. Logic hard-codes OpenAI/Ollama. | `instructor_client.py:18-48` |
| **HIGH** | `ActionRunner` does not persist PENDING logs before mutation. | `simulation/core.py:81-97` |
| **HIGH** | `ExecuteLogicAction` is a placeholder returning mock data. | `logic_actions.py:16-63` |
| **MEDIUM** | Async actions perform synchronous LLM calls, blocking the event loop. | `llm_actions.py:23-50` |
| **MEDIUM** | Model defaults are inconsistent (gpt-4o vs llama3.2). | `aip_logic/function.py:40-43` |
| **LOW** | Exception swallowing in MCP registry initialization. | `mcp_manager.py:326-370` |

---

## 2. Verification Report (Jan 7, 2026)
Local verification using the 3-Stage Protocol confirmed 100% of the Codex findings.

- **Antigravity Runtime Gaps**: `InstructorClient.__init__` defaulted to Ollama/OpenAI and did not consume the Antigravity MCP config dynamically.
- **Reactive Logging Failure**: `ActionRunner` log saving was commented out, preventing auditing of failed/hung attempts.
- **Logic Orchestration Gap**: `ExecuteLogicAction` explicitly returned a `mock_output` dictionary.
- **Operational Anti-patterns**: `llm_actions.py` called sync `client.generate()` within async `apply_edits`.

---

## 3. Remediation Roadmap
1. **Antigravity Wiring**: Implement a Provider interface and configuration loader for `.gemini/antigravity/mcp_config.json`.
2. **Atomic Logging**: Enable PENDING log persistence in `ActionRunner`.
3. **Logic Implementation**: Connect `ExecuteLogicAction` to the `LogicEngine` registry.
4. **Async Optimization**: Ensure LLM calls in async actions are properly awaited or run in executors.

---

## 4. Verification & Roadmap Alignment
The ODA implementation was found to have strong alignment with Palantir AIP/Foundry patterns (ActionType, SubmissionCriteria, Side Effects) despite the implementation gaps. 123/123 E2E tests passed following initial refactoring.
