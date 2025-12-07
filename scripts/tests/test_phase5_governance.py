
import sys
import time
from sqlalchemy import select
from scripts.ontology.manager import ObjectManager
from scripts.ontology.core import OrionObject
from scripts.ontology.schemas.governance import OrionActionLog
from scripts.ontology.schemas.memory import OrionInsight
from scripts.action.core import ActionDefinition, ActionRunner, ActionContext
from scripts.consolidation.miner import ConsolidationMiner
from scripts.ontology.db import objects_table

# --- MOCKS ---
class GovernanceTestServer(OrionObject):
    state: str = "OK"

class FragileAction(ActionDefinition):
    @classmethod
    def action_id(cls): return "test.fragile"
    
    def validate(self, ctx): return True
    
    def apply(self, ctx):
        obj = ctx.manager.get(GovernanceTestServer, ctx.parameters["id"], session=ctx.session)
        obj.state = "BROKEN" # State change attempt
        ctx.manager.save(obj, session=ctx.session)
        
        # EXPLODE
        raise RuntimeError("Planned Explosion")

def run_test():
    print("=== PHASE 5 GOVERNANCE & CONSOLIDATION TEST ===")
    
    om = ObjectManager()
    om.register_type(GovernanceTestServer)
    om.register_type(OrionActionLog)
    om.register_type(OrionInsight)
    
    # Setup Data
    srv = GovernanceTestServer(id="SRV-GOV-001")
    om.save(srv)
    print("Setup: Server Created.")
    
    runner = ActionRunner(om)
    unique_trace_id = f"job-gov-{int(time.time())}"
    ctx = ActionContext(job_id=unique_trace_id, parameters={"id": srv.id})
    
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
    ctx2 = ActionContext(job_id="job-gov-2", parameters={"id": srv.id})
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
