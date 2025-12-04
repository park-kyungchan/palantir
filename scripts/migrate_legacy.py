import os
import json
import yaml
import shutil
from datetime import datetime, timezone
from typing import Dict, Any

# Paths
LEGACY_ROLES_DIR = ".agent/roles"
LEGACY_TASKS_DIR = ".agent/tasks"
OBJECTS_DIR = ".agent/objects"

def get_timestamp():
    return datetime.now(timezone.utc).isoformat()

def migrate_roles():
    print("🔄 Migrating Roles to Agent Objects...")
    if not os.path.exists(LEGACY_ROLES_DIR):
        print(f"⚠️  {LEGACY_ROLES_DIR} not found. Skipping.")
        return

    for filename in os.listdir(LEGACY_ROLES_DIR):
        if not filename.endswith(".md"):
            continue
            
        role_id = filename.replace(".md", "")
        filepath = os.path.join(LEGACY_ROLES_DIR, filename)
        
        # Read Content (Assuming Markdown with Frontmatter or just Text)
        with open(filepath, 'r') as f:
            content = f.read()
            
        # Construct Agent Object
        agent_object = {
            "id": role_id,
            "type": "Agent",
            "created_at": get_timestamp(),
            "updated_at": get_timestamp(),
            "provenance": "migration_script",
            "role_name": role_id.capitalize(),
            "description": content[:200].strip(), # Extract brief description
            "capabilities": ["general_reasoning", "coding"], # Default capabilities
            "state": "idle"
        }
        
        # Save to Objects Dir
        save_path = os.path.join(OBJECTS_DIR, "Agent", f"{role_id}.json")
        with open(save_path, 'w') as f:
            json.dump(agent_object, f, indent=2)
        print(f"   ✅ Migrated {filename} -> {save_path}")

def migrate_tasks():
    print("🔄 Migrating Tasks to Task Objects...")
    if not os.path.exists(LEGACY_TASKS_DIR):
        print(f"⚠️  {LEGACY_TASKS_DIR} not found. Skipping.")
        return

    for filename in os.listdir(LEGACY_TASKS_DIR):
        if not filename.endswith(".json"):
            continue
            
        task_id = filename.replace(".json", "")
        filepath = os.path.join(LEGACY_TASKS_DIR, filename)
        
        with open(filepath, 'r') as f:
            try:
                legacy_data = json.load(f)
            except json.JSONDecodeError:
                print(f"   ❌ Failed to parse {filename}. Skipping.")
                continue
        
        # Construct Task Object (Mapping Legacy Fields)
        task_object = {
            "id": task_id,
            "type": "Task",
            "created_at": legacy_data.get("created_at", get_timestamp()),
            "updated_at": get_timestamp(),
            "provenance": "migration_script",
            "objective": legacy_data.get("objective", "No objective"),
            "status": legacy_data.get("status", "pending"),
            "assigned_to": legacy_data.get("assigned_to", None),
            "plan_id": legacy_data.get("plan_id", None)
        }
        
        # Save to Objects Dir
        save_path = os.path.join(OBJECTS_DIR, "Task", f"{task_id}.json")
        with open(save_path, 'w') as f:
            json.dump(task_object, f, indent=2)
        print(f"   ✅ Migrated {filename} -> {save_path}")

def main():
    print("🚀 Starting Phase 2 Migration...")
    migrate_roles()
    migrate_tasks()
    print("✨ Migration Complete.")

if __name__ == "__main__":
    main()
