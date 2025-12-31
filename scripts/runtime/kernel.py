
import asyncio
import sys
import logging
from typing import Optional

# Ensure V3 path
sys.path.append("/home/palantir/orion-orchestrator-v2")

from scripts.ontology.client import FoundryClient
# from scripts.llm.ollama_client import HybridRouter, OllamaClient  <-- REMOVED
from scripts.llm.instructor_client import InstructorClient       # <-- ADDED
from scripts.relay.queue import RelayQueue
from scripts.ontology.storage import ProposalRepository, initialize_database
from scripts.ontology.objects.proposal import Proposal, ProposalStatus
from scripts.ontology.actions import action_registry, GovernanceEngine, ActionContext
from scripts.ontology.plan import Plan
from scripts.runtime.marshaler import ToolMarshaler
from scripts.aip_logic.engine import LogicEngine  # [AIP Logic Integration]

# Configure Logging
logging.basicConfig(level=logging.INFO, format="[%(name)s] %(message)s")
logger = logging.getLogger("Kernel")

class OrionRuntime:
    """
    The V3 Semantic OS Kernel (Generic Ontology Engine).
    
    Principles:
    1. Schema is Law: Uses `Plan` Pydantic model.
    2. Registry Supremacy: Actions via `ActionRegistry`.
    3. Metadata Governance: Policy via `GovernanceEngine`.
    4. Deterministic AI: Uses `instructor` for strict JSON outputs.
    5. Logic Injection: Centralized AI Logic Engine.
    """
    def __init__(self):
        # self.router = HybridRouter() # Deprecated in favor of direct Instructor for now
        self.llm = InstructorClient()
        self.logic_engine = LogicEngine(self.llm)  # [DI] Centralized Logic Engine
        self.relay = RelayQueue()
        self.governance = GovernanceEngine(action_registry)
        self.marshaler = ToolMarshaler(action_registry)
        self.running = True
        self.repo: Optional[ProposalRepository] = None
        logger.info("Semantic OS Kernel Booting... (Mode: Enterprise Async)")

    async def start(self):
        # Initialize Persistence Layer
        db = await initialize_database()
        self.repo = ProposalRepository(db)
        
        logger.info("Online. Waiting for Semantic Signals...")
        
        while self.running:
            # 1. Check Relay Queue (Cognitive Tasks) - Non-blocking async call
            task_payload = await self.relay.dequeue_async()
            if task_payload:
                logger.info(f"Processing Relay Task: {task_payload.get('id', 'unknown')}")
                await self._process_task_cognitive(task_payload)
            
            # 2. Check Approved Proposals (Execution Worker)
            await self._process_approved_proposals()
                
            await asyncio.sleep(1)

    async def _process_approved_proposals(self):
        """Execute proposals that have been approved."""
        if not self.repo:
            return

        approved = await self.repo.find_by_status(ProposalStatus.APPROVED)
        if approved:
            logger.info(f"Found {len(approved)} approved proposals.")
            for p in approved:
                logger.info(f"🚀 Executing Proposal {p.id} ({p.action_type})...")
                try:
                    # Execute via Marshaler
                    result = await self.marshaler.execute_action(
                        action_name=p.action_type,
                        params=p.payload,
                        context=ActionContext(actor_id=p.reviewed_by or "system")
                    )
                    
                    await self.repo.execute(
                        p.id, 
                        executor_id="kernel", 
                        result=result.to_dict()
                    )
                    logger.info(f"✅ Execution verified for {p.id}")
                except Exception as e:
                    logger.error(f"❌ Execution Failed for {p.id}: {e}")

    def shutdown(self):
        self.running = False
        logger.info("Kernel shutting down.")

    async def _process_task_cognitive(self, task_payload):
        """
        Cognitive Consumption: LLM Analysis -> Ontology Creation.
        Uses Instructor for reliable Plan parsing.
        """
        prompt = task_payload['prompt']
        logger.info(f"🧠 Thinking... (Analyzing: '{prompt[:30]}...')")
        
        try:
            # 1. Ask LLM for Plan using Instructor (Schema is Law)
            # No manual JSON parsing needed here. Instructor guarantees Pydantic logic.
            # Running in ThreadPool if call is blocking, or using async client if implemented under hood.
            # Assuming InstructorClient wraps async or we run in executor.
            
            # Note: The InstructorClient.generate_plan is now ASYNC (ODA Compliant).
            # We await it directly.
            plan = await self.llm.generate_plan(prompt)
            
            logger.info(f"🐛 Plan Parsed Successfully: {len(plan.jobs)} jobs")

            # 2. Iterate and Dispatch
            for job in plan.jobs:
                logger.info(f"   Processing Job: {job.title} [{job.action_type}]")
                
                # A. Governance Check
                policy = self.governance.check_execution_policy(job.action_type)
                
                if policy == "DENY":
                    logger.error(f"   ⛔ Action '{job.action_type}' unknown or denied.")
                    continue
                
                if policy == "REQUIRE_PROPOSAL":
                    if self.repo:
                        proposal = Proposal(
                            action_type=job.action_type,
                            payload=job.params,
                            created_by='kernel_ai',
                            priority=job.priority
                        )
                        # save now uses Async ORM
                        await self.repo.save(proposal, actor_id="kernel_ai")
                        logger.info(f"   🛡️  Proposal Created: {proposal.id} (Requires Approval)")
                    else:
                        logger.error("   ❌ Repo unavailable, cannot create proposal.")
                        
                elif policy == "ALLOW_IMMEDIATE":
                    # Instant Execution
                    logger.info(f"   ⚡ Executing Immediately: {job.action_type}")
                    result = await self.marshaler.execute_action(
                        action_name=job.action_type,
                        params=job.params,
                        context=ActionContext.system()
                    )
                    if not result.success:
                        logger.error(f"      ❌ Immediate Execution Failed: {result.error}")

        except Exception as e:
            logger.error(f"❌ Cognitive Processing Failed: {e}")

if __name__ == "__main__":
    runtime = OrionRuntime()
    try:
        asyncio.run(runtime.start())
    except KeyboardInterrupt:
        runtime.shutdown()
