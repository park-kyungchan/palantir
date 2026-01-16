"""
Ollama client + hybrid router utilities (test-facing).

This module exists to provide a lightweight, local-first "Hybrid Router" that can
route prompts to LOCAL vs RELAY execution and an async Ollama client compatible
with the E2E tests in `tests/e2e/`.
"""

from __future__ import annotations

import json
import re
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel, Field


class RouteTarget(str, Enum):
    """Where to execute a prompt."""

    LOCAL = "LOCAL"
    RELAY = "RELAY"


class RoutingDecision(BaseModel):
    """Result of routing a prompt."""

    target: RouteTarget
    reason: str
    complexity_score: int = 0
    triggered_keywords: List[str] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)


class RouterConfig(BaseModel):
    """Configuration for HybridRouter and OllamaClient."""

    word_threshold: int = Field(default=50, ge=10)
    sentence_threshold: int = Field(default=5, ge=1)
    critical_keywords: List[str] = Field(
        default_factory=lambda: ["delete", "deploy", "production", "database"]
    )
    technical_terms: List[str] = Field(default_factory=lambda: ["api", "microservice"])

    ollama_base_url: str = Field(default="http://localhost:11434")
    ollama_model: str = Field(default="llama3.2")
    ollama_timeout: float = Field(default=10.0, gt=0.0)
    ollama_max_retries: int = Field(default=1, ge=0)

    @classmethod
    def from_file(cls, path: Path) -> "RouterConfig":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.model_validate(data)

    def to_file(self, path: Path) -> None:
        Path(path).write_text(self.model_dump_json(indent=2), encoding="utf-8")


class HybridRouter:
    """
    Heuristic router that decides whether a prompt should run locally.

    Rules (in order):
    1) Explicit markers: `[LOCAL]` / `[RELAY]`
    2) Critical keywords -> RELAY
    3) Complexity (word/sentence thresholds + technical-term weighting)
    """

    def __init__(self, config: RouterConfig | None = None) -> None:
        self.config = config or RouterConfig()

    def route(self, prompt: str) -> RoutingDecision:
        prompt_str = (prompt or "").strip()

        explicit = self._parse_explicit_marker(prompt_str)
        if explicit is not None:
            stripped, target = explicit
            return RoutingDecision(
                target=target,
                reason=f"Explicit marker: {target.value}",
                complexity_score=0,
                triggered_keywords=[],
                metrics=self._metrics(stripped, 0),
            )

        lowered = prompt_str.lower()
        triggered = [
            kw for kw in self.config.critical_keywords if kw.lower() in lowered
        ]
        if triggered:
            score = self._complexity_score(prompt_str)
            return RoutingDecision(
                target=RouteTarget.RELAY,
                reason=f"Critical keyword(s) detected: {', '.join(triggered)}",
                complexity_score=score,
                triggered_keywords=triggered,
                metrics=self._metrics(prompt_str, score),
            )

        score = self._complexity_score(prompt_str)
        threshold = self.config.word_threshold
        if score >= threshold:
            return RoutingDecision(
                target=RouteTarget.RELAY,
                reason=f"Complexity score exceeded threshold ({score} >= {threshold})",
                complexity_score=score,
                triggered_keywords=[],
                metrics=self._metrics(prompt_str, score),
            )

        return RoutingDecision(
            target=RouteTarget.LOCAL,
            reason="Within local complexity threshold",
            complexity_score=score,
            triggered_keywords=[],
            metrics=self._metrics(prompt_str, score),
        )

    @staticmethod
    def _parse_explicit_marker(prompt: str) -> Optional[tuple[str, RouteTarget]]:
        upper = prompt.upper()
        if upper.startswith("[LOCAL]"):
            return prompt[len("[LOCAL]") :].lstrip(), RouteTarget.LOCAL
        if upper.startswith("[RELAY]"):
            return prompt[len("[RELAY]") :].lstrip(), RouteTarget.RELAY
        return None

    def _complexity_score(self, prompt: str) -> int:
        metrics = self._basic_metrics(prompt)
        score = metrics["word_count"]

        lowered = prompt.lower()
        tech_hits = sum(1 for t in self.config.technical_terms if t.lower() in lowered)
        score += tech_hits * 10

        # Sentence penalty nudges multi-sentence prompts toward relay.
        if metrics["sentence_count"] > self.config.sentence_threshold:
            score += (metrics["sentence_count"] - self.config.sentence_threshold) * 5

        return score

    @staticmethod
    def _basic_metrics(prompt: str) -> Dict[str, int]:
        words = re.findall(r"\b\w+\b", prompt)
        sentence_count = max(1, len([s for s in re.split(r"[.!?]+", prompt) if s.strip()]))
        return {"word_count": len(words), "sentence_count": sentence_count}

    def _metrics(self, prompt: str, score: int) -> Dict[str, Any]:
        base = self._basic_metrics(prompt)
        base["threshold"] = self.config.word_threshold
        base["complexity_score"] = score
        return base


class OllamaResponse(BaseModel):
    """Normalized response from Ollama."""

    content: str
    model: str
    done: bool = True
    duration_seconds: Optional[float] = None
    raw: Dict[str, Any] = Field(default_factory=dict)


class OllamaClient:
    """Async client for a local Ollama server."""

    def __init__(self, config: RouterConfig | None = None) -> None:
        self.config = config or RouterConfig()
        self._client = httpx.AsyncClient(
            base_url=self.config.ollama_base_url,
            timeout=self.config.ollama_timeout,
        )

    async def health_check(self) -> bool:
        try:
            res = await self._client.get("/api/tags")
            return res.status_code == 200
        except httpx.HTTPError:
            return False

    async def generate(self, prompt: str) -> OllamaResponse:
        payload = {"model": self.config.ollama_model, "prompt": prompt, "stream": False}
        last_error: Exception | None = None

        for _ in range(max(1, self.config.ollama_max_retries + 1)):
            try:
                res = await self._client.post("/api/generate", json=payload)
                res.raise_for_status()
                data = res.json()
                duration_ns = data.get("total_duration")
                duration_seconds = (
                    float(duration_ns) / 1_000_000_000 if duration_ns is not None else None
                )
                return OllamaResponse(
                    content=str(data.get("response", "")),
                    model=str(data.get("model", self.config.ollama_model)),
                    done=bool(data.get("done", True)),
                    duration_seconds=duration_seconds,
                    raw=data if isinstance(data, dict) else {},
                )
            except Exception as e:  # noqa: BLE001 - boundary layer retries
                last_error = e

        raise RuntimeError("Ollama generate failed") from last_error

    async def close(self) -> None:
        await self._client.aclose()


class HybridLLMService:
    """
    Convenience wrapper combining HybridRouter + OllamaClient.
    """

    def __init__(self, config: RouterConfig | None = None) -> None:
        self.config = config or RouterConfig()
        self.router = HybridRouter(self.config)
        self.ollama = OllamaClient(self.config)

    async def generate(self, prompt: str) -> OllamaResponse:
        decision = self.router.route(prompt)
        if decision.target == RouteTarget.LOCAL:
            return OllamaResponse(
                content="",
                model="local",
                done=True,
                duration_seconds=0.0,
                raw={"routing_decision": decision.model_dump()},
            )
        return await self.ollama.generate(prompt)

    async def close(self) -> None:
        await self.ollama.close()

