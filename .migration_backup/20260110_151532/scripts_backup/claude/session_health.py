"""
Orion ODA - Session Health Monitor
===================================
Boris Cherny Pattern 12: Session Discard

"If the agent gets stuck in a loop or goes down a wrong path,
I just kill it and start fresh - cheaper than trying to fix context."

This module provides:
- Dead-end detection (repetitive patterns)
- Session health metrics
- Early termination criteria
- Cost/benefit analysis for session continuation

Usage:
    monitor = SessionHealthMonitor()
    health = await monitor.evaluate()
    if health.should_terminate:
        # Recommend session discard
"""

import hashlib
import json
import logging
import os
from collections import Counter, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class HealthMetrics:
    """Session health metrics."""
    repetition_score: float = 0.0  # 0-1, higher = more repetitive
    progress_score: float = 1.0    # 0-1, higher = more progress
    error_rate: float = 0.0        # 0-1, higher = more errors
    context_usage: float = 0.0     # 0-1, percentage of context used
    tool_diversity: float = 1.0    # 0-1, higher = more varied tool usage
    time_efficiency: float = 1.0   # 0-1, higher = more efficient

    @property
    def overall_health(self) -> float:
        """Calculate overall health score (0-1, higher = healthier)."""
        weights = {
            'repetition': -0.25,    # Repetition is bad
            'progress': 0.30,       # Progress is good
            'error_rate': -0.20,    # Errors are bad
            'context_usage': -0.10, # High context usage is concerning
            'tool_diversity': 0.10, # Diversity is slightly good
            'time_efficiency': 0.05 # Efficiency is slightly good
        }

        score = (
            (1 - self.repetition_score) * abs(weights['repetition']) +
            self.progress_score * weights['progress'] +
            (1 - self.error_rate) * abs(weights['error_rate']) +
            (1 - self.context_usage) * abs(weights['context_usage']) +
            self.tool_diversity * weights['tool_diversity'] +
            self.time_efficiency * weights['time_efficiency']
        )

        return max(0.0, min(1.0, score))

    @property
    def status(self) -> str:
        """Get health status label."""
        health = self.overall_health
        if health >= 0.8:
            return "HEALTHY"
        elif health >= 0.6:
            return "FAIR"
        elif health >= 0.4:
            return "DEGRADED"
        elif health >= 0.2:
            return "CRITICAL"
        else:
            return "TERMINAL"


@dataclass
class HealthReport:
    """Session health evaluation report."""
    session_id: str
    timestamp: str
    metrics: HealthMetrics
    should_terminate: bool = False
    termination_reason: Optional[str] = None
    recommendations: List[str] = field(default_factory=list)
    dead_end_detected: bool = False
    loop_detected: bool = False
    estimated_remaining_value: float = 1.0  # 0-1, expected value from continuing

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "metrics": {
                "repetition_score": self.metrics.repetition_score,
                "progress_score": self.metrics.progress_score,
                "error_rate": self.metrics.error_rate,
                "context_usage": self.metrics.context_usage,
                "tool_diversity": self.metrics.tool_diversity,
                "time_efficiency": self.metrics.time_efficiency,
                "overall_health": self.metrics.overall_health,
                "status": self.metrics.status,
            },
            "should_terminate": self.should_terminate,
            "termination_reason": self.termination_reason,
            "recommendations": self.recommendations,
            "dead_end_detected": self.dead_end_detected,
            "loop_detected": self.loop_detected,
            "estimated_remaining_value": self.estimated_remaining_value,
        }


@dataclass
class ToolCall:
    """Record of a tool call for pattern analysis."""
    tool_name: str
    timestamp: str
    success: bool
    input_hash: str  # Hash of input for repetition detection
    duration_ms: int = 0


