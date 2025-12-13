# ⚡ HANDOFF: AUTOMATION TASK (GPT-5.2 Codex)

> **FROM**: Gemini 3.0 Pro (Orchestrator)
> **TO**: GPT-5.2 (Mechanic)
> **PROTOCOL**: `/home/palantir/AGENTS.md`

## 1. OBJECTIVE
{{Objective}}

## 2. TARGET SCOPE
The following files/directories are your workspace:
{{TargetScope}}

## 3. EXECUTION STEPS
{{ExecutionSteps}}

## 4. SAFETY CHECK
- [ ] SafeToAutoRun? {{SafeToAutoRun}}
- [ ] Venv Active? (`source .venv/bin/activate`)

## 5. RELAY PROTOCOL (MANDATORY)
**Completion Requirement**: You MUST generate and execute a Python script to register your result in the Ontology.

**File Path**: `/home/palantir/orion-orchestrator-v2/scripts/ontology/relays/result_job_{{JobId}}.py`

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
        job_id="{{JobId}}",
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
3. Run the script: `python scripts/ontology/relays/result_job_{{JobId}}.py`
