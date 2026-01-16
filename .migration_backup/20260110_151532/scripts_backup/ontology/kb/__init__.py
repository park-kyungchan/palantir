"""
Knowledge base indexing and matching utilities.

These helpers provide a lightweight, offline way to map:
- user prompt terms
- detected code patterns (from the tutoring engine)

to relevant markdown documents in `coding/knowledge_bases/`.
"""

from scripts.ontology.kb.index import load_or_build_kb_index
from scripts.ontology.kb.match import match_kbs

__all__ = ["load_or_build_kb_index", "match_kbs"]

