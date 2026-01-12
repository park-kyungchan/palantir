# ODA_PHASE: 2. Execution (Relay)
# 🤖 AGENT HANDOFF: AUTOMATION SPECIALIST (Automation Agent)
> **Role**: Mechanic / Implementer
> **Source**: Orchestrator
> **Target**: Automation Agent

---

## 📋 Mission Briefing
You are receiving a **Job Definition** from the Orchestrator. Your goal is to execute specific, low-level coding or automation tasks with precision.

### 📌 Job Context
- **Job ID**: `job_hwpx_docling_mathpix_01`
- **Objective**: `Resolve Docling UTF-8 decode failure and model access issues in HWPX pipeline; define Mathpix vs Docling strategy while staying OWPML-only.`
- **Role**: Automation

### 🛠️ Execution Protocol (Strict)
1.  **Read Context**: You MUST read the input files listed below before acting.
2.  **Atomic Action**: Do exactly what is described in the `action_name`. Do not deviate or "improve" unless critical.
3.  **Use Tools**: Use `run_command`, `write_to_file`, etc., as appropriate.
4.  **Confirm**: Verify your changes (run the script, check syntax).

### 🔍 Input Context
- `/home/palantir/hwpx/convert_pipeline.py`
- `/home/palantir/hwpx/lib/ingestors/factory.py`
- `/home/palantir/hwpx/lib/ingestors/docling_ingestor.py`
- `/home/palantir/hwpx/lib/ingestors/pymupdf_ingestor.py`
- `/home/palantir/hwpx/lib/layout/detector.py`
- `/home/palantir/hwpx/lib/ocr/manager.py`
- `/home/palantir/hwpx/lib/ocr/engine.py`
- `/home/palantir/hwpx/lib/compiler.py`
- `/home/palantir/hwpx/lib/owpml/document_builder.py`
- `/home/palantir/hwpx/lib/owpml/package_normalizer.py`
- `/home/palantir/hwpx/docs/ActionTable_2504.pdf`
- `/home/palantir/hwpx/docs/HwpAutomation_2504.pdf`
- `/home/palantir/hwpx/docs/ParameterSetTable_2504.pdf`
- `/home/palantir/hwpx/docs/한글오토메이션EventHandler추가_2504.pdf`
- `/home/palantir/hwpx/docs/OWPML_HWPX_technical_reference_for_AI_agent_framework.md`
- `/home/palantir/hwpx/sample.pdf`

### 🚀 Action Manifest

    **Action**: deep_investigation_and_fix
    **Arguments**: {
  "target": "/home/palantir/hwpx",
  "pdf": "/home/palantir/hwpx/sample.pdf",
  "output": "/home/palantir/hwpx/sample_e2e.hwpx",
  "ingestor_default": "docling",
  "constraints": [
    "OWPML-only output",
    "No Automation/HAction",
    "Schema-first ODA compliance"
  ]
}
    
    **Description**:
    Investigate Docling UTF-8 decode error and model access issues. Propose and implement a fix (Docling config, preprocessing, or Mathpix integration) that preserves OWPML-only pipeline output. Provide clear execution steps and verification logs.
    

### 📝 Handback Instructions
When finished, you must:
1.  Generate a **Job Result** artifact.
2.  Your output must start with "MISSION ACCOMPLISHED" or "MISSION FAILED".
