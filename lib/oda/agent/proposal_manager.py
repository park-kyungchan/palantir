"""
ODA v3.0 - Proposal Manager (LLM-Agnostic)
=========================================

This module provides a provider-neutral import path for Proposal creation from
structured execution outputs.

Historically, the implementation lived under `lib.oda.claude.*` as part of the
Claude Code integration layer. The underlying code is LLM-agnostic and is
re-exported here so Claude/Gemini/Codex clients can share the same interface.
"""

from __future__ import annotations

from lib.oda.claude.proposal_manager import (  # noqa: F401
    ApprovalMode,
    FileCreation,
    FileDeletion,
    FileModification,
    ProposalManager,
    SubagentOutput,
)

__all__ = [
    "ApprovalMode",
    "FileCreation",
    "FileDeletion",
    "FileModification",
    "ProposalManager",
    "SubagentOutput",
]

