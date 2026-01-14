"""
Orion ODA V3 - SubAgent Manager
================================
Parallel sub-agent spawning and orchestration.

Maps to:
- IndyDevDan's infinite-agentic-loop pattern
- Boris Cherny's "5 parallel Claudes" pattern with system notifications

Usage:
    manager = SubAgentManager(max_parallel=5, enable_notifications=True)
    wave = await manager.spawn_agents(["task1", "task2"])
    # System notifications sent automatically on wave complete
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from lib.oda.layer.parallel_notifier import ParallelNotifier, get_notifier

logger = logging.getLogger(__name__)


class SubAgentStatus(str, Enum):
    """Sub-agent execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class SubAgent:
    """
    Represents a spawned sub-agent.

    Boris Cherny pattern: "I number my tabs 1-5"
    - tab_id provides terminal tab identification
    - Enables system notifications per tab
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    task: str = ""
    status: SubAgentStatus = SubAgentStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    wave: int = 1
    tab_id: int = 0  # Boris Cherny pattern: Tab numbering (1-5)
    started_at: float = 0.0
    completed_at: float = 0.0
    needs_input: bool = False  # Flag for input-awaiting state

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "task": self.task,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "wave": self.wave,
            "tab_id": self.tab_id,
            "needs_input": self.needs_input,
            "duration_ms": int((self.completed_at - self.started_at) * 1000)
            if self.completed_at else 0,
        }


@dataclass
class Wave:
    """Represents a wave of parallel sub-agents."""
    number: int
    agents: List[SubAgent] = field(default_factory=list)
    started_at: float = 0.0
    completed_at: float = 0.0
    
    @property
    def is_complete(self) -> bool:
        return all(
            a.status in [SubAgentStatus.COMPLETED, SubAgentStatus.FAILED]
            for a in self.agents
        )
    
    @property
    def success_count(self) -> int:
        return sum(1 for a in self.agents if a.status == SubAgentStatus.COMPLETED)
    
    @property
    def failure_count(self) -> int:
        return sum(1 for a in self.agents if a.status == SubAgentStatus.FAILED)
    
    def to_dict(self) -> dict:
        return {
            "number": self.number,
            "agents": [a.to_dict() for a in self.agents],
            "is_complete": self.is_complete,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
        }


class SubAgentManager:
    """
    Manages parallel sub-agent execution.

    Maps to:
    - IndyDevDan's infinite-agentic-loop orchestration
    - Boris Cherny's "5 parallel Claudes" pattern

    Usage:
        manager = SubAgentManager(max_parallel=5, enable_notifications=True)
        wave = await manager.spawn_agents(["task1", "task2"])
        # System notifications sent automatically
    """

    def __init__(
        self,
        max_parallel: int = 5,
        agent_executor: Callable = None,
        enable_notifications: bool = True,
        notifier: Optional[ParallelNotifier] = None,
    ):
        self.max_parallel = max_parallel
        self.agent_executor = agent_executor
        self.enable_notifications = enable_notifications
        self.notifier = notifier or (get_notifier() if enable_notifications else None)
        self.waves: List[Wave] = []
        self._current_wave: int = 0
        self._tab_counter: int = 0  # Boris Cherny: Tab numbering
    
    async def spawn_agents(
        self,
        tasks: List[str],
        context: Dict[str, Any] = None,
    ) -> Wave:
        """
        Spawn a wave of parallel sub-agents.

        Args:
            tasks: List of task descriptions
            context: Shared context for all agents

        Returns:
            Wave object with spawned agents

        Boris Cherny Integration:
            - Assigns tab_id (1-5, cycling) to each agent
            - Sends system notifications on wave complete
            - Notifies on individual agent completion/failure
        """
        import time

        self._current_wave += 1
        wave = Wave(number=self._current_wave, started_at=time.time())

        # Create agents for each task with tab_id assignment
        for i, task in enumerate(tasks):
            # Boris Cherny: Assign tab numbers 1-5, cycling
            self._tab_counter = (self._tab_counter % self.max_parallel) + 1
            agent = SubAgent(
                task=task,
                wave=self._current_wave,
                tab_id=self._tab_counter,
            )
            wave.agents.append(agent)

        self.waves.append(wave)

        logger.info(f"🌊 Wave {wave.number}: Spawning {len(tasks)} agents")

        # Execute in parallel (respecting max_parallel)
        semaphore = asyncio.Semaphore(self.max_parallel)

        async def run_agent(agent: SubAgent):
            async with semaphore:
                agent.status = SubAgentStatus.RUNNING
                agent.started_at = time.time()

                try:
                    if self.agent_executor:
                        agent.result = await self.agent_executor(
                            agent.task,
                            context or {}
                        )
                    else:
                        # Default: simulated execution
                        await asyncio.sleep(0.1)
                        agent.result = {"status": "simulated", "task": agent.task}

                    agent.status = SubAgentStatus.COMPLETED
                    logger.debug(f"✅ Agent {agent.id} (Tab {agent.tab_id}) completed")

                    # Boris Cherny: Notify on success
                    if self.notifier:
                        await self.notifier.notify_agent_success(
                            tab_id=agent.tab_id,
                            task=agent.task,
                            duration_seconds=time.time() - agent.started_at,
                        )

                except Exception as e:
                    logger.error(f"❌ Agent {agent.id} (Tab {agent.tab_id}) failed: {e}")
                    agent.status = SubAgentStatus.FAILED
                    agent.error = str(e)

                    # Boris Cherny: Notify on failure
                    if self.notifier:
                        await self.notifier.notify_agent_failed(
                            tab_id=agent.tab_id,
                            task=agent.task,
                            error=str(e),
                        )

                finally:
                    agent.completed_at = time.time()

        # Run all agents in parallel
        await asyncio.gather(*[run_agent(a) for a in wave.agents])

        wave.completed_at = time.time()

        logger.info(
            f"✅ Wave {wave.number} complete: "
            f"{wave.success_count}/{len(wave.agents)} succeeded"
        )

        # Boris Cherny: Send wave complete notification
        if self.notifier:
            failed_tasks = [
                a.task[:50] for a in wave.agents
                if a.status == SubAgentStatus.FAILED
            ]
            await self.notifier.notify_wave_complete(
                wave_number=wave.number,
                success_count=wave.success_count,
                total=len(wave.agents),
                failed_tasks=failed_tasks if failed_tasks else None,
            )

        return wave
    
    async def run_infinite_loop(
        self,
        spec: str,
        output_dir: str,
        count: int | str = "infinite",
        batch_size: int = 5,
    ) -> List[Wave]:
        """
        Run the infinite agentic loop.
        
        Maps to IndyDevDan's /project:infinite command.
        
        Args:
            spec: Specification file path
            output_dir: Output directory
            count: Number of iterations or "infinite"
            batch_size: Agents per wave
        """
        is_infinite = count == "infinite"
        target_count = float("inf") if is_infinite else int(count)
        
        generated = 0
        
        logger.info(f"🔄 Starting infinite loop: {spec} -> {output_dir}")
        
        while generated < target_count:
            # Compute wave size
            remaining = target_count - generated
            wave_size = min(batch_size, remaining) if not is_infinite else batch_size
            
            # Generate tasks for this wave
            tasks = [
                f"Generate iteration {generated + i + 1} from {spec}"
                for i in range(int(wave_size))
            ]
            
            wave = await self.spawn_agents(tasks)
            
            generated += wave.success_count
            
            # Break if no progress (all failed)
            if wave.success_count == 0:
                logger.warning("⚠️ No agents succeeded, stopping loop")
                break
            
            # Context window check (safety limit)
            if self._current_wave >= 100:
                logger.warning("⚠️ Wave limit reached, stopping infinite loop")
                break
        
        return self.waves
    
    def get_status(self) -> Dict[str, Any]:
        """Get current orchestration status."""
        return {
            "total_waves": len(self.waves),
            "current_wave": self._current_wave,
            "total_agents": sum(len(w.agents) for w in self.waves),
            "completed": sum(w.success_count for w in self.waves),
            "failed": sum(w.failure_count for w in self.waves),
            "waves": [
                {
                    "number": w.number,
                    "agents": len(w.agents),
                    "completed": w.success_count,
                    "is_complete": w.is_complete,
                }
                for w in self.waves
            ],
        }
    
    def reset(self) -> None:
        """Reset the manager state."""
        self.waves.clear()
        self._current_wave = 0
