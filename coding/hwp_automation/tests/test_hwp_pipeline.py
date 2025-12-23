
import sys
import os
import asyncio
from pathlib import Path

# Add project root to path
sys.path.append("/home/palantir/orion-orchestrator-v2")

# Set API Key (Mocking env var)
os.environ["MATHPIX_APP_KEY"] = "120869bee25107f293c726520c24398bc2e4d8941c8b0573adf1aa1c7859eec0"

from coding.hwp_automation.scripts.pipeline_actions import ExecuteHwpPipelineAction
# We need to mock ActionContext logic if it has dependencies that are hard to satisfy
# Assuming ActionContext is a simple Pydantic model or dataclass

# Mocking dependent modules if they fail to import due to environment
try:
    from scripts.ontology.actions import ActionContext
except ImportError:
    # Create valid mock if import fails
    class ActionContext:
        def __init__(self, actor_id, proposal_id=None, reasoning_trace=None):
            self.actor_id = actor_id
            self.proposal_id = proposal_id
            self.reasoning_trace = reasoning_trace

async def main():
    print("[TEST] Initializing ODA Action: ExecuteHwpPipelineAction")
    action = ExecuteHwpPipelineAction()
    
    # Mock Context
    # We call __init__ directly if it's a class, but usually pydantic model needs arguments?
    # Let's try basic instantiation
    try:
        context = ActionContext(
            actor_id="user_test",
            proposal_id="test_prop_001",
            reasoning_trace="Testing ODA migration"
        )
    except:
        # Fallback if Pydantic
        context = ActionContext(actor_id="user_test")
    
    params = {
        "pdf_path": "/mnt/c/Users/packr/Desktop/sample.pdf",
        "output_dir": "/home/palantir/orion-orchestrator-v2/coding/hwp_automation/output",
        "hwpx_filename": "oda_compliant_output.hwpx",
        "column_count": 2,
        "execute_ps1": False 
    }
    
    print("[TEST] Executing apply_edits...")
    try:
        # ActionType returns (Object, Edits)
        execution_obj, edits = await action.apply_edits(params, context)
        print(f"[TEST] Execution Success!")
        print(f"       Status: {execution_obj.pipeline_status}")
        print(f"       Images: {execution_obj.images_generated}")
        
    except Exception as e:
        print(f"[TEST] Execution Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
