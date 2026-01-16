"""
Foundry-mimic Ontology Building Submodule.

Goal: Provide an LLM-independent, Foundry-inspired way to define and validate:
- Object types / link types / interfaces
- Action types / functions
- Permission checks / dynamic security (as policy specs)
- Schema changes + schema migration plans
- Proposal-gated application of ontology changes

This package is intentionally isolated from the core ODA runtime so that
overlaps/conflicts can be managed as a separate submodule and integrated via
well-defined adapters and ActionTypes.
"""

from .models import (
    ActionTypeSpec,
    FunctionTypeSpec,
    InterfaceTypeSpec,
    LinkTypeSpec,
    ObjectTypeSpec,
    OntologyChangeSet,
    OntologySpec,
)

from .service import (
    OntologySpecStore,
    apply_change_set,
    load_ontology_spec,
    save_ontology_spec,
    validate_change_set,
    validate_ontology_spec,
)

__all__ = [
    "ActionTypeSpec",
    "FunctionTypeSpec",
    "InterfaceTypeSpec",
    "LinkTypeSpec",
    "ObjectTypeSpec",
    "OntologyChangeSet",
    "OntologySpec",
    "OntologySpecStore",
    "apply_change_set",
    "load_ontology_spec",
    "save_ontology_spec",
    "validate_change_set",
    "validate_ontology_spec",
]

