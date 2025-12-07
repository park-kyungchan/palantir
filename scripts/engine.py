
import argparse
import sys
import logging
import json
import os
from typing import Optional

# Ensure we can import from core components
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.action_registry import ActionRegistry, ActionRunner
from scripts.ontology.plan import Plan
from scripts.ontology.job import Job
from scripts.memory.manager import MemoryManager

# --- SETUP LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class OrionEngine:
    """
    The Central Nervous System of the Orion Agent.
    Coordinates: Input -> Plan -> Governance -> Action -> Memory.
    """
    
    def __init__(self):
        self.registry = ActionRegistry()
        self.runner = ActionRunner(self.registry)
        self.memory = MemoryManager()
        
    def dispatch_plan(self, plan_path: str):
        """
        Execute a Plan file (JSON) after validating it.
        """
        logger.info(f"🚀 Dispatching Plan from: {plan_path}")
        
        # 1. Load Plan
        try:
            with open(plan_path, 'r') as f:
                plan_data = json.load(f)
            plan = Plan(**plan_data)
        except Exception as e:
            logger.error(f"❌ Plan Loading Failed: {e}")
            return
            
        logger.info(f"📋 Objective: {plan.objective}")
        
        # 2. Governance Check (Placeholder for now)
        # In a real system, we'd check if the plan violates any immutable rules.
        logger.info("✅ Plan Committed to Ontology")
        
        # 3. Execution Loop
        total_jobs = len(plan.jobs)
        for i, job in enumerate(plan.jobs, 1):
            logger.info(f"⚙️ Executing Job [{i}/{total_jobs}]: {job.action_name}")
            
            try:
                result = self.runner.execute(job.action_name, **job.action_args)
                logger.info(f"   Scan Success: {str(result)[:100]}...") # Truncate log
                
                # 4. Memory Injection (Short-term)
                # We could log the result back to an ephemeral memory store here
                
            except Exception as e:
                logger.error(f"   ❌ Job Failed: {e}")
                # Logic: Stop on failure? Or continue? 
                # For now, strict stop.
                return

        logger.info("🏁 All Jobs Completed.")
        
        # --- PHASE 5: MEMORY RECALL (Orion) ---
        # Experimental: Post-execution analysis
        # insights = self.memory.mine_insights_from_plan(plan)
        # log insights...

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Orion Engine Dispatcher")
    subparsers = parser.add_subparsers(dest="command")
    
    # Dispatch Command
    dispatch_parser = subparsers.add_parser("dispatch", help="Execute a Plan JSON")
    dispatch_parser.add_argument("--file", required=True, help="Path to plan.json")
    
    args = parser.parse_args()
    
    if args.command == "dispatch":
        engine = OrionEngine()
        engine.dispatch_plan(args.file)
    else:
        parser.print_help()
