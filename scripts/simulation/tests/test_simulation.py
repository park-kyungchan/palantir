
import sys
from scripts.ontology.ontology_types import OrionObject
from scripts.ontology.manager import ObjectManager
from scripts.simulation.core import SimulationEngine
from scripts.action.core import ActionDefinition, ActionContext

# --- Mocks ---
class SimTestServer(OrionObject):
    status: str = "Active"

class CrashServer(ActionDefinition):
    @classmethod
    def action_id(cls): return "test.crash_server"
    
    def validate(self, ctx): return True
    
    def apply(self, ctx):
        obj = ctx.manager.get(SimTestServer, ctx.parameters["id"], session=ctx.session)
        obj.status = "Crashed"
        ctx.manager.save(obj, session=ctx.session)

def run_test():
    print("=== STARTING PHASE 3 SIMULATION TEST ===")
    
    om = ObjectManager()
    om.register_type(SimTestServer)
    
    # 1. Reality Setup
    srv = SimTestServer(id="SIM-001", status="Active")
    om.save(srv)
    print(f"Reality State: {srv.status}")
    
    # 2. Run Simulation
    engine = SimulationEngine(om)
    ctx = ActionContext(job_id="job-sim-1", parameters={"id": srv.id})
    action = CrashServer()
    
    print("\n[Running Simulation...]")
    diff = engine.run_simulation([action], [ctx])
    
    # 3. Assert Diff
    print(f"\n[Simulation Result Diff]: {diff}")
    
    assert len(diff.updated) == 1
    assert diff.updated[0]['id'] == "SIM-001"
    assert diff.updated[0]['changes']['status'] == "Crashed"
    print("[PASS] Diff captured correctly.")
    
    # 4. Assert Isolation (Reality Check)
    om.default_session.expire_all()
    real_srv = om.get(SimTestServer, srv.id)
    print(f"Reality State After Simulation: {real_srv.status}")
    
    assert real_srv.status == "Active", "CRITICAL: Simulation leaked to Reality!"
    print("[PASS] Isolation Configured correctly.")
    
    print("=== PHASE 3 SIMULATION TEST PASSED ===")

if __name__ == "__main__":
    try:
        run_test()
    except Exception as e:
        print(f"!!! CRITICAL FAILURE !!! {e}")
        sys.exit(1)
