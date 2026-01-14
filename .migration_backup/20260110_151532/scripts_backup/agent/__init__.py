"""
Orion ODA v3.0 - Agent Infrastructure
=====================================

This module provides standardized entry points and protocols for LLM agents
to interact with the Orion Ontology-Driven Architecture.

Components:
- executor: AgentExecutor for running actions
- protocols: Standardized execution protocols
- validators: Input validation utilities
"""

from scripts.agent.executor import AgentExecutor
from scripts.agent.protocols import ExecutionProtocol, TaskResult

__all__ = ["AgentExecutor", "ExecutionProtocol", "TaskResult"]
