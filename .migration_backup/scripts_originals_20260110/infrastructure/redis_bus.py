"""
Orion ODA V3 - Redis Event Bus
===============================
Distributed event bus using Redis pub/sub.

P-03: Replace in-memory EventBus with Redis for scalability.

Features:
    - Publish/Subscribe pattern
    - Topic-based routing (orion:events:{type})
    - Graceful fallback to in-memory when Redis unavailable
    - Async operations with aioredis

Usage:
    bus = RedisEventBus()
    await bus.connect()
    await bus.publish("proposal.created", {"id": "..."})
    await bus.subscribe("proposal.*", callback)
"""

import asyncio
import json
import logging
from typing import Any, Callable, Dict, Optional, Set

logger = logging.getLogger(__name__)

# Redis is optional - graceful fallback
try:
    import redis.asyncio as aioredis
    HAS_REDIS = True
except ImportError:
    aioredis = None
    HAS_REDIS = False
    logger.debug("aioredis not installed. Using in-memory fallback.")


class RedisEventBus:
    """
    Distributed event bus using Redis pub/sub.
    
    Maps to P-03: Distributed EventBus requirement.
    
    Channel naming convention:
        orion:events:{event_type}
        
    Example channels:
        orion:events:proposal.created
        orion:events:action.executed
        orion:events:*
    
    Usage:
        bus = RedisEventBus()
        await bus.connect()
        
        # Publish
        await bus.publish("proposal.created", {"id": "abc"})
        
        # Subscribe
        async def handler(event):
            print(f"Received: {event}")
        
        await bus.subscribe("proposal.*", handler)
    """
    
    CHANNEL_PREFIX = "orion:events:"
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
    ):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        
        self._redis: Optional[Any] = None
        self._pubsub: Optional[Any] = None
        self._subscriptions: Dict[str, Set[Callable]] = {}
        self._subscription_task: Optional[asyncio.Task] = None
        self._connected = False
        
        # In-memory fallback for when Redis is unavailable
        self._inmemory_handlers: Dict[str, Set[Callable]] = {}
    
    @property
    def is_connected(self) -> bool:
        return self._connected
    
    async def connect(self) -> bool:
        """
        Connect to Redis.
        
        Returns:
            True if connected, False if using in-memory fallback
        """
        if not HAS_REDIS:
            logger.warning("Redis not available, using in-memory fallback")
            return False
        
        try:
            self._redis = aioredis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,
            )
            
            # Test connection
            await self._redis.ping()
            
            self._pubsub = self._redis.pubsub()
            self._connected = True
            
            logger.info(f"Connected to Redis at {self.host}:{self.port}")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Using in-memory fallback.")
            self._connected = False
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._subscription_task:
            self._subscription_task.cancel()
            try:
                await self._subscription_task
            except asyncio.CancelledError:
                pass
        
        if self._pubsub:
            await self._pubsub.close()
        
        if self._redis:
            await self._redis.close()
        
        self._connected = False
        logger.info("Disconnected from Redis")
    
    async def publish(
        self,
        event_type: str,
        payload: Dict[str, Any],
    ) -> int:
        """
        Publish an event.
        
        Args:
            event_type: Event type (e.g., "proposal.created")
            payload: Event data
            
        Returns:
            Number of subscribers that received the message
        """
        message = json.dumps({
            "type": event_type,
            "payload": payload,
        })
        
        if self._connected and self._redis:
            channel = f"{self.CHANNEL_PREFIX}{event_type}"
            subscribers = await self._redis.publish(channel, message)
            logger.debug(f"Published to {channel}: {subscribers} subscribers")
            return subscribers
        else:
            # In-memory fallback
            return await self._publish_inmemory(event_type, payload)
    
    async def _publish_inmemory(
        self,
        event_type: str,
        payload: Dict[str, Any],
    ) -> int:
        """Publish using in-memory handlers."""
        count = 0
        
        for pattern, handlers in self._inmemory_handlers.items():
            if self._matches_pattern(event_type, pattern):
                for handler in handlers:
                    try:
                        await handler({"type": event_type, "payload": payload})
                        count += 1
                    except Exception as e:
                        logger.error(f"Handler error: {e}")
        
        return count
    
    async def subscribe(
        self,
        pattern: str,
        handler: Callable,
    ) -> None:
        """
        Subscribe to events matching a pattern.
        
        Args:
            pattern: Event pattern (e.g., "proposal.*", "action.executed")
            handler: Async function to handle events
        """
        if pattern not in self._subscriptions:
            self._subscriptions[pattern] = set()
        self._subscriptions[pattern].add(handler)
        
        if self._connected and self._pubsub:
            channel_pattern = f"{self.CHANNEL_PREFIX}{pattern}"
            
            if "*" in pattern:
                await self._pubsub.psubscribe(channel_pattern)
            else:
                await self._pubsub.subscribe(channel_pattern)
            
            # Start listener if not running
            if not self._subscription_task or self._subscription_task.done():
                self._subscription_task = asyncio.create_task(
                    self._listen_loop()
                )
            
            logger.info(f"Subscribed to: {channel_pattern}")
        else:
            # In-memory fallback
            if pattern not in self._inmemory_handlers:
                self._inmemory_handlers[pattern] = set()
            self._inmemory_handlers[pattern].add(handler)
    
    async def unsubscribe(self, pattern: str, handler: Callable) -> None:
        """Unsubscribe a handler from a pattern."""
        if pattern in self._subscriptions:
            self._subscriptions[pattern].discard(handler)
        
        if pattern in self._inmemory_handlers:
            self._inmemory_handlers[pattern].discard(handler)
    
    async def _listen_loop(self) -> None:
        """Background task to listen for messages."""
        try:
            async for message in self._pubsub.listen():
                if message["type"] in ("message", "pmessage"):
                    await self._dispatch_message(message)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Listen loop error: {e}")
    
    async def _dispatch_message(self, message: Dict) -> None:
        """Dispatch a received message to handlers."""
        try:
            data = json.loads(message["data"])
            event_type = data.get("type", "")
            
            for pattern, handlers in self._subscriptions.items():
                if self._matches_pattern(event_type, pattern):
                    for handler in handlers:
                        try:
                            await handler(data)
                        except Exception as e:
                            logger.error(f"Handler error for {event_type}: {e}")
                            
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON in message: {message}")
    
    @staticmethod
    def _matches_pattern(event_type: str, pattern: str) -> bool:
        """Check if event_type matches pattern."""
        if pattern == "*":
            return True
        
        if "*" not in pattern:
            return event_type == pattern
        
        # Simple wildcard matching
        parts = pattern.split("*")
        if len(parts) == 2:
            prefix, suffix = parts
            return event_type.startswith(prefix) and event_type.endswith(suffix)
        
        return False


# Convenience functions
_global_bus: Optional[RedisEventBus] = None


async def get_redis_bus() -> RedisEventBus:
    """Get or create the global Redis event bus."""
    global _global_bus
    
    if _global_bus is None:
        _global_bus = RedisEventBus()
        await _global_bus.connect()
    
    return _global_bus


async def publish_event(event_type: str, payload: Dict[str, Any]) -> int:
    """Convenience function to publish an event."""
    bus = await get_redis_bus()
    return await bus.publish(event_type, payload)


async def subscribe_to_events(pattern: str, handler: Callable) -> None:
    """Convenience function to subscribe to events."""
    bus = await get_redis_bus()
    await bus.subscribe(pattern, handler)
