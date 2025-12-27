
import sys
from typing import ClassVar, Type, List, Optional, Tuple, Any
from scripts.ontology.ontology_types import OrionObject
from scripts.ontology.manager import ObjectManager
from scripts.simulation.core import SimulationEngine
from scripts.ontology.actions import ActionType, ActionContext, EditOperation

# --- Mocks ---
class SimTestServer(OrionObject):
    status: str = "Active"

class CrashServer(ActionType[SimTestServer]):
    api_name: ClassVar[str] = "test.crash_server"
    object_type: ClassVar[Type[SimTestServer]] = SimTestServer

    async def apply_edits(self, params: dict, context: ActionContext) -> Tuple[Optional[SimTestServer], List[EditOperation]]:
        manager = context.metadata["manager"]
        session = context.metadata.get("session")
        
        obj = manager.get(SimTestServer, params["id"], session=session)
        obj.status = "Crashed"
        manager.save(obj, session=session)
        return obj, []

async def run_test():
    print("=== STARTING PHASE 3 SIMULATION TEST ===")
    
    om = ObjectManager()
    om.register_type(SimTestServer)
    
    # 1. Reality Setup
    import time
    sim_id = f"SIM-{int(time.time())}"
    srv = SimTestServer(id=sim_id, status="Active")
    om.save(srv)
    print(f"Reality State: {srv.status}")
    
    # 2. Run Simulation
    engine = SimulationEngine(om)
    ctx = ActionContext(
        actor_id="tester",
        correlation_id="job-sim-1", 
        metadata={"params": {"id": srv.id}}
    )
    # No legacy parameters needed for simulation engine directly as runner extracts from metadata if needed, 
    # but ActionType.validate uses 'params' passed to it. In my core.py Runner, I added:
    # params = getattr(ctx, "parameters", {})
    # So I MUST set .parameters for getting params in validate?
    # Actually my core.py runner uses: params = getattr(ctx, "parameters", {})
    # Wait, my core.py runner uses `ctx.metadata.get("params", {})` for the LOG.
    # But for VALIDATE: `params = getattr(ctx, "parameters", {})`.
    # And for APPLY: `action.apply_edits(params, ctx)`.
    # So I DO need to set `.parameters` on the context object for my compatibility runner to pick it up!
    ctx.parameters = ctx.metadata["params"]
    
    action = CrashServer()
    
    print("\n[Running Simulation...]")
    diff = await engine.run_simulation([action], [ctx])
    
    # 3. Assert Diff
    print(f"\n[Simulation Result Diff]: {diff}")
    
    assert len(diff.updated) == 1
    assert diff.updated[0]['id'] == srv.id
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
    import asyncio
    try:
        asyncio.run(run_test())
    except Exception as e:
        print(f"!!! CRITICAL FAILURE !!! {e}")
        sys.exit(1)
