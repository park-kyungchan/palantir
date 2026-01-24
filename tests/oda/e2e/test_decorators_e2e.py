from __future__ import annotations

import pytest

from lib.oda.ontology.decorators import (
    ComputedPropertyMixin,
    InterfaceImplementationError,
    SharedPropertyConflictError,
    computed_property,
    implements_interface,
    invalidate_computed,
    require_interface,
    require_shared_property,
    uses_property,
    uses_shared_property,
)
from lib.oda.ontology.ontology_types import OntologyObject
from lib.oda.ontology.registry import register_interface
from lib.oda.ontology.types.interface_types import InterfaceDefinition, MethodSpec, PropertySpec


def test_computed_property_caches_and_invalidates_on_dependency_change() -> None:
    class Order(ComputedPropertyMixin, OntologyObject):
        quantity: int
        unit_price: float

        @computed_property(depends_on=["quantity", "unit_price"])
        def subtotal(self) -> float:
            return self.quantity * self.unit_price

    order = Order(quantity=2, unit_price=5.0)

    # Initial compute + cache
    assert order.subtotal == 10.0
    assert order.get_computed_metadata()["subtotal"]["is_cached"] is True

    # Dependency change invalidates cache and recomputes
    order.quantity = 3
    assert order.subtotal == 15.0

    # Explicit invalidation works
    invalidate_computed(order, "subtotal")
    assert order.subtotal == 15.0


def test_interface_decorator_validates_and_require_interface_enforces() -> None:
    interface_id = "IE2EDocument"

    register_interface(
        InterfaceDefinition(
            interface_id=interface_id,
            description="E2E test interface",
            required_properties=[PropertySpec(name="title", type_hint="str")],
            required_methods=[MethodSpec(name="render", signature="(self) -> str")],
        )
    )

    with pytest.raises(InterfaceImplementationError):
        @implements_interface(interface_id)
        class BadDocument(OntologyObject):
            title: str

    @implements_interface(interface_id)
    class Document(OntologyObject):
        title: str

        def render(self) -> str:
            return self.title

    @require_interface(interface_id)
    def process(doc: Document) -> str:
        return doc.render()

    assert process(Document(title="hello")) == "hello"
    with pytest.raises(TypeError):
        process(object())  # type: ignore[arg-type]


def test_shared_property_decorator_creates_pydantic_field_and_default_factory() -> None:
    with pytest.raises(SharedPropertyConflictError):
        @uses_shared_property("created_at")
        class Conflicting(OntologyObject):
            title: str

    @uses_shared_property("tags")
    class TaggedDocument(OntologyObject):
        title: str

    assert "tags" in TaggedDocument.model_fields
    assert uses_property(TaggedDocument, "tags") is True

    doc1 = TaggedDocument(title="a")
    doc2 = TaggedDocument(title="b")
    assert doc1.tags == []
    assert doc2.tags == []

    doc1.tags.append("x")
    assert doc1.tags == ["x"]
    assert doc2.tags == []
    assert doc1.tags is not doc2.tags

    @require_shared_property("tags")
    def needs_tags(obj: object) -> str:
        return "ok"

    assert needs_tags(doc1) == "ok"

    class Plain(OntologyObject):
        title: str

    with pytest.raises(TypeError):
        needs_tags(Plain(title="nope"))

