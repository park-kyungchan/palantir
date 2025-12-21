
import sys
# sys.path.append("/home/palantir") # Done by Env usually

from scripts.ontology.ontology_types import OrionObject
from scripts.ontology.manager import ObjectManager
from scripts.action.core import ActionDefinition, ActionContext, ActionRunner, UnitOfWork

# --- Mocks ---
class TestServer(OrionObject):
    value: int = 0

class SuccessAction(ActionDefinition):
    @classmethod
    def action_id(cls): return "test.success"
    
    def validate(self, ctx): return True
    
    def apply(self, ctx):
        obj = ctx.manager.get(TestServer, ctx.parameters["id"], session=ctx.session)
        obj.value = 100
        ctx.manager.save(obj, session=ctx.session)

class FailAction(ActionDefinition):
    @classmethod
    def action_id(cls): return "test.fail"
    
    def validate(self, ctx): return True
    
    def apply(self, ctx):
        obj = ctx.manager.get(TestServer, ctx.parameters["id"], session=ctx.session)
        obj.value = 999 
        ctx.manager.save(obj, session=ctx.session)
        # Crash Here
        raise RuntimeError("Simulated Crash")

# --- Test ---
def run_test():
    print("=== STARTING PHASE 2 TRANSACTION TEST ===")
    
    om = ObjectManager()
    om.register_type(TestServer)
    
    # Setup
    srv = TestServer(id="TEST-TX-001", value=0)
    om.save(srv)
    print(f"Initial State: {srv.value}") # 0
    
    runner = ActionRunner(om)
    ctx = ActionContext(job_id="job-1", parameters={"id": srv.id})
    
    # 1. Success Case
    try:
        runner.execute(SuccessAction(), ctx)
        print("[PASS] Success Action executed.")
    except Exception as e:
        print(f"[FAIL] Success Action threw: {e}")

    # Verify State
    om.default_session.expire_all()
    loaded = om.get(TestServer, srv.id)
    assert loaded.value == 100
    print(f"State after Success: {loaded.value}") # Should be 100

    # 2. Failure Case (Rollback)
    try:
        runner.execute(FailAction(), ctx)
        print("[FAIL] Fail Action did not raise exception!")
    except RuntimeError:
        print("[PASS] Fail Action raised exception as expected.")
    
    # Verify State (Should still be 100, NOT 999)
    om.default_session.expire_all()
    loaded_after_fail = om.get(TestServer, srv.id)
    print(f"State after Fail: {loaded_after_fail.value}")
    
    assert loaded_after_fail.value == 100, f"Rollback Failed! Value is {loaded_after_fail.value}"
    print("=== PHASE 2 TRANSACTION TEST PASSED ===")

if __name__ == "__main__":
    try:
        run_test()
    except Exception as e:
        print(f"!!! CRITICAL FAILURE !!! {e}")
        sys.exit(1)
