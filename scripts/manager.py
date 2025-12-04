import os
import json
from typing import Type, TypeVar, List, Optional
from pydantic import BaseModel
from scripts.ontology import OrionObject, ConfigDict

# Type Variable for Generics
T = TypeVar('T', bound=OrionObject)

OBJECTS_ROOT = ".agent/objects"

class ObjectManager:
    def __init__(self, root_dir: str = OBJECTS_ROOT):
        self.root_dir = root_dir

    def _get_path(self, obj_type: str, obj_id: str) -> str:
        return os.path.join(self.root_dir, obj_type, f"{obj_id}.json")

    def save(self, obj: OrionObject) -> str:
        """Saves an OrionObject to the file system."""
        path = self._get_path(obj.type, obj.id)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, 'w') as f:
            f.write(obj.model_dump_json(indent=2, by_alias=True))
        
        return path

    def load(self, model_class: Type[T], obj_id: str) -> T:
        """Loads an OrionObject from the file system."""
        # Infer type from class name or assume caller knows
        # Note: In a real system, we might need a registry mapping 'Task' -> TaskClass
        obj_type = model_class.__name__
        path = self._get_path(obj_type, obj_id)
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"Object {obj_type}:{obj_id} not found at {path}")
            
        with open(path, 'r') as f:
            data = json.load(f)
            
        return model_class.model_validate(data)

    def list_ids(self, obj_type: str) -> List[str]:
        """Lists all object IDs for a given type."""
        dir_path = os.path.join(self.root_dir, obj_type)
        if not os.path.exists(dir_path):
            return []
            
        return [f.replace(".json", "") for f in os.listdir(dir_path) if f.endswith(".json")]

# Example Usage
if __name__ == "__main__":
    # Temporary Mock Class for Testing until we import real ones
    class Agent(OrionObject):
        role_name: str
        description: str
        capabilities: List[str]
        state: str

    manager = ObjectManager()
    
    print("🔍 Verifying Migrated Agents...")
    agent_ids = manager.list_ids("Agent")
    for aid in agent_ids:
        try:
            agent = manager.load(Agent, aid)
            print(f"   ✅ Loaded Agent: {agent.id} ({agent.role_name})")
        except Exception as e:
            print(f"   ❌ Failed to load {aid}: {e}")
