"""
Orion ODA v3.0 - Protocol Enforcement Decorators
==================================================
Decorators for enforcing 3-Stage Protocol compliance.

Usage:
    @require_protocol(AuditProtocol)
    class DeepAuditAction(ActionType):
        # This action requires AuditProtocol to pass before execution
        pass
    
    @require_protocol(PlanningProtocol, policy=ProtocolPolicy.WARN)
    class CreateProposalAction(ActionType):
        # This action warns but proceeds if protocol fails
        pass
"""

from __future__ import annotations

import functools
import logging
from typing import TYPE_CHECKING, Any, Callable, Optional, Type, TypeVar

if TYPE_CHECKING:
    from lib.oda.ontology.protocols.base import (
        ThreeStageProtocol,
        ProtocolPolicy,
        ProtocolResult,
        ProtocolContext,
    )

logger = logging.getLogger(__name__)

T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])


# =============================================================================
# PROTOCOL REGISTRY
# =============================================================================

class ProtocolRegistry:
    """
    Registry tracking protocol requirements for actions.
    
    Used by GovernanceEngine to check protocol compliance.
    """
    _registry: dict[str, tuple[Type["ThreeStageProtocol"], "ProtocolPolicy"]] = {}
    _results: dict[str, "ProtocolResult"] = {}
    
    @classmethod
    def register(
        cls,
        action_name: str,
        protocol_class: Type["ThreeStageProtocol"],
        policy: "ProtocolPolicy"
    ) -> None:
        """Register a protocol requirement for an action."""
        cls._registry[action_name] = (protocol_class, policy)
        logger.debug(f"Registered {protocol_class.__name__} for {action_name} ({policy.value})")
    
    @classmethod
    def get_requirement(
        cls, 
        action_name: str
    ) -> Optional[tuple[Type["ThreeStageProtocol"], "ProtocolPolicy"]]:
        """Get protocol requirement for an action."""
        return cls._registry.get(action_name)
    
    @classmethod
    def store_result(cls, action_name: str, result: "ProtocolResult") -> None:
        """Store a protocol execution result."""
        cls._results[action_name] = result
    
    @classmethod
    def get_result(cls, action_name: str) -> Optional["ProtocolResult"]:
        """Get stored protocol result for an action."""
        return cls._results.get(action_name)
    
    @classmethod
    def clear_result(cls, action_name: str) -> None:
        """Clear stored result (for re-execution)."""
        cls._results.pop(action_name, None)
    
    @classmethod
    def is_compliant(cls, action_name: str) -> tuple[bool, Optional[str]]:
        """
        Check if an action is protocol-compliant.
        
        Returns:
            Tuple of (is_compliant, reason)
        """
        requirement = cls.get_requirement(action_name)
        
        if not requirement:
            # No protocol required
            return True, None
        
        protocol_class, policy = requirement
        result = cls.get_result(action_name)
        
        if not result:
            if policy.value == "block":
                return False, f"Protocol {protocol_class.__name__} required but not executed"
            elif policy.value == "warn":
                logger.warning(f"Protocol {protocol_class.__name__} not executed for {action_name}")
                return True, f"Warning: Protocol {protocol_class.__name__} skipped"
            else:  # skip
                return True, None
        
        if not result.passed:
            if policy.value == "block":
                return False, f"Protocol {protocol_class.__name__} failed: {result.total_findings} findings"
            elif policy.value == "warn":
                logger.warning(f"Protocol {protocol_class.__name__} failed for {action_name}")
                return True, f"Warning: Protocol {protocol_class.__name__} failed"
            else:
                return True, None
        
        return True, None


# =============================================================================
# DECORATORS
# =============================================================================

def require_protocol(
    protocol_class: Type["ThreeStageProtocol"],
    policy: Optional["ProtocolPolicy"] = None
) -> Callable[[Type[T]], Type[T]]:
    """
    Class decorator to require 3-Stage Protocol compliance.
    
    Usage:
        @require_protocol(AuditProtocol)
        class DeepAuditAction(ActionType):
            pass
    
    Args:
        protocol_class: The protocol that must pass
        policy: Enforcement policy (default: BLOCK)
    
    Returns:
        Decorated class with protocol requirement registered
    """
    from lib.oda.ontology.protocols.base import ProtocolPolicy as PP
    
    actual_policy = policy or PP.BLOCK
    
    def decorator(cls: Type[T]) -> Type[T]:
        # Get action name from class
        action_name = getattr(cls, "api_name", cls.__name__)
        
        # Register requirement
        ProtocolRegistry.register(action_name, protocol_class, actual_policy)
        
        # Store metadata on class
        cls._protocol_class = protocol_class  # type: ignore
        cls._protocol_policy = actual_policy  # type: ignore
        
        return cls
    
    return decorator


def stage_a(func: F) -> F:
    """
    Mark a method as Stage A implementation.
    
    Usage:
        class MyProtocol(ThreeStageProtocol):
            @stage_a
            async def stage_a(self, context):
                ...
    """
    func._protocol_stage = "A_SCAN"  # type: ignore
    return func


def stage_b(func: F) -> F:
    """
    Mark a method as Stage B implementation.
    """
    func._protocol_stage = "B_TRACE"  # type: ignore
    return func


def stage_c(func: F) -> F:
    """
    Mark a method as Stage C implementation.
    """
    func._protocol_stage = "C_VERIFY"  # type: ignore
    return func


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

async def run_protocol_for_action(
    action_name: str,
    context: "ProtocolContext"
) -> Optional["ProtocolResult"]:
    """
    Run the required protocol for an action.
    
    Args:
        action_name: Name of the action
        context: Protocol execution context
    
    Returns:
        ProtocolResult if protocol was required and executed, None otherwise
    """
    requirement = ProtocolRegistry.get_requirement(action_name)
    
    if not requirement:
        return None
    
    protocol_class, _ = requirement
    protocol = protocol_class()
    
    result = await protocol.execute(context)
    ProtocolRegistry.store_result(action_name, result)
    
    return result


def get_protocol_status(action_name: str) -> dict[str, Any]:
    """
    Get protocol compliance status for an action.
    
    Returns dict with:
        - required: bool
        - protocol_name: str or None
        - policy: str or None
        - executed: bool
        - passed: bool or None
        - findings_count: int or None
    """
    requirement = ProtocolRegistry.get_requirement(action_name)
    result = ProtocolRegistry.get_result(action_name)
    
    if not requirement:
        return {
            "required": False,
            "protocol_name": None,
            "policy": None,
            "executed": False,
            "passed": None,
            "findings_count": None,
        }
    
    protocol_class, policy = requirement
    
    return {
        "required": True,
        "protocol_name": protocol_class.__name__,
        "policy": policy.value,
        "executed": result is not None,
        "passed": result.passed if result else None,
        "findings_count": result.total_findings if result else None,
    }
