
import sys
import os
sys.path.append("/home/palantir/orion-orchestrator-v2")

from scripts.ontology.schemas.result import JobResult, Artifact
from scripts.ontology.manager import ObjectManager

def test_result_persistence():
    print("🧪 Testing JobResult Persistence...")
    
    # 1. Instantiate
    result = JobResult(
        job_id="test-job-001",
        status="SUCCESS",
        output_artifacts=[
            Artifact(path="/tmp/test.txt", description="Test Artifact")
        ],
        metrics={"latency": 50}
    )
    
    print(f"Object Created: {result}")
    
    # 2. Save via Manager
    manager = ObjectManager()
    manager.save(result)
    
    print("Saved to DB.")
    
    # 3. Retrieve
    # We need to query by ID. Result ID is auto-generated (UUIDv7)
    obj_id = result.id
    print(f"Retrieving ID: {obj_id}")
    
    retrieved = manager.get(JobResult, obj_id)
    
    if retrieved and retrieved.job_id == "test-job-001":
        print("✅ SUCCESS: Object retrieved and matches.")
    else:
        print(f"❌ FAILURE: Retrieved object is {retrieved}")

if __name__ == "__main__":
    test_result_persistence()
