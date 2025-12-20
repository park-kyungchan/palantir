# ODA_PHASE: 2. Execution (Relay)
# ⚡ HANDOFF: AUTOMATION TASK (GPT-5.2 Codex)

> **FROM**: Gemini 3.0 Pro (Orchestrator)
> **TO**: GPT-5.2 (Mechanic)
> **PROTOCOL**: `/home/palantir/AGENTS.md`

## 1. OBJECTIVE
Verify Disk Space for ODA Operations

## 2. TARGET SCOPE
The following files/directories are your workspace:
- `/home/palantir/AGENTS.md`

## 3. EXECUTION STEPS

    **Action**: run_command
    **Arguments**: {
  "command": "df -h"
}
    
    **Description**:
    Check available space on /home/palantir. Ensure we have >10GB for testing.
    

## 4. SAFETY CHECK
- [ ] SafeToAutoRun? False (User Approval Required)
- [ ] Venv Active? (`source .venv/bin/activate`)

## 5. RELAY PROTOCOL (MANDATORY)
**Completion Requirement**: You MUST generate and execute a Python script to register your result in the Ontology.

**File Path**: `/home/palantir/orion-orchestrator-v2/scripts/ontology/relays/result_job_job-test-01.py`

**Template**:
```python
#!/usr/bin/env python3
import sys
import os

# Ensure project root is in path
sys.path.append("/home/palantir/orion-orchestrator-v2")

from scripts.ontology.schemas.result import JobResult, Artifact
from scripts.ontology.manager import ObjectManager

def main():
    # 1. Define Result
    result = JobResult(
        job_id="job-test-01",
        status="SUCCESS",
        output_artifacts=[
            # Example: Artifact(path="/path/to/file.py", description="Created File")
        ],
        metrics={}
    )
    
    # 2. Commit to Ontology
    manager = ObjectManager()
    manager.save(result)
    print(f"✅ Job {result.job_id} Result Committed.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Verification Failed: {e}")
        sys.exit(1)
```

**ACTION REQUIRED**:
1. Execute the steps.
2. Create the Relay Result Script using the template above.
3. Run the script: `python scripts/ontology/relays/result_job_job-test-01.py`
