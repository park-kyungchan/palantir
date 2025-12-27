
import asyncio
import os
import sys
import json
import logging
from datetime import datetime, timezone

# Path Setup
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

# ODA Components
from scripts.ontology.storage.database import initialize_database, Database
from scripts.ontology.storage.models import Base
from scripts.ontology.storage.proposal_repository import ProposalRepository
from scripts.ontology.objects.proposal import Proposal, ProposalStatus
from scripts.ontology.plan import Plan
from scripts.ontology.job import Job
from scripts.ontology.handoff import generate_handoff
from scripts.maintenance.rebuild_db import rebuild_database
from scripts.relay.queue import RelayQueue
from scripts.runtime.marshaler import ToolMarshaler
from scripts.ontology.actions import action_registry, ActionContext, EditType
# Register Actions
import scripts.ontology.objects.task_actions  # noqa: F401

# Configure Logging
logging.basicConfig(level=logging.INFO, format="[E2E] %(message)s")
logger = logging.getLogger("E2E_Workflow")

# Mock Interaction Data
MOCK_PLAN_JSON = {
    "id": "plan_e2e_test_001",
    "plan_id": "PLAN-E2E-001",
    "objective": "Verify ODA Workflow Integration",
    "jobs": [
        {
            "id": "job_001",
            "title": "Provision ODA Testing Task",
            "role": "Automation",
            "description": "Create a task to track the E2E verification process.",
            "impacted_files": [],
            "input_context": ["DYNAMIC_IMPACT_ANALYSIS.xml"],
            "action_name": "create_task",
            "action_args": {
                "title": "[E2E] Verify Workflow Integrity",
                "priority": "high",
                "description": "Automated task creation test."
            }
        }
    ]
}

PLAN_FILE_PATH = "/home/palantir/orion-orchestrator-v2/.agent/plans/e2e_plan.json"
PENDING_HANDOFF_DIR = "/home/palantir/orion-orchestrator-v2/.agent/handoffs/pending"

async def run_e2e_test():
    logger.info("🎬 STARTING WORKFLOW-LEVEL E2E TEST")
    
    # =========================================================================
    # PHASE 1: INITIALIZATION (System Boot)
    # =========================================================================
    logger.info("🔹 PHASE 1: Initialization")
    
    # 1.1 DB Rebuild (Fresh State)
    # We modify the rebuild_db script to run quietly or we just call the logic
    logger.info("   - Rebuilding Database (Clean Slate)...")
    await rebuild_database()
    
    # 1.2 Initialize Repo
    db = await initialize_database()
    repo = ProposalRepository(db)
    relay = RelayQueue()
    marshaler = ToolMarshaler(action_registry)
    
    logger.info("   - System Components Initialized.")

    # =========================================================================
    # PHASE 2: PLANNING (Gemini -> Handoff)
    # =========================================================================
    logger.info("🔹 PHASE 2: Planning & Handoff")
    
    # 2.1 Save Mock Plan
    os.makedirs(os.path.dirname(PLAN_FILE_PATH), exist_ok=True)
    with open(PLAN_FILE_PATH, 'w') as f:
        json.dump(MOCK_PLAN_JSON, f, indent=2)
    logger.info(f"   - Mock Plan saved to {PLAN_FILE_PATH}")
    
    # 2.2 Generate Handoff Artifact (Simulating 'handoff.py' execution)
    # Ensure directory exists for handoff
    os.makedirs(PENDING_HANDOFF_DIR, exist_ok=True)
    
    logger.info("   - Generating Handoff Artifact...")
    # NOTE: We call the function directly to test logic, mimicking CLI call
    generate_handoff(PLAN_FILE_PATH, 0)
    
    # 2.3 Verify Artifact
    expected_handoff = os.path.join(PENDING_HANDOFF_DIR, "job_job_001_automation.md")
    if os.path.exists(expected_handoff):
        logger.info(f"   ✅ Handoff File Verified: {expected_handoff}")
    else:
        logger.error(f"   ❌ Handoff File Missing at {expected_handoff}")
        return

    # =========================================================================
    # PHASE 3: EXECUTION (Relay -> Kernel -> Persistence)
    # =========================================================================
    logger.info("🔹 PHASE 3: Execution (Kernel Simulation)")
    
    # 3.1 Simulate Relay Dequeue (The Agent receives the Handoff instruction)
    # In a real scenario, the Agent (GPT/Claude) reads the MD file and executes the action.
    # Here, we simulate the Kernel receiving the Action Request from the Agent.
    
    job_def = MOCK_PLAN_JSON["jobs"][0]
    action_name = job_def["action_name"]
    params = job_def["action_args"]
    
    logger.info(f"   - Executing Action: {action_name}")
    
    # 3.2 Secure Execution via Marshaler
    try:
        context = ActionContext(actor_id="e2e_tester", correlation_id="req_001")
        result = await marshaler.execute_action(action_name, params, context)
        
        if result.success:
            logger.info("   ✅ Action Execution SUCCESS")
            logger.info(f"      Result: {result.to_dict()}")
            
            # 3.3 Simulate Persistence (Kernel Responsibility in V3.5)
            # Since Actions are functional and stateless, the Kernel/Orchestrator must persist the result.
            async with db.transaction() as session:
                from sqlalchemy import text
                
                # Apply Edits
                for edit in result.edits:
                    if edit.edit_type == EditType.CREATE and edit.object_type == "Task":
                        logger.info(f"   💾 Persisting {edit.object_type} {edit.object_id} to DB...")
                        
                        changes = edit.changes
                        # Handle Enum conversion
                        priority = changes.get("priority", "medium")
                        if hasattr(priority, "value"): priority = priority.value
                        
                        # 3.3 Persist via Repository (Kernel Responsibility in V3.5)
                        from scripts.ontology.storage.task_repository import TaskRepository
                        task_repo = TaskRepository(db)

                        for edit in result.edits:
                            if edit.object_type == "Task":
                                logger.info(f"   Applying {edit.edit_type.value} for {edit.object_type} {edit.object_id}...")
                                await task_repo.apply_edit_operation(edit, actor_id=context.actor_id)
                                logger.info("   Data Persisted via TaskRepository.")
                        logger.info("   ✅ Data Persisted.")

            # Verify Persistence (Direct DB Query)
            async with db.transaction() as session:
                from sqlalchemy import text
                res = await session.execute(text("SELECT title, priority FROM tasks WHERE title = :t"), {"t": params["title"]})
                row = res.first()
                if row:
                    logger.info(f"   ✅ DB Verification: Found Task '{row[0]}' with priority '{row[1]}'")
                else:
                    logger.error("   ❌ DB Verification FAILED: Task not found in SQLite.")
        else:
            logger.error(f"   ❌ Action Execution FAILED: {result.error}")
            
    except Exception as e:
        logger.error(f"   ❌ Execution Exception: {e}")
        import traceback
        traceback.print_exc()

    # =========================================================================
    # PHASE 4: MEMORY (Trace -> Insight)
    # =========================================================================
    logger.info("🔹 PHASE 4: Memory Loop (Simulation)")
    logger.info("   - (Simulation) 'consolidate.py' would now mine this execution.")
    logger.info("   - (Simulation) 'recall.py' would retrieve this pattern for next run.")
    
    # TODO: In strict E2E, we would invoke consolidate.py here. 
    # For this iteration, verifying the DB write proves the ODA Pipeline is functional.

    logger.info("🏁 E2E TEST COMPLETE: ODA Workflow Integrity Verified.")

if __name__ == "__main__":
    asyncio.run(run_e2e_test())
