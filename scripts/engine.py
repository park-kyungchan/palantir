#!/home/palantir/.venv/bin/python
import os
import sys
import json
import argparse
import uuid
from typing import List, Dict, Any
from datetime import datetime

# Fix import path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from scripts.ontology import Plan
from scripts.actions import ActionRegistry

# --- Configuration ---
AGENT_DIR = ".agent"
PLANS_DIR = os.path.join(AGENT_DIR, "plans")
OUTPUTS_DIR = os.path.join(AGENT_DIR, "outputs")
SCHEMAS_DIR = os.path.join(AGENT_DIR, "schemas")
ROLES_DIR = os.path.join(AGENT_DIR, "roles")
WORKSPACE_ROOT = os.path.abspath("/home/palantir")

def load_schema(schema_name):
    schema_path = os.path.join(SCHEMAS_DIR, f"{schema_name}.schema.json")
    if not os.path.exists(schema_path):
        return None
    with open(schema_path, 'r') as f:
        return json.load(f)

def generate_mermaid(plan: Plan) -> str:
    mermaid = ["graph TD"]
    mermaid.append(f'    root["Plan: {plan.objective}"]')
    mermaid.append("    style root fill:#f9f,stroke:#333,stroke-width:4px")
    previous_node = "root"
    for job in plan.jobs:
        job_id = job.id
        action_name = job.action_name
        node_def = f'{job_id}["Action: {action_name}"]'
        mermaid.append(f"    {previous_node} --> {node_def}")
        previous_node = job_id
    mermaid.append(f"    {previous_node} --> End((End))")
    return "\n".join(mermaid)

def init():
    dirs = [PLANS_DIR, OUTPUTS_DIR, SCHEMAS_DIR, ROLES_DIR]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    print(f"✅ Orion Workspace Initialized in {AGENT_DIR}")

def dispatch(args):
    if args.file:
        try:
            with open(args.file, 'r') as f:
                data = json.load(f)
                plan = Plan.model_validate(data)
        except Exception as e:
            print(f"❌ Error reading/validating plan file: {e}")
            sys.exit(1)
    else:
        try:
            # 1. Try Router first (Rule-Based)
            from scripts.router import RequestRouter
            router = RequestRouter()
            plan = router.route(args.task)
            
            if plan:
                print(f"⚡ [Router] Fast-tracked plan via Rule-Based Router: {plan.jobs[0].action_name}")
            else:
                # 2. Fallback to Manual/Legacy creation (Placeholder for now)
                # In a real scenario, this would call the LLM to generate the plan
                print("ℹ️  [Engine] Router miss. Falling back to default plan creation.")
                plan = Plan(
                    id=f"plan_{uuid.uuid4().hex[:8]}",
                    plan_id=str(uuid.uuid4()),
                    objective=args.task,
                    ontology_impact=["Unknown"],
                    jobs=[
                        {
                            "id": "job_1",
                            "action_name": "unknown_action",
                            "description": args.task,
                            "input_context": [args.context] if args.context else [],
                            "evidence": "Manual Dispatch via CLI"
                        }
                    ]
                )
        except Exception as e:
             print(f"❌ Error creating plan: {e}")
             return

    print("🛡️  [Governance] Plan Validated by Pydantic.")
    
    print("🛡️  [Governance] Plan Validated by Pydantic.")
    
    # --- PHASE 3: GOVERNANCE ENFORCEMENT ---
    # Replaced raw/generic write with Governed Action
    from scripts.governance import ActionDispatcher
    from scripts.ontology_actions import PersistPlanAction, PersistPlanParams
    
    dispatcher = ActionDispatcher(WORKSPACE_ROOT)
    action = PersistPlanAction(PersistPlanParams(plan=plan, is_new=True))
    
    try:
        result = dispatcher.dispatch(action)
        print(f"✅ Plan Committed to Ontology: {result['action_id']}")
    except Exception as e:
        print(f"❌ Governance Failure: {e}")
        return
    
    print(f"✅ Plan Dispatched: {plan.plan_id}")
    
    viz_path = os.path.join(PLANS_DIR, f"plan_{plan.plan_id}_viz.md")
    viz_content = f"# 📊 Plan Visualization: {plan.plan_id}\n\n" + generate_mermaid(plan)
    ActionRegistry.get_action("write_to_file")(
        TargetFile=viz_path,
        CodeContent=viz_content
    )
    print(f"📊 Visualization generated: {viz_path}")

def work(args):
    plan_path = os.path.join(PLANS_DIR, f"plan_{args.plan_id}.json")
    if not os.path.exists(plan_path):
        print(f"❌ Plan {args.plan_id} not found.")
        return

    with open(plan_path, 'r') as f:
        data = json.load(f)
        plan = Plan.model_validate(data)
    
    print(f"⚙️  [Orion] Executing Plan: {plan.objective}")
    
    from scripts.loop import run_loop
    results = run_loop(plan)
    
    print(f"✅ Execution Complete. Results: {len(results)} jobs processed.")

def list_actions_command():
    actions = ActionRegistry.list_actions()
    print(f"\n🛠️  Registered Actions ({len(actions)}):")
    for action in actions:
        print(f"  - {action.name}: {action.description}")
        print(f"    Params: {list(action.parameters.get('properties', {}).keys())}")
    print("")

def main():
    parser = argparse.ArgumentParser(description="Orion AI Agent CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    subparsers.add_parser("init", help="Initialize Orion workspace")
    
    dispatch_parser = subparsers.add_parser("dispatch", help="Dispatch a task plan")
    dispatch_parser.add_argument("--file", help="Path to plan JSON file")
    dispatch_parser.add_argument("task", nargs="?", help="Task description")
    dispatch_parser.add_argument("context", nargs="?", help="Context file/dir")

    work_parser = subparsers.add_parser("work", help="Execute a plan")
    work_parser.add_argument("plan_id", help="ID of the plan to execute")
    
    subparsers.add_parser("list-actions", help="List available Actions")

    args = parser.parse_args()

    if args.command == "init":
        init()
    elif args.command == "dispatch":
        dispatch(args)
    elif args.command == "work":
        work(args)
    elif args.command == "list-actions":
        list_actions_command()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
