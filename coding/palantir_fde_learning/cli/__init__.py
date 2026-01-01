# cli/__init__.py
"""
CLI Module for Palantir FDE Learning System

This module provides the command-line interface for interacting with
the learning system. Built with Click for robust CLI patterns.

Architecture Notes:
- CLI is an adapter layer (outermost in Clean Architecture)
- Commands delegate to Application layer (ScopingEngine, services)
- Follows Palantir's developer tooling patterns (osdk CLI)

Available Commands:
- fde-learn profile: Manage learner profiles
- fde-learn recommend: Get concept recommendations
- fde-learn stats: View learning statistics
- fde-learn kb: Knowledge base operations
"""

from palantir_fde_learning.cli.main import app

__all__ = ["app"]
