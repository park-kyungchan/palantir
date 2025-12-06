
import time
import traceback
from typing import Dict, Any, List
from scripts.ontology import Plan
from scripts.actions import ActionRegistry
from scripts.observer import EventBus
from scripts.governance import ActionDispatcher, OrionAction

# Create a global dispatcher for Tier 1 Actions
# In a real app, inject this dependency
dispatcher = None 

def get_dispatcher():
    global dispatcher
    if dispatcher is None:
        from scripts.engine import WORKSPACE_ROOT # Circular import risk?
        import os
        workspace = os.path.abspath("/home/palantir") # Hardcoded for safety if import fails
        dispatcher = ActionDispatcher(workspace)
    return dispatcher

def run_loop(plan: Plan) -> Dict[str, Any]:
    """
    Orion Execution Loop v3.0 (Governed).
    Handles both Tier 2 (Function) Tools and Tier 1 (Class) Actions.
    """
    plan_id = plan.plan_id
    print(f"🚀 [Executor] Starting Governed Execution for Plan: {plan_id}")
    
    EventBus.start_trace(plan_id, tags=["execution_loop", "v3"])
    EventBus.log_event("STATE_CHANGE", "Executor", {"status": "STARTED", "plan_id": plan_id})
    
    results = {}
    
    for i, job in enumerate(plan.jobs):
        job_id = job.get("id") or f"job_{i}"
        action_name = job.get("action_name")
        action_args = job.get("action_args", {})
        
        print(f"   ▶️  Job {job_id}: {action_name}")
        EventBus.log_event("JOB_START", "Executor", {"job_id": job_id, "action": action_name})
        
        start_time = time.time()
        result = None
        error = None
        
        try:
            # Inspection: Is it a Tier 1 Class-Based Action?
            # (Future: System Registry for Classes. For now, we assume simple function registry for Tools)
            
            # Lookup Tier 2 Tool
            action_func = ActionRegistry.get_action(action_name)
            
            if action_func:
                # Execute Tier 2 (Tool)
                # Governance for Tools is handled inside the @register wrapper
                print(f"      🤖 Invoking Tool: {action_name}")
                result = action_func(**action_args)
                
            else:
                # Check if it's a Tier 1 Action (Hardcoded Mapping for Phase 3)
                if action_name == "persist_plan":
                    from scripts.ontology_actions import PersistPlanAction, PersistPlanParams
                    # Map args to params
                    params = PersistPlanParams(**action_args)
                    action = PersistPlanAction(params)
                    
                    # Dispatch via Governance Funnel
                    print(f"      🛡️ Dispatching Governed Action: {action_name}")
                    disp_result = get_dispatcher().dispatch(action)
                    result = disp_result.get("result")
                else:
                    raise ValueError(f"Action '{action_name}' not found in Registry or Tier 1 Map.")

            # Success Logging
            duration = time.time() - start_time
            print(f"      ✅ Result: {str(result)[:100]}...") 
            EventBus.log_event("JOB_SUCCESS", "Executor", {
                "job_id": job_id, 
                "action": action_name, 
                "duration_ms": duration * 1000
            })
            results[job_id] = result

        except Exception as e:
            duration = time.time() - start_time
            error = str(e)
            stack = traceback.format_exc()
            print(f"      ❌ Failed: {error}")
            EventBus.log_event("JOB_FAILURE", "Executor", {
                "job_id": job_id, 
                "error": error,
                "stack": stack
            })
            results[job_id] = f"Error: {error}"
            
            # Stop on critical failure? Configurable.
            # break 

    print("🏁 [Executor] Plan Execution Finished.")
    EventBus.log_event("STATE_CHANGE", "Executor", {"status": "COMPLETED"})
    EventBus.end_trace()
    
    return results
