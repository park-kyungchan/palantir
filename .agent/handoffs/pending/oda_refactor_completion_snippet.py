
"""
This snippet demonstrates the completed refactoring of the Orion ODA V3 Architecture.
It includes the refactored Action Registry, Policy/Governance Engine, and the Generic Kernel.

Status:
- Phase 1 (Foundation): Complete (No duplicate base classes)
- Phase 2 (Logic Engine): Complete (Metadata-driven governance)
- Phase 3 (Kernel Rewrite): Complete (Schema-driven dispatch)
- Phase 4 (Persistence): Deferred (Using stabilized legacy SQL for now)
"""

from __future__ import annotations
import asyncio
import json
import logging
from typing import Optional, Dict, Type, Any
from dataclasses import dataclass

# =============================================================================
# 1. ACTION REGISTRY & GOVERNANCE (from scripts/ontology/actions.py)
# =============================================================================

@dataclass
class ActionMetadata:
    requires_proposal: bool = False
    is_dangerous: bool = False
    description: str = ""

class ActionRegistry:
    def __init__(self):
        self._actions: Dict[str, tuple[Type[Any], ActionMetadata]] = {}
    
    def register(self, action_class: Type[Any], **metadata_overrides) -> None:
        api_name = getattr(action_class, "api_name", action_class.__name__)
        requires_proposal = metadata_overrides.get(
            "requires_proposal", 
            getattr(action_class, "requires_proposal", False)
        )
        metadata = ActionMetadata(requires_proposal=requires_proposal)
        self._actions[api_name] = (action_class, metadata)

    def get_metadata(self, api_name: str) -> Optional[ActionMetadata]:
        entry = self._actions.get(api_name)
        return entry[1] if entry else None

action_registry = ActionRegistry()

class GovernanceEngine:
    def __init__(self, registry: ActionRegistry):
        self.registry = registry
    
    def check_execution_policy(self, action_name: str) -> str:
        meta = self.registry.get_metadata(action_name)
        if not meta: return "DENY"
        return "REQUIRE_PROPOSAL" if meta.requires_proposal else "ALLOW_IMMEDIATE"

# =============================================================================
# 2. GENERIC KERNEL LOGIC (from scripts/runtime/kernel.py)
# =============================================================================

# Simplified Plan Model for snippet context
class Job:
    def __init__(self, action_type, params):
        self.action_type = action_type
        self.params = params

class MockRepo:
    async def save(self, proposal, action):
        print(f"[DB] Saved Proposal: {proposal['action_type']}")

class OrionRuntime:
    def __init__(self):
        self.governance = GovernanceEngine(action_registry)
        self.repo = MockRepo()

    async def _process_task_cognitive(self, plan_jobs):
        """
        Refactored Logic: No more hardcoded strings.
        """
        print(f"KERNEL: Processing {len(plan_jobs)} jobs...")
        
        for job in plan_jobs:
            # DYNAMIC POLICY CHECK
            policy = self.governance.check_execution_policy(job.action_type)
            
            if policy == "DENY":
                print(f"  ⛔ Action '{job.action_type}' -> DENIED (Unknown)")
            
            elif policy == "REQUIRE_PROPOSAL":
                print(f"  🛡️ Action '{job.action_type}' -> PROPOSAL REQUIRED")
                await self.repo.save({
                    "action_type": job.action_type, 
                    "payload": job.params
                }, action="created")
                
            elif policy == "ALLOW_IMMEDIATE":
                print(f"  ⚡ Action '{job.action_type}' -> EXECUTING IMMEDIATELY")

# =============================================================================
# 3. DEMONSTRATION
# =============================================================================

async def demo():
    # Setup: Register Actions
    class DeployAction:
        api_name = "deploy_production"
        requires_proposal = True
        
    class CheckHealthAction:
        api_name = "check_health"
        requires_proposal = False

    action_registry.register(DeployAction)
    action_registry.register(CheckHealthAction)

    # Execution
    kernel = OrionRuntime()
    
    jobs = [
        Job("check_health", {}),
        Job("deploy_production", {"version": "1.0"}),
        Job("hack_system", {})
    ]
    
    await kernel._process_task_cognitive(jobs)

if __name__ == "__main__":
    asyncio.run(demo())
