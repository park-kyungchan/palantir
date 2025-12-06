import re
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from scripts.ontology import Plan

class RequestRouter:
    """
    Rule-Based Router to bypass LLM for deterministic tasks.
    Uses Regex to map user prompts directly to Actions.
    """
    
    def __init__(self):
        # Define routes: (Regex Pattern, Action Name, Param Mapper Function)
        self.routes = [
            (r"^read file (.+)$", "read_file", lambda m: {"path": m.group(1).strip()}),
            (r"^cat (.+)$", "read_file", lambda m: {"path": m.group(1).strip()}),
            (r"^show tree ?(.*)$", "tree_view", lambda m: {"path": m.group(1).strip() or ".", "max_depth": 2}),
            (r"^tree ?(.*)$", "tree_view", lambda m: {"path": m.group(1).strip() or ".", "max_depth": 2}),
            (r"^check processes$", "list_processes", lambda m: {}),
            (r"^ps$", "list_processes", lambda m: {}),
            (r"^analyze dependency (.+)$", "analyze_dependency", lambda m: {"TargetFile": m.group(1).strip()}),
            (r"^calculate impact (.+)$", "calculate_impact", lambda m: {"TargetFile": m.group(1).strip()}),
            (r"^grep '([^']+)' in (.+)$", "grep_search", lambda m: {"pattern": m.group(1), "path": m.group(2).strip()}),
        ]

    def route(self, user_prompt: str) -> Optional[Plan]:
        """
        Tries to match the user prompt against known patterns.
        Returns a Plan object if a match is found, else None.
        """
        for pattern, action_name, param_mapper in self.routes:
            match = re.match(pattern, user_prompt, re.IGNORECASE)
            if match:
                params = param_mapper(match)
                return self._create_plan(user_prompt, action_name, params)
        return None

    def _create_plan(self, objective: str, action_name: str, params: Dict[str, Any]) -> Plan:
        """Creates a single-job Plan."""
        plan_id = f"plan_{uuid.uuid4().hex[:8]}"
        job_id = f"job_{uuid.uuid4().hex[:8]}"
        
        return Plan(
            id=plan_id,
            type="Plan",
            created_at=datetime.now().isoformat(),
            meta_version=1,
            plan_id=plan_id,
            objective=objective,
            ontology_impact=["System"], # Generic impact
            jobs=[
                {
                    "id": job_id,
                    "action_name": action_name,
                    "action_args": params
                }
            ]
        )

if __name__ == "__main__":
    # Self-Test
    router = RequestRouter()
    test_prompts = [
        "read file scripts/router.py",
        "show tree",
        "calculate impact scripts/ontology.py",
        "write code to fix bug" # Should fail
    ]
    
    print("🧪 Testing Router...")
    for p in test_prompts:
        plan = router.route(p)
        if plan:
            print(f"   ✅ Matched: '{p}' -> {plan.jobs[0]['action_name']}")
        else:
            print(f"   ❌ No Match: '{p}'")
