"""
Orion ODA (Ontology-Driven Architecture) Package
=================================================
Version: 4.0
License: MIT
Namespace: lib.oda

This package provides the core ODA framework including:
- ontology: Core ontology types, actions, and storage
- semantic: Embedding and vector store integration
- pai: Personal AI infrastructure (traits, skills, hooks)
- claude: Claude Code integration handlers
- agent: Agent orchestration
- transaction: Transaction management

Usage:
    from lib.oda import __version__
    from lib.oda.ontology import Plan, Job, Action
"""

__version__ = "4.0.0"
__author__ = "Orion Team"

__all__ = [
    "__version__",
    "__author__",
]
