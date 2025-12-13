import os
import json
import argparse
from datetime import datetime
from scripts.ontology.plan import Plan

# Configuration
TEMPLATE_DIR = "/home/palantir/orion-orchestrator-v2/.agent/handoffs/templates"
PENDING_DIR = "/home/palantir/orion-orchestrator-v2/.agent/handoffs/pending"
PLANS_DIR = "/home/palantir/.agent/plans" # Assuming plans are stored here

def load_template(role: str) -> str:
    """Loads the markdown template for the given role."""
    filename = f"claude_architect.md" if role.lower() == "architect" else f"gpt_mechanic.md"
    path = os.path.join(TEMPLATE_DIR, filename)
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Template not found for role: {role} at {path}")
        
    with open(path, 'r') as f:
        return f.read()

def generate_handoff(plan_path: str, job_index: int):
    """
    Generates a Handoff Markdown file from a Plan + Job.
    
    Args:
        plan_path: Path to the Plan JSON file.
        job_index: Index of the Job in the Plan's job list (0-based).
    """
    # 1. Load Plan
    if not os.path.exists(plan_path):
        raise FileNotFoundError(f"Plan file not found: {plan_path}")
        
    with open(plan_path, 'r') as f:
        plan_data = json.load(f)
    
    # Simple validation using Pydantic model logic (simplified here for script speed)
    plan_id = plan_data.get("id")
    objective = plan_data.get("objective")
    jobs = plan_data.get("jobs", [])
    
    if job_index >= len(jobs):
        raise ValueError(f"Job Index {job_index} out of range for Plan {plan_id} (Total Jobs: {len(jobs)})")
        
    job = jobs[job_index]
    role = job.get("role", "Automation") # Default to Automation if not set
    job_id = job.get("id")
    
    print(f"🔄 Generating Handoff for Job {job_id} ({role})...")
    
    # 2. Load Template
    template_content = load_template(role)
    
    # 3. Prepare Context
    # Map Job fields to Template Placeholders
    context_files = "\n".join([f"- `{f}`" for f in job.get("input_context", [])])
    if not context_files:
        context_files = "(No specific context files provided. Phase 1 Research recommended.)"
        
    instructions = f"""
    **Action**: {job.get('action_name')}
    **Arguments**: {json.dumps(job.get('action_args', {}), indent=2)}
    
    **Description**:
    {job.get('description', 'Execute the specified action.')}
    """
    
    # 4. Fill Template
    # Using simple string replacement to avoid external dependencies like Jinja2
    content = template_content
    content = content.replace("{{Objective}}", objective)
    # Inject ODA Lifecycle Context
    content = f"# ODA_PHASE: 2. Execution (Relay)\n{content}"
    content = content.replace("{{ContextFiles}}", context_files)
    content = content.replace("{{DetailedInstructions}}", instructions)
    content = content.replace("{{TargetScope}}", context_files) # Reuse for GPT
    content = content.replace("{{ExecutionSteps}}", instructions) # Reuse for GPT
    content = content.replace("{{SafeToAutoRun}}", "False (User Approval Required)")
    content = content.replace("{{JobId}}", job_id)
    
    # 5. Write to Pending
    filename = f"job_{job_id}_{role.lower()}.md"
    output_path = os.path.join(PENDING_DIR, filename)
    
    with open(output_path, 'w') as f:
        f.write(content)
        
    print(f"✅ Handoff Artifact Created: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Handoff Artifacts from Plan")
    parser.add_argument("--plan", required=True, help="Path to Plan JSON")
    parser.add_argument("--job", type=int, required=True, help="Job Index (0-based)")
    
    args = parser.parse_args()
    
    generate_handoff(args.plan, args.job)
