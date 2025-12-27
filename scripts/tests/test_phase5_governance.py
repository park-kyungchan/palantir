
import sys
import time
from typing import ClassVar, Type, List, Optional, Tuple, Any
from sqlalchemy import select
from scripts.ontology.manager import ObjectManager
from scripts.ontology.ontology_types import OrionObject
from scripts.ontology.schemas.governance import OrionActionLog
from scripts.ontology.schemas.memory import OrionInsight
from scripts.simulation.core import ActionRunner
from scripts.ontology.actions import ActionType, ActionContext, EditOperation
from scripts.consolidation.miner import ConsolidationMiner
from scripts.ontology.db import objects_table

# --- MOCKS ---
class GovernanceTestServer(OrionObject):
    state: str = "OK"

class FragileAction(ActionType[GovernanceTestServer]):
    api_name: ClassVar[str] = "test.fragile"
    object_type: ClassVar[Type[GovernanceTestServer]] = GovernanceTestServer
    
    async def apply_edits(self, params: dict, context: ActionContext) -> Tuple[Optional[GovernanceTestServer], List[EditOperation]]:
        manager = context.metadata["manager"]
        session = context.metadata.get("session")
        
        # Access ID from params (expecting it to be there)
        obj_id = params["id"]
        obj = manager.get(GovernanceTestServer, obj_id, session=session)
        obj.state = "BROKEN" # State change attempt
        manager.save(obj, session=session)
        
        # EXPLODE
        raise RuntimeError("Planned Explosion")

def run_test():
    print("=== PHASE 5 GOVERNANCE & CONSOLIDATION TEST ===")
    
    om = ObjectManager()
    om.register_type(GovernanceTestServer)
    om.register_type(OrionActionLog)
    om.register_type(OrionInsight)
    
    # Setup Data
    gov_id = f"SRV-GOV-{int(time.time())}"
    srv = GovernanceTestServer(id=gov_id)
    om.save(srv)
    print("Setup: Server Created.")
    
    runner = ActionRunner(om)
    unique_trace_id = f"job-gov-{int(time.time())}"
    
    # Context creation ODA style + LegacyCompat
    ctx = ActionContext(
        actor_id="tester",
        correlation_id=unique_trace_id, 
        metadata={"params": {"id": srv.id}}
    )
    ctx.parameters = ctx.metadata["params"] # Legacy Compat for Runner
    
    # 1. Execute Fragile Action (Expect Failure)
    print("\n[Step 1] Executing Fragile Action...")
    try:
        runner.execute(FragileAction(), ctx)
    except RuntimeError:
        print("Caught Expected RuntimeError.")
        
    # 2. Verify Rollback (Reality)
    om.default_session.expire_all()
    srv_check = om.get(GovernanceTestServer, srv.id)
    assert srv_check.state == "OK", "Rollback failed! State is BROKEN."
    print("[PASS] UnitOfWork Rolled Back Business Data.")
    
    # 3. Verify Log Persistence (Audit)
    # Use raw SQL to find the log since ID is unknown
    session = om.default_session
    
    stmt = select(objects_table).where(objects_table.c.type == "OrionActionLog")
    raw_logs = session.execute(stmt).fetchall()
    
    found_log = None
    target_job_id = unique_trace_id
    
    # Filter for the specific trace_id to avoid matching old logs from previous runs
    for row in raw_logs:
        if row.data.get('action_type') == "test.fragile" and row.data.get('trace_id') == target_job_id:
            found_log = row
            break
            
    if found_log is None:
        print(f"[DEBUG] Available Logs: {[r.data.get('trace_id') for r in raw_logs]}")
            
    assert found_log is not None, f"Audit Log for {target_job_id} NOT found in DB!"
    data = found_log.data
    print(f"[DEBUG] Found Log Data: {data}")
    assert data['status'] == "FAILURE", f"Log status is {data['status']}"
    assert "Planned Explosion" in str(data.get('error')), f"Error msg mismatch: {data.get('error')}"
    print("[PASS] Audit Log Persisted despite Rollback.")

    # 4. Consolidation (Mining)
    print("\n[Step 2] Running Consolidation Miner...")
    # Trigger 2 more failures to hit threshold (default 2? or 3?)
    ctx2 = ActionContext(actor_id="tester", correlation_id="job-gov-2", metadata={"params": {"id": srv.id}})
    ctx2.parameters = ctx2.metadata["params"]
    try: runner.execute(FragileAction(), ctx2) 
    except: pass
    
    miner = ConsolidationMiner(om)
    miner.mine_failures()
    
    # Check for Insight
    stmt_insight = select(objects_table).where(objects_table.c.type == "OrionInsight")
    insights = session.execute(stmt_insight).fetchall()
    
    found_insight = False
    for row in insights:
        summary = row.data['content']['summary']
        if "test.fragile" in summary and "Planned Explosion" in summary:
            found_insight = True
            print(f"[PASS] Insight Generated: {summary}")
            break
            
    assert found_insight, "Miner failed to generate Insight!"
    print("\n=== PHASE 5 VERIFIED SUCCESSFULLY ===")

if __name__ == "__main__":
    run_test()
