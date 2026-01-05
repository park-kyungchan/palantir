"""
Orion ODA v3.0 - Hybrid LLM Router & Ollama Client
Intelligent routing between Local LLM and Relay Queue

This module implements the HybridRouter which decides whether to:
- Process locally (Ollama) for simple, low-risk tasks
- Route to Relay Queue for complex or critical tasks

Routing Decision Factors:
1. Critical Keywords: Certain words always trigger Relay (e.g., "delete", "deploy")
2. Complexity Score: Token count, sentence structure, technical terms
3. Explicit Markers: User can force routing with [LOCAL] or [RELAY] prefixes
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Set

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

class RouterConfig(BaseModel):
    """
    Configuration for the HybridRouter.
    
    Can be loaded from YAML/JSON file or environment variables.
    """
    
    # Complexity thresholds
    word_threshold: int = Field(
        default=50,
        description="Word count threshold for complexity routing",
        ge=10,
        le=500
    )
    
    sentence_threshold: int = Field(
        default=5,
        description="Sentence count threshold for complexity routing",
        ge=1,
        le=50
    )
    
    # Critical keywords (always route to RELAY)
    critical_keywords: List[str] = Field(
        default_factory=lambda: [
            # Destructive operations
            "delete",
            "remove",
            "drop",
            "truncate",
            "destroy",
            "wipe",
            "purge",
            # Deployment operations
            "deploy",
            "release",
            "publish",
            "rollback",
            "migrate",
            # Infrastructure
            "production",
            "prod",
            "database",
            "server",
            "cluster",
            "kubernetes",
            "k8s",
            # Security
            "credential",
            "password",
            "secret",
            "token",
            "api_key",
            "apikey",
            # Financial
            "payment",
            "billing",
            "invoice",
            "refund",
        ],
        description="Keywords that always trigger RELAY routing"
    )
    
    # Technical terms (increase complexity score)
    technical_terms: List[str] = Field(
        default_factory=lambda: [
            "api",
            "endpoint",
            "microservice",
            "architecture",
            "integration",
            "authentication",
            "authorization",
            "encryption",
            "scalability",
            "redundancy",
        ],
        description="Technical terms that increase complexity score"
    )
    
    # Weights for complexity calculation
    word_weight: float = Field(default=1.0, ge=0.0, le=10.0)
    sentence_weight: float = Field(default=5.0, ge=0.0, le=20.0)
    technical_term_weight: float = Field(default=3.0, ge=0.0, le=10.0)
    question_weight: float = Field(default=2.0, ge=0.0, le=10.0)
    
    # Ollama settings
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama API base URL"
    )
    ollama_model: str = Field(
        default="llama3.2",
        description="Default Ollama model"
    )
    ollama_timeout: float = Field(
        default=60.0,
        description="Ollama request timeout in seconds",
        ge=5.0,
        le=300.0
    )
    ollama_max_retries: int = Field(
        default=3,
        description="Max retries for Ollama requests",
        ge=0,
        le=10
    )
    
    @classmethod
    def from_file(cls, path: str | Path) -> "RouterConfig":
        """Load configuration from YAML or JSON file."""
        path = Path(path)
        
        if not path.exists():
            logger.warning(f"Config file not found: {path}, using defaults")
            return cls()
        
        content = path.read_text()
        
        if path.suffix in (".yaml", ".yml"):
            try:
                import yaml
                data = yaml.safe_load(content)
            except ImportError:
                logger.error("PyYAML not installed, falling back to defaults")
                return cls()
        elif path.suffix == ".json":
            data = json.loads(content)
        else:
            raise ValueError(f"Unsupported config format: {path.suffix}")
        
        return cls(**data)
    
    def to_file(self, path: str | Path) -> None:
        """Save configuration to JSON file."""
        path = Path(path)
        path.write_text(self.model_dump_json(indent=2))


# =============================================================================
# ROUTING DECISION
# =============================================================================

class RouteTarget(str, Enum):
    """Routing destination."""
    LOCAL = "LOCAL"    # Process with local Ollama
    RELAY = "RELAY"    # Queue for external processing


@dataclass
class RoutingDecision:
    """
    Detailed routing decision with audit trail.
    
    Includes the reasoning for the routing choice,
    useful for debugging and tuning.
    """
    target: RouteTarget
    reason: str
    complexity_score: float
    triggered_keywords: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    @property
    def is_local(self) -> bool:
        return self.target == RouteTarget.LOCAL
    
    @property
    def is_relay(self) -> bool:
        return self.target == RouteTarget.RELAY
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "target": self.target.value,
            "reason": self.reason,
            "complexity_score": self.complexity_score,
            "triggered_keywords": self.triggered_keywords,
            "metrics": self.metrics,
            "timestamp": self.timestamp.isoformat(),
        }


# =============================================================================
# HYBRID ROUTER
# =============================================================================

class HybridRouter:
    """
    Intelligent router for LLM task distribution.
    
    Decides whether to process a task locally (Ollama) or
    route it to the Relay Queue for external processing.
    
    Routing Logic:
    1. Check for explicit markers ([LOCAL], [RELAY])
    2. Check for critical keywords
    3. Calculate complexity score
    4. Compare against thresholds
    
    Usage:
        ```python
        config = RouterConfig.from_file("config/router.yaml")
        router = HybridRouter(config)
        
        decision = router.route("Delete all user data from production")
        # decision.target == RouteTarget.RELAY
        # decision.triggered_keywords == ["delete", "production"]
        
        decision = router.route("What is 2 + 2?")
        # decision.target == RouteTarget.LOCAL
        ```
    """
    
    # Explicit routing markers
    LOCAL_MARKER = "[LOCAL]"
    RELAY_MARKER = "[RELAY]"
    
    def __init__(self, config: RouterConfig | None = None):
        self.config = config or RouterConfig()
        self._keyword_pattern = self._build_keyword_pattern()
    
    def _build_keyword_pattern(self) -> re.Pattern:
        """Build regex pattern for critical keyword detection."""
        # Sort by length descending to match longer keywords first
        keywords = sorted(self.config.critical_keywords, key=len, reverse=True)
        # Escape special regex characters and join with OR
        escaped = [re.escape(kw) for kw in keywords]
        pattern = r"\b(" + "|".join(escaped) + r")\b"
        return re.compile(pattern, re.IGNORECASE)
    
    def _find_critical_keywords(self, text: str) -> List[str]:
        """Find all critical keywords in the text."""
        matches = self._keyword_pattern.findall(text)
        return list(set(match.lower() for match in matches))
    
    def _count_technical_terms(self, text: str) -> int:
        """Count occurrences of technical terms."""
        text_lower = text.lower()
        count = 0
        for term in self.config.technical_terms:
            count += text_lower.count(term.lower())
        return count
    
    def _calculate_complexity(self, text: str) -> tuple[float, Dict[str, Any]]:
        """
        Calculate complexity score for a task description.
        
        Returns:
            Tuple of (score, metrics_dict)
        """
        # Basic metrics
        words = text.split()
        word_count = len(words)
        
        # Sentence count (rough heuristic)
        sentences = re.split(r"[.!?]+", text)
        sentence_count = len([s for s in sentences if s.strip()])
        
        # Technical terms
        technical_count = self._count_technical_terms(text)
        
        # Questions (often indicate complex queries)
        question_count = text.count("?")
        
        # Calculate weighted score
        score = (
            word_count * self.config.word_weight +
            sentence_count * self.config.sentence_weight +
            technical_count * self.config.technical_term_weight +
            question_count * self.config.question_weight
        )
        
        metrics = {
            "word_count": word_count,
            "sentence_count": sentence_count,
            "technical_count": technical_count,
            "question_count": question_count,
            "threshold": self._get_complexity_threshold(),
        }
        
        return score, metrics
    
    def _get_complexity_threshold(self) -> float:
        """Calculate the complexity threshold from config."""
        return (
            self.config.word_threshold * self.config.word_weight +
            self.config.sentence_threshold * self.config.sentence_weight
        )
    
    def route(self, task_description: str) -> RoutingDecision:
        """
        Determine routing for a task.
        
        Args:
            task_description: The task/prompt to be processed
        
        Returns:
            RoutingDecision with target, reason, and metrics
        """
        text = task_description.strip()
        
        # 1. Check explicit markers
        if text.upper().startswith(self.LOCAL_MARKER):
            return RoutingDecision(
                target=RouteTarget.LOCAL,
                reason="Explicit LOCAL marker",
                complexity_score=0,
                metrics={"explicit_marker": True}
            )
        
        if text.upper().startswith(self.RELAY_MARKER):
            return RoutingDecision(
                target=RouteTarget.RELAY,
                reason="Explicit RELAY marker",
                complexity_score=0,
                metrics={"explicit_marker": True}
            )
        
        # 2. Check critical keywords
        triggered_keywords = self._find_critical_keywords(text)
        if triggered_keywords:
            return RoutingDecision(
                target=RouteTarget.RELAY,
                reason=f"Critical keywords detected: {triggered_keywords}",
                complexity_score=float("inf"),  # Infinite = always RELAY
                triggered_keywords=triggered_keywords,
                metrics={"keyword_triggered": True}
            )
        
        # 3. Calculate complexity
        score, metrics = self._calculate_complexity(text)
        threshold = self._get_complexity_threshold()
        
        if score >= threshold:
            return RoutingDecision(
                target=RouteTarget.RELAY,
                reason=f"Complexity score ({score:.1f}) exceeds threshold ({threshold:.1f})",
                complexity_score=score,
                metrics=metrics
            )
        
        return RoutingDecision(
            target=RouteTarget.LOCAL,
            reason=f"Complexity score ({score:.1f}) below threshold ({threshold:.1f})",
            complexity_score=score,
            metrics=metrics
        )
    
    def route_simple(self, task_description: str) -> Literal["LOCAL", "RELAY"]:
        """
        Simple routing that returns just the target string.
        
        For backward compatibility with existing code.
        """
        return self.route(task_description).target.value


# =============================================================================
# OLLAMA CLIENT
# =============================================================================

@dataclass
class OllamaResponse:
    """Response from Ollama API."""
    content: str
    model: str
    done: bool
    total_duration: Optional[int] = None  # nanoseconds
    eval_count: Optional[int] = None  # tokens generated
    
    @property
    def duration_seconds(self) -> float:
        """Get duration in seconds."""
        if self.total_duration:
            return self.total_duration / 1_000_000_000
        return 0.0


class OllamaClient:
    """
    Async client for Ollama API.
    
    Handles connection, retries, and response parsing.
    
    Usage:
        ```python
        config = RouterConfig()
        client = OllamaClient(config)
        
        response = await client.generate("What is 2 + 2?")
        print(response.content)  # "4"
        ```
    """
    
    def __init__(self, config: RouterConfig | None = None):
        self.config = config or RouterConfig()
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.config.ollama_base_url,
                timeout=self.config.ollama_timeout,
            )
        return self._client
    
    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
    
    async def generate(
        self,
        prompt: str,
        model: str | None = None,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> OllamaResponse:
        """
        Generate a completion from Ollama.
        
        Args:
            prompt: The user prompt
            model: Model to use (defaults to config)
            system: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        
        Returns:
            OllamaResponse with generated content
        
        Raises:
            httpx.HTTPError: On connection/request errors after retries
        """
        client = await self._get_client()
        model = model or self.config.ollama_model
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        
        if system:
            payload["system"] = system
        
        last_error: Optional[Exception] = None
        
        for attempt in range(self.config.ollama_max_retries + 1):
            try:
                response = await client.post("/api/generate", json=payload)
                response.raise_for_status()
                data = response.json()
                
                return OllamaResponse(
                    content=data.get("response", ""),
                    model=data.get("model", model),
                    done=data.get("done", True),
                    total_duration=data.get("total_duration"),
                    eval_count=data.get("eval_count"),
                )
            
            except httpx.HTTPError as e:
                last_error = e
                logger.warning(
                    f"Ollama request failed (attempt {attempt + 1}/"
                    f"{self.config.ollama_max_retries + 1}): {e}"
                )
                
                if attempt < self.config.ollama_max_retries:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        raise last_error or RuntimeError("Ollama request failed")
    
    async def health_check(self) -> bool:
        """Check if Ollama is available."""
        try:
            client = await self._get_client()
            response = await client.get("/api/tags")
            return response.status_code == 200
        except Exception:
            return False
    
    async def list_models(self) -> List[str]:
        """List available models."""
        try:
            client = await self._get_client()
            response = await client.get("/api/tags")
            response.raise_for_status()
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []


# =============================================================================
# UNIFIED INTERFACE
# =============================================================================

class HybridLLMService:
    """
    Unified service combining Router and Ollama Client.
    
    Provides a single interface for LLM operations with
    automatic routing decisions.
    
    Usage:
        ```python
        service = HybridLLMService()
        
        # Simple query - processed locally
        result = await service.process("What is 2 + 2?")
        # result.routing.target == LOCAL
        # result.response.content == "4"
        
        # Complex query - routed to relay
        result = await service.process("Deploy the checkout service to production")
        # result.routing.target == RELAY
        # result.queued == True
        ```
    """
    
    def __init__(self, config: RouterConfig | None = None):
        self.config = config or RouterConfig()
        self.router = HybridRouter(self.config)
        self.ollama = OllamaClient(self.config)
    
    async def close(self) -> None:
        """Close all connections."""
        await self.ollama.close()
    
    async def process(
        self,
        prompt: str,
        force_local: bool = False,
        force_relay: bool = False,
    ) -> Dict[str, Any]:
        """
        Process a prompt with automatic routing.
        
        Args:
            prompt: The prompt to process
            force_local: Force local processing (skip routing)
            force_relay: Force relay routing (skip routing)
        
        Returns:
            Dict with routing decision and response/queue status
        """
        # Determine routing
        if force_local:
            decision = RoutingDecision(
                target=RouteTarget.LOCAL,
                reason="Forced local processing",
                complexity_score=0,
            )
        elif force_relay:
            decision = RoutingDecision(
                target=RouteTarget.RELAY,
                reason="Forced relay routing",
                complexity_score=0,
            )
        else:
            decision = self.router.route(prompt)
        
        result = {
            "routing": decision.to_dict(),
            "prompt": prompt,
        }
        
        if decision.is_local:
            # Process locally with Ollama
            try:
                response = await self.ollama.generate(prompt)
                result["response"] = {
                    "content": response.content,
                    "model": response.model,
                    "duration_seconds": response.duration_seconds,
                }
                result["success"] = True
            except Exception as e:
                result["error"] = str(e)
                result["success"] = False
        else:
            # Queue for relay processing
            # This would integrate with RelayQueue
            result["queued"] = True
            result["queue_reason"] = decision.reason
            result["success"] = True
        
        return result


# =============================================================================
# CONFIGURATION FILE TEMPLATE
# =============================================================================

DEFAULT_CONFIG_TEMPLATE = """
# Orion ODA v3.0 - Router Configuration
# Save as: config/router.yaml or config/router.json

# Complexity Thresholds
word_threshold: 50
sentence_threshold: 5

# Critical Keywords (always route to RELAY)
critical_keywords:
  # Destructive operations
  - delete
  - remove
  - drop
  - truncate
  - destroy
  # Deployment operations
  - deploy
  - release
  - publish
  - rollback
  - migrate
  # Infrastructure
  - production
  - prod
  - database
  - server
  - kubernetes
  # Security
  - credential
  - password
  - secret
  - token
  - api_key

# Technical Terms (increase complexity score)
technical_terms:
  - api
  - endpoint
  - microservice
  - architecture
  - integration

# Complexity Weights
word_weight: 1.0
sentence_weight: 5.0
technical_term_weight: 3.0
question_weight: 2.0

# Ollama Settings
ollama_base_url: "http://localhost:11434"
ollama_model: "llama3.2"
ollama_timeout: 60.0
ollama_max_retries: 3
"""
