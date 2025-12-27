
import sys
from typing import List, Optional
from pydantic import Field
from datetime import datetime

from scripts.ontology.ontology_types import OrionObject
from scripts.ontology.manager import ObjectManager
from scripts.ontology.db import DB_PATH
from scripts.ontology.schemas.memory import OrionPattern, PatternStructure
from scripts.simulation.core import SimulationEngine, ActionRunner
from scripts.ontology.actions import ActionType, ActionContext, EditOperation, EditType, ActionResult
from typing import ClassVar, Type, List, Optional, Any, Tuple
import asyncio

# --- 1. Define Domain Objects ---
class E2EServer(OrionObject):
    name: str
    server_type: str  # "Legacy" or "Modern"
    status: str = "Unstable"
    cache_cleared: bool = False

# --- 2. Define Actions ---
class ClearCacheAction(ActionType[E2EServer]):
    api_name: ClassVar[str] = "server.clear_cache"
    object_type: ClassVar[Type[E2EServer]] = E2EServer

    async def apply_edits(self, params: dict, context: ActionContext) -> Tuple[Optional[E2EServer], List[EditOperation]]:
        server_id = params["server_id"]
        manager = context.metadata["manager"]
        session = context.metadata.get("session")
        
        server = manager.get(E2EServer, server_id, session=session)
        server.cache_cleared = True
        manager.save(server, session=session)
        print(f"[Action] Cache Cleared for {server.name}")
        return server, []

class RestartServerAction(ActionType[E2EServer]):
    api_name: ClassVar[str] = "server.restart"
    object_type: ClassVar[Type[E2EServer]] = E2EServer

    async def apply_edits(self, params: dict, context: ActionContext) -> Tuple[Optional[E2EServer], List[EditOperation]]:
        server_id = params["server_id"]
        manager = context.metadata["manager"]
        session = context.metadata.get("session")
        
        server = manager.get(E2EServer, server_id, session=session)
        
        # Constraint: Legacy servers explode if cache not cleared
        if server.server_type == "Legacy" and not server.cache_cleared:
            raise RuntimeError(f"Constraint Violation: Legacy Server {server.name} requires cache clear before restart!")
            
        server.status = "Active"
        manager.save(server, session=session)
        print(f"[Action] Server {server.name} Restarted Successfully")
        return server, []

# --- 3. Test Logic ---
def run_e2e_test():
    print("=== STARTING ORION E2E VERIFICATION ===")
    
    om = ObjectManager()
    om.register_type(E2EServer)
    om.register_type(OrionPattern)
    
    # --- SETUP ---
    print("\n[Step 1] Bootstrapping Data...")
    
    # Create Server
    import time
    srv_id = f"SRV-E2E-{int(time.time())}"
    srv = E2EServer(id=srv_id, name="Alpha-Node", server_type="Legacy")
    om.save(srv)
    print(f"Created Server: {srv.id} ({srv.server_type})")
    
    # Create Knowledge (Pattern)
    pat_id = f"PAT-E2E-{int(time.time())}"
    pat = OrionPattern(
        id=pat_id,
        structure=PatternStructure(
            trigger=f"memory_leak detected on legacy systems {int(time.time())}", # Unique trigger for FTS
            steps=["clear_cache", "restart_server"],
            anti_patterns=["direct_restart"]
        )
    )
    om.save(pat)
    print(f"Created Pattern: {pat.id} (Trigger: {pat.structure.trigger})")
    print("Data persisted to SQLite.")

    # --- MEMORY RECALL (FTS) ---
    print("\n[Step 2] Cognitive Search (FTS)...")
    # Simulate searching for "memory_leak"
    import sqlite3
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    # Primitive FTS query (LIKE for simplicity in this env, assuming no FTS5 virtual table setup yet)
    cur.execute(f"SELECT id FROM objects WHERE type='OrionPattern' AND fts_content LIKE '%memory_leak%' AND id='{pat_id}'")
    rows = cur.fetchall()
    found_ids = [r[0] for r in rows]
    
    print(f"Search Query 'memory_leak' found: {found_ids}")
    assert pat_id in found_ids, "FTS Failed to find the pattern!"
    
    recall_opt = om.get(OrionPattern, found_ids[0])
    recommended_steps = recall_opt.structure.steps
    print(f"Recalled Solution Steps: {recommended_steps}")

    # --- SIMULATION 1: NAIVE FAILURE ---
    print("\n[Step 3] Simulation A: Naive Restart (Expecting Failure)...")
    sim_engine = SimulationEngine(om)
    
    # Definition: Just Restart
    ctx_fail = ActionContext(actor_id="system", correlation_id="job-fail", metadata={"params": {"server_id": srv.id}})
    ctx_fail.parameters = ctx_fail.metadata["params"] # Legacy Compat
    action_restart = RestartServerAction()
    
    # Run
    diff_fail = sim_engine.run_simulation([action_restart], [ctx_fail])
    
    # Assert
    # print(f"Diff Result: {diff_fail}")
    assert len(diff_fail.updated) == 0, "Simulation A captured changes but should have failed/rolled back!"
    print("Simulation A Correctly Failed (Safe Rollback Confirmed).")

    # --- SIMULATION 2: INFORMED SUCCESS ---
    print("\n[Step 4] Simulation B: Semantic Plan (Clear -> Restart)...")
    
    ctx_success_1 = ActionContext(actor_id="system", correlation_id="job-ok-1", metadata={"params": {"server_id": srv.id}})
    ctx_success_1.parameters = ctx_success_1.metadata["params"]
    
    ctx_success_2 = ActionContext(actor_id="system", correlation_id="job-ok-2", metadata={"params": {"server_id": srv.id}})
    ctx_success_2.parameters = ctx_success_2.metadata["params"]
    
    action_clear = ClearCacheAction()
    
    # Run Chain
    diff_success = sim_engine.run_simulation(
        [action_clear, action_restart], 
        [ctx_success_1, ctx_success_2]
    )
    
    # Assert
    print(f"Diff Result: {len(diff_success.updated)} updates.")
    assert len(diff_success.updated) >= 1, "Simulation B should have updates"
    
    final_state_change = diff_success.updated[-1] # The last update to the server
    assert final_state_change['id'] == srv.id
    assert final_state_change['changes']['status'] == "Active"
    
    print("Simulation B Successful. Plan Validated.")

    # --- EXECUTION ---
    print("\n[Step 5] Execution in Real Reality...")
    
    # We use ActionRunner directly on Default Session (Reality)
    runner = ActionRunner(om, session=om.default_session)
    
    # 1. Clear Cache
    runner.execute(action_clear, ctx_success_1)
    
    # 2. Restart
    runner.execute(action_restart, ctx_success_2)
    
    # Verify Real Database
    om.default_session.expire_all()
    real_srv = om.get(E2EServer, srv.id)
    
    print(f"Final Real Server Status: {real_srv.status}")
    print(f"Final Real Server Cache: {real_srv.cache_cleared}")
    
    assert real_srv.status == "Active"
    assert real_srv.cache_cleared == True
    
    print("\n=== E2E TEST COMPLETED: SYSTEM FUNCTIONAL ===")

if __name__ == "__main__":
    try:
        run_e2e_test()
    except Exception as e:
        print(f"!!! CRITICAL FAILURE !!! {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
