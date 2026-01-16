"""
Claude Code CLI Integration Module

This module provides integration between Claude Code CLI native capabilities
and the Orion ODA (Ontology-Driven Architecture) framework.

Key Components:
- todo_sync: Synchronize TodoWrite with ODA Task objects
- evidence_tracker: Track file reads and line references for anti-hallucination
- protocol_runner: Execute 3-Stage Protocols with Claude Code tools

LLM-Agnostic: These utilities work with any LLM backend.
"""

from lib.oda.claude.todo_sync import TodoTaskSync, TodoStatus
from lib.oda.claude.evidence_tracker import EvidenceTracker, EvidenceContext
from lib.oda.claude.protocol_runner import ClaudeProtocolRunner

__all__ = [
    "TodoTaskSync",
    "TodoStatus",
    "EvidenceTracker",
    "EvidenceContext",
    "ClaudeProtocolRunner",
]
