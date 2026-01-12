"""
Orion ODA V3 - Semantic OS Kernel
=================================
Runtime kernel for processing cognitive tasks and proposals.

Performance Optimizations (ODA-RISK-013):
- Parallel proposal execution with configurable concurrency
- Batch processing to reduce DB round-trips
- Caching for frequently accessed data
"""
import asyncio
import os
import json
import logging
from typing import Optional, List

from lib.oda.llm.instructor_client import InstructorClient
from lib.oda.relay.queue import RelayQueue
from lib.oda.ontology.storage import ProposalRepository, initialize_database
from lib.oda.ontology.objects.proposal import Proposal, ProposalPriority, ProposalStatus
from lib.oda.ontology.actions import action_registry, GovernanceEngine, ActionContext
from lib.oda.runtime.marshaler import ToolMarshaler
from lib.oda.aip_logic.engine import LogicEngine  # [AIP Logic Integration]

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

    Performance (ODA-RISK-013):
    - Configurable concurrency for proposal execution
    - Semaphore-based rate limiting
    - Batch processing for efficiency
    """
    def __init__(self):
        self.llm = InstructorClient()
        self.logic_engine = LogicEngine(self.llm)  # [DI] Centralized Logic Engine
        self.relay: Optional[RelayQueue] = None
        self.governance = GovernanceEngine(action_registry)
        self.marshaler = ToolMarshaler(action_registry)
        self.running = True
        self.repo: Optional[ProposalRepository] = None

        # P1.2: Status counters (IndyDevDan status line pattern)
        self._pending_count = 0
        self._executed_count = 0
        self._blocked_count = 0

        # ODA-RISK-013: Performance configuration
        self._max_concurrent_proposals = int(os.environ.get("ORION_MAX_CONCURRENT_PROPOSALS", "5"))
        self._proposal_semaphore: Optional[asyncio.Semaphore] = None
        self._batch_size = int(os.environ.get("ORION_PROPOSAL_BATCH_SIZE", "10"))

        logger.info("Semantic OS Kernel Booting... (Mode: Enterprise Async)")

    async def start(self):
        # Initialize Persistence Layer
        db = await initialize_database()
        self.repo = ProposalRepository(db)
        self.relay = RelayQueue()

        # ODA-RISK-013: Initialize concurrency control
        self._proposal_semaphore = asyncio.Semaphore(self._max_concurrent_proposals)

        logger.info(f"Online. Waiting for Semantic Signals... (concurrency={self._max_concurrent_proposals})")

        # P3-03: Configurable poll interval (DIA v2.1 C5 compliant)
        poll_interval = float(os.environ.get("ORION_POLL_INTERVAL", "1.0"))

        while self.running:
            # 1. Check Relay Queue (Cognitive Tasks) - Non-blocking async call
            task_payload = await self.relay.dequeue_async() if self.relay else None
            if task_payload:
                logger.info(f"Processing Relay Task: {task_payload.get('id', 'unknown')}")
                await self._process_task_cognitive(task_payload)

            # 2. Check Approved Proposals (Execution Worker) - Now parallel
            await self._process_approved_proposals()

            await asyncio.sleep(poll_interval)

    async def _process_approved_proposals(self):
        """
        Execute proposals that have been approved.

        ODA-RISK-013: Uses parallel execution with semaphore-based rate limiting.
        """
        if not self.repo:
            return

        # ODA-RISK-013: Batch fetch with DB-level limit to prevent memory issues
        batch = await self.repo.find_by_status(ProposalStatus.APPROVED, limit=self._batch_size)
        if not batch:
            return

        logger.info(f"Processing batch of {len(batch)} approved proposals.")

        # ODA-RISK-013: Parallel execution with semaphore
        tasks = [self._execute_single_proposal(p) for p in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Log summary
        success_count = sum(1 for r in results if r is True)
        fail_count = sum(1 for r in results if r is False or isinstance(r, Exception))
        if success_count or fail_count:
            logger.info(f"Batch complete: {success_count} succeeded, {fail_count} failed")

    async def _execute_single_proposal(self, p: Proposal) -> bool:
        """
        Execute a single proposal with semaphore-based concurrency control.

        ODA-RISK-013: Rate-limited execution to prevent resource exhaustion.
        """
        async with self._proposal_semaphore:
            logger.info(f"🚀 Executing Proposal {p.id} ({p.action_type})...")
            try:
                # Execute via Marshaler
                raw_payload = p.payload or {}
                trace_id = raw_payload.get("__trace_id") or p.id
                action_params = {
                    k: v for k, v in raw_payload.items()
                    if not str(k).startswith("__")
                }
                result = await self.marshaler.execute_action(
                    action_name=p.action_type,
                    params=action_params,
                    context=ActionContext(
                        actor_id=p.reviewed_by or "system",
                        correlation_id=str(trace_id),
                        metadata={"proposal_id": p.id},
                    )
                )

                await self.repo.execute(
                    p.id,
                    executor_id="kernel",
                    result=result.to_dict()
                )
                self._executed_count += 1
                logger.info(f"✅ Execution verified for {p.id}")
                return True
            except Exception as e:
                logger.error(f"❌ Execution Failed for {p.id}: {e}")
                return False

    def shutdown(self):
        self.running = False
        logger.info("Kernel shutting down.")

    async def _process_task_cognitive(self, task_payload):
        """
        Cognitive Consumption: LLM Analysis -> Ontology Creation.
        Uses Instructor for reliable Plan parsing.
        """
        task_id = task_payload.get("id")
        prompt = task_payload["prompt"]
        logger.info(f"🧠 Thinking... (Analyzing: '{prompt[:30]}...')")
        response: str

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
            immediate_success = 0
            immediate_failed = 0
            proposals_created = 0
            blocked = 0
            for job in plan.jobs:
                action_name = job.action_name
                action_args = job.action_args or {}
                logger.info(f"   Processing Job: {job.id} [{action_name}]")
                
                # A. Governance Check (P1.1: PolicyResult with reason)
                policy = self.governance.check_execution_policy(action_name, action_args)
                
                if policy.is_blocked():
                    self._blocked_count += 1
                    blocked += 1
                    logger.error(f"   ⛔ BLOCKED: {policy.reason}")
                    continue
                
                if policy.decision == "REQUIRE_PROPOSAL":
                    if self.repo:
                        proposal_payload = {
                            **action_args,
                            "__trace_id": task_id,
                            "__plan_id": getattr(plan, "plan_id", None),
                            "__job_id": job.id,
                        }
                        proposal = Proposal(
                            action_type=action_name,
                            payload=proposal_payload,
                            created_by="kernel_ai",
                            priority=ProposalPriority.MEDIUM,
                        )
                        proposal.submit()
                        # save now uses Async ORM
                        await self.repo.save(proposal, actor_id="kernel_ai", comment=policy.reason)
                        self._pending_count += 1
                        proposals_created += 1
                        logger.info(f"   🛡️  Proposal Created: {proposal.id} ({policy.reason})")
                    else:
                        logger.error("   ❌ Repo unavailable, cannot create proposal.")
                        
                elif policy.is_allowed():
                    # Instant Execution
                    logger.info(f"   ⚡ Executing Immediately: {action_name}")
                    result = await self.marshaler.execute_action(
                        action_name=action_name,
                        params=action_args,
                        context=ActionContext(
                            actor_id="system",
                            correlation_id=task_id,
                            metadata={
                                "task_id": task_id,
                                "plan_id": getattr(plan, "plan_id", None),
                                "job_id": job.id,
                            },
                        )
                    )
                    if result.success:
                        self._executed_count += 1
                        immediate_success += 1
                    else:
                        immediate_failed += 1
                        logger.error(f"      ❌ Immediate Execution Failed: {result.error}")

            response = json.dumps(
                {
                    "task_id": task_id,
                    "plan_id": getattr(plan, "plan_id", None),
                    "objective": getattr(plan, "objective", None),
                    "jobs_total": len(getattr(plan, "jobs", []) or []),
                    "proposals_created": proposals_created,
                    "immediate_success": immediate_success,
                    "immediate_failed": immediate_failed,
                    "blocked": blocked,
                },
                ensure_ascii=False,
            )

        except Exception as e:
            logger.error(f"❌ Cognitive Processing Failed: {e}")
            response = json.dumps(
                {"task_id": task_id, "error": str(e)},
                ensure_ascii=False,
            )

        if task_id and self.relay:
            try:
                await self.relay.complete_async(task_id, response)
            except Exception as e:
                logger.error(f"[RelayQueue] Failed to complete task {task_id}: {e}")

        return response

if __name__ == "__main__":
    runtime = OrionRuntime()
    try:
        asyncio.run(runtime.start())
    except KeyboardInterrupt:
        runtime.shutdown()
