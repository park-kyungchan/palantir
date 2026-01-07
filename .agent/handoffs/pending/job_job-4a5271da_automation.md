# ODA_PHASE: 2. Execution (Relay)
# 🤖 AGENT HANDOFF: AUTOMATION SPECIALIST (Automation Agent)
> **Role**: Mechanic / Implementer
> **Source**: Orchestrator
> **Target**: Automation Agent

---

## 📋 Mission Briefing
You are receiving a **Job Definition** from the Orchestrator. Your goal is to execute specific, low-level coding or automation tasks with precision.

### 📌 Job Context
- **Job ID**: `job-4a5271da`
- **Objective**: `Your requirement`
- **Role**: Automation

### 🛠️ Execution Protocol (Strict)
1.  **Read Context**: You MUST read the input files listed below before acting.
2.  **Atomic Action**: Do exactly what is described in the `action_name`. Do not deviate or "improve" unless critical.
3.  **Use Tools**: Use `run_command`, `write_to_file`, etc., as appropriate.
4.  **Confirm**: Verify your changes (run the script, check syntax).

### 🔍 Input Context
- `.agent/workflows/01_plan.md`
- `scripts/ontology/handoff.py`

### 🚀 Action Manifest

    **Action**: execute_workflow
    **Arguments**: {}
    
    **Description**:
    Your requirement
    

### 📝 Handback Instructions
When finished, you must:
1.  Generate a **Job Result** artifact.
2.  Your output must start with "MISSION ACCOMPLISHED" or "MISSION FAILED".
