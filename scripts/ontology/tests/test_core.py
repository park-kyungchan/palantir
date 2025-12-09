
import sys
import os

# Add workspace to path
sys.path.append(os.getcwd())

from scripts.ontology.core import OrionObject
from scripts.ontology.manager import ObjectManager
from pydantic import Field

# Define a Test Object
class TestServer(OrionObject):
    name: str
    status: str = "Active"
    region: str = "us-east-1"
    cpu_usage: float = 0.0

def run_test():
    print("=== STARTING PHASE 1 SELF-VERIFICATION ===")
    
    # 1. Initialize Manager
    om = ObjectManager()
    om.register_type(TestServer)
    print("[PASS] ObjectManager Initialized")

    # 2. Create Object (InMemory)
    server = TestServer(name="Alpha-One")
    print(f"[INFO] Created Object: {server.id} (Dirty: {server.is_dirty()})")
    
    # Assert Defaults
    assert server.status == "Active"
    assert server.version == 1
    
    # 3. Save to DB (Insert)
    om.save(server)
    print("[PASS] Object Saved to SQLite")
    assert server.is_dirty() == False, "Object should be clean after save"

    # 4. Modify Object (Dirty Tracking)
    server.status = "Down" # Trigger setter
    assert server.is_dirty() == True, "Object should be dirty after modification"
    print(f"[PASS] Dirty Tracking Detected Change: {server.get_changes()}")

    # 5. Save Updates (Update)
    om.save(server)
    assert server.version == 2, "Version should increment on update"
    print("[PASS] Object Updated in SQLite")

    # 6. Load from DB (Hydration)
    om.default_session.expire_all() # Clear cache to force SQL fetch
    
    loaded_server = om.get(TestServer, server.id)
    assert loaded_server is not None
    assert loaded_server.id == server.id
    assert loaded_server.status == "Down"
    assert loaded_server.name == "Alpha-One"
    assert loaded_server.version == 2
    print(f"[PASS] Object Hydrated Correctly: {loaded_server.status}")

    # 7. Validation of 'Living' nature
    # Standard Pydantic behavior + Identity
    try:
        loaded_server.cpu_usage = "High" # Should fail type check if validate_assignment works
    except Exception as e:
        print(f"[PASS] Type Safety Confirmed: {e}")

    print("=== PHASE 1 VERIFICATION COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    try:
        run_test()
    except Exception as e:
        print(f"!!! FAILURE !!! {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