class SessionHealthMonitor:
    """
    Monitors session health and detects dead-ends.

    Boris Cherny Pattern: "Don't throw good money after bad -
    if a session is going nowhere, start fresh."

    Detection Mechanisms:
    1. Repetition Detection: Same tool calls with same inputs
    2. Loop Detection: Cyclic patterns in tool sequence
    3. Error Rate: Increasing failure rate
    4. Progress Stall: No todo completions over time
    5. Context Exhaustion: High context usage with low progress
    """

    # Termination thresholds
    REPETITION_THRESHOLD = 0.7     # 70% repetition triggers concern
    ERROR_RATE_THRESHOLD = 0.5     # 50% error rate is critical
    CONTEXT_CRITICAL = 0.9         # 90% context usage is critical
    LOOP_MIN_LENGTH = 3            # Minimum loop length to detect
    LOOP_REPETITIONS = 2           # Number of repetitions to confirm loop
    STALL_MINUTES = 10             # Minutes without progress = stall

    def __init__(
        self,
        workspace_root: Optional[str] = None,
        session_id: Optional[str] = None,
        max_history: int = 100,
    ):
        self.workspace_root = Path(
            workspace_root or os.getenv("ORION_WORKSPACE_ROOT", "/home/palantir")
        )
        self.session_id = session_id or os.getenv("CLAUDE_SESSION_ID", "unknown")
        self.max_history = max_history

        # Tool call history for pattern detection
        self.tool_history: Deque[ToolCall] = deque(maxlen=max_history)

        # Progress tracking
        self.todos_completed: int = 0
        self.todos_total: int = 0
        self.last_progress_time: Optional[datetime] = None

        # Error tracking
        self.error_count: int = 0
        self.success_count: int = 0

        # Session timing
        self.session_start: datetime = datetime.utcnow()

        # State paths
        self.agent_tmp = self.workspace_root / "park-kyungchan/palantir/.agent/tmp"
        self.health_file = self.agent_tmp / f"health_{self.session_id}.json"

    def record_tool_call(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        success: bool,
        duration_ms: int = 0,
    ) -> None:
        """Record a tool call for health analysis."""
        # Create input hash for repetition detection
        input_str = json.dumps(tool_input, sort_keys=True)
        input_hash = hashlib.md5(input_str.encode()).hexdigest()[:8]

        call = ToolCall(
            tool_name=tool_name,
            timestamp=datetime.utcnow().isoformat(),
            success=success,
            input_hash=input_hash,
            duration_ms=duration_ms,
        )

        self.tool_history.append(call)

        if success:
            self.success_count += 1
        else:
            self.error_count += 1

    def record_progress(self, completed: int, total: int) -> None:
        """Record todo progress."""
        if completed > self.todos_completed:
            self.last_progress_time = datetime.utcnow()

        self.todos_completed = completed
        self.todos_total = total

    def _calculate_repetition_score(self) -> float:
        """Calculate how repetitive the tool calls are."""
        if len(self.tool_history) < 5:
            return 0.0

        # Create signatures for each call
        signatures = [
            f"{call.tool_name}:{call.input_hash}"
            for call in self.tool_history
        ]

        # Count duplicates
        counter = Counter(signatures)
        unique_count = len(counter)
        total_count = len(signatures)

        # Repetition score: 1 - (unique / total)
        if total_count == 0:
            return 0.0

        return 1 - (unique_count / total_count)

    def _detect_loop(self) -> Tuple[bool, Optional[List[str]]]:
        """Detect cyclic patterns in tool sequence."""
        if len(self.tool_history) < self.LOOP_MIN_LENGTH * self.LOOP_REPETITIONS:
            return False, None

        # Get recent tool names
        recent_tools = [call.tool_name for call in self.tool_history]

        # Check for repeating patterns of various lengths
        for pattern_length in range(self.LOOP_MIN_LENGTH, len(recent_tools) // self.LOOP_REPETITIONS + 1):
            # Get the potential pattern from the most recent calls
            pattern = recent_tools[-pattern_length:]

            # Check if this pattern repeats before it
            repetitions = 0
            for i in range(self.LOOP_REPETITIONS):
                start = -(pattern_length * (i + 1))
                end = -(pattern_length * i) if i > 0 else None

                if end:
                    segment = recent_tools[start:end]
                else:
                    segment = recent_tools[start:]

                if segment == pattern:
                    repetitions += 1

            if repetitions >= self.LOOP_REPETITIONS:
                return True, pattern

        return False, None

    def _calculate_progress_score(self) -> float:
        """Calculate progress score based on todo completion."""
        if self.todos_total == 0:
            return 0.5  # Neutral if no todos

        completion_rate = self.todos_completed / self.todos_total

        # Factor in time since last progress
        if self.last_progress_time:
            minutes_since_progress = (datetime.utcnow() - self.last_progress_time).total_seconds() / 60
            if minutes_since_progress > self.STALL_MINUTES:
                # Decay progress score if stalled
                decay = min(0.5, minutes_since_progress / (self.STALL_MINUTES * 2))
                completion_rate *= (1 - decay)

        return completion_rate

    def _calculate_error_rate(self) -> float:
        """Calculate the error rate of tool calls."""
        total = self.success_count + self.error_count
        if total == 0:
            return 0.0
        return self.error_count / total

    def _calculate_tool_diversity(self) -> float:
        """Calculate how varied the tool usage is."""
        if len(self.tool_history) < 3:
            return 1.0

        tool_names = [call.tool_name for call in self.tool_history]
        unique_tools = len(set(tool_names))

        # Normalize against expected diversity (assuming ~10 common tools)
        expected_diversity = min(10, len(tool_names))
        return min(1.0, unique_tools / expected_diversity)

    def _calculate_time_efficiency(self) -> float:
        """Calculate time efficiency based on progress vs time."""
        session_duration = (datetime.utcnow() - self.session_start).total_seconds() / 60

        if session_duration < 1:
            return 1.0  # Too early to measure

        if self.todos_total == 0:
            return 0.5  # Neutral

        # Expected: 1 todo per 2-5 minutes
        expected_completions = session_duration / 3
        actual_completions = self.todos_completed

        if expected_completions == 0:
            return 1.0

        efficiency = min(1.0, actual_completions / expected_completions)
        return efficiency

    def _estimate_context_usage(self) -> float:
        """Estimate context usage (approximation based on tool calls)."""
        # Rough estimate: each tool call uses ~1-2% context
        # This is a heuristic - actual context usage isn't directly accessible
        estimated_usage = len(self.tool_history) * 0.015
        return min(1.0, estimated_usage)

    def _detect_dead_end(self, metrics: HealthMetrics, loop_detected: bool) -> bool:
        """Determine if session is in a dead-end state."""
        # Dead-end conditions:
        # 1. High repetition + low progress
        if metrics.repetition_score > 0.6 and metrics.progress_score < 0.3:
            return True

        # 2. Loop detected with no recent progress
        if loop_detected and metrics.progress_score < 0.5:
            return True

        # 3. Very high error rate
        if metrics.error_rate > 0.7:
            return True

        # 4. High context usage with minimal progress
        if metrics.context_usage > 0.8 and metrics.progress_score < 0.2:
            return True

        return False

    def _should_terminate(
        self,
        metrics: HealthMetrics,
        dead_end: bool,
        loop_detected: bool,
    ) -> Tuple[bool, Optional[str]]:
        """Determine if session should be terminated."""
        # Boris Cherny Rule: "Don't throw good money after bad"

        # Critical: Terminal health status
        if metrics.status == "TERMINAL":
            return True, "Session health is terminal - recommend fresh start"

        # Dead-end detected
        if dead_end:
            return True, "Dead-end detected - session is not making progress"

        # Confirmed loop with high repetition
        if loop_detected and metrics.repetition_score > self.REPETITION_THRESHOLD:
            return True, "Repetitive loop detected - recommend breaking cycle"

        # Critical error rate
        if metrics.error_rate > self.ERROR_RATE_THRESHOLD:
            return True, f"Error rate too high ({metrics.error_rate:.0%})"

        # Context exhaustion with low progress
        if metrics.context_usage > self.CONTEXT_CRITICAL and metrics.progress_score < 0.3:
            return True, "Context nearly exhausted with insufficient progress"

        return False, None

    def _generate_recommendations(
        self,
        metrics: HealthMetrics,
        dead_end: bool,
        loop_detected: bool,
    ) -> List[str]:
        """Generate recommendations for improving session health."""
        recommendations = []

        if metrics.repetition_score > 0.5:
            recommendations.append("Try different approaches - current strategy shows repetition")

        if loop_detected:
            recommendations.append("Break the loop: try a completely different tool or approach")

        if metrics.error_rate > 0.3:
            recommendations.append("Many tool calls failing - check environment or inputs")

        if metrics.progress_score < 0.3:
            recommendations.append("Progress stalled - consider breaking task into smaller steps")

        if metrics.context_usage > 0.7:
            recommendations.append("Context usage high - consider /compact or fresh session")

        if metrics.time_efficiency < 0.3:
            recommendations.append("Time efficiency low - focus on high-impact actions")

        if dead_end:
            recommendations.append("RECOMMENDATION: Start fresh session with clearer goals")

        if not recommendations:
            recommendations.append("Session health is good - continue current approach")

        return recommendations

    async def evaluate(self) -> HealthReport:
        """
        Evaluate session health and generate report.

        Returns:
            HealthReport with metrics, recommendations, and termination advice
        """
        # Load any persisted state
        await self._load_state()

        # Calculate metrics
        metrics = HealthMetrics(
            repetition_score=self._calculate_repetition_score(),
            progress_score=self._calculate_progress_score(),
            error_rate=self._calculate_error_rate(),
            context_usage=self._estimate_context_usage(),
            tool_diversity=self._calculate_tool_diversity(),
            time_efficiency=self._calculate_time_efficiency(),
        )

        # Detect patterns
        loop_detected, loop_pattern = self._detect_loop()
        dead_end = self._detect_dead_end(metrics, loop_detected)

        # Determine termination
        should_terminate, termination_reason = self._should_terminate(
            metrics, dead_end, loop_detected
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            metrics, dead_end, loop_detected
        )

        # Calculate remaining value estimate
        remaining_value = metrics.overall_health * (1 - metrics.context_usage)

        report = HealthReport(
            session_id=self.session_id,
            timestamp=datetime.utcnow().isoformat(),
            metrics=metrics,
            should_terminate=should_terminate,
            termination_reason=termination_reason,
            recommendations=recommendations,
            dead_end_detected=dead_end,
            loop_detected=loop_detected,
            estimated_remaining_value=remaining_value,
        )

        # Persist state
        await self._save_state(report)

        # Log critical findings
        if should_terminate:
            logger.warning(f"Session {self.session_id}: Termination recommended - {termination_reason}")
        elif dead_end:
            logger.warning(f"Session {self.session_id}: Dead-end detected")
        elif loop_detected:
            logger.info(f"Session {self.session_id}: Loop detected - {loop_pattern}")

        return report

    async def _load_state(self) -> None:
        """Load persisted health state."""
        if not self.health_file.exists():
            return

        try:
            data = json.loads(self.health_file.read_text())

            # Restore counters
            self.todos_completed = data.get("todos_completed", 0)
            self.todos_total = data.get("todos_total", 0)
            self.error_count = data.get("error_count", 0)
            self.success_count = data.get("success_count", 0)

            # Restore timing
            if data.get("last_progress_time"):
                self.last_progress_time = datetime.fromisoformat(data["last_progress_time"])
            if data.get("session_start"):
                self.session_start = datetime.fromisoformat(data["session_start"])

        except Exception as e:
            logger.debug(f"Failed to load health state: {e}")

    async def _save_state(self, report: HealthReport) -> None:
        """Save health state for persistence."""
        try:
            self.agent_tmp.mkdir(parents=True, exist_ok=True)

            state = {
                "session_id": self.session_id,
                "todos_completed": self.todos_completed,
                "todos_total": self.todos_total,
                "error_count": self.error_count,
                "success_count": self.success_count,
                "last_progress_time": self.last_progress_time.isoformat() if self.last_progress_time else None,
                "session_start": self.session_start.isoformat(),
                "last_report": report.to_dict(),
            }

            self.health_file.write_text(json.dumps(state, indent=2))

        except Exception as e:
            logger.debug(f"Failed to save health state: {e}")


# Singleton instance
_monitor: Optional[SessionHealthMonitor] = None


def get_health_monitor() -> SessionHealthMonitor:
    """Get or create the singleton health monitor."""
    global _monitor
    if _monitor is None:
        _monitor = SessionHealthMonitor()
    return _monitor


# CLI interface
async def main():
    """CLI entry point for health check."""
    import sys

    monitor = get_health_monitor()
    report = await monitor.evaluate()

    print(f"\n{'='*50}")
    print(f"Session Health Report: {report.session_id}")
    print(f"{'='*50}")
    print(f"Status: {report.metrics.status}")
    print(f"Overall Health: {report.metrics.overall_health:.1%}")
    print()
    print("Metrics:")
    print(f"  - Repetition: {report.metrics.repetition_score:.1%}")
    print(f"  - Progress: {report.metrics.progress_score:.1%}")
    print(f"  - Error Rate: {report.metrics.error_rate:.1%}")
    print(f"  - Context Usage: {report.metrics.context_usage:.1%}")
    print(f"  - Tool Diversity: {report.metrics.tool_diversity:.1%}")
    print()
    print("Findings:")
    print(f"  - Dead-end Detected: {report.dead_end_detected}")
    print(f"  - Loop Detected: {report.loop_detected}")
    print(f"  - Remaining Value: {report.estimated_remaining_value:.1%}")
    print()
    print("Recommendations:")
    for rec in report.recommendations:
        print(f"  - {rec}")
    print()

    if report.should_terminate:
        print(f"TERMINATION RECOMMENDED: {report.termination_reason}")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
