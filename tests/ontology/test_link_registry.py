"""
Orion ODA V4.0 - LinkType Registry Tests
=========================================
Unit tests for LinkType registration, introspection, and export.

Tests cover:
- LinkTypeMetadata validation
- OntologyRegistry link type operations
- LinkIntrospector graph queries
- export_links_json() output format

Schema Version: 4.0.0
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import List

import pytest

from lib.oda.ontology.registry import (
    OntologyRegistry,
    register_link_type,
    get_registry,
)
from lib.oda.ontology.types.link_types import (
    CascadePolicy,
    LinkDirection,
    LinkTypeConstraints,
    LinkTypeMetadata,
)
from lib.oda.ontology.introspection.links import (
    LinkIntrospector,
    LinkAnalysis,
    LinkPath,
    PathType,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def empty_registry() -> OntologyRegistry:
    """Create a fresh empty registry for isolated tests."""
    return OntologyRegistry()


@pytest.fixture
def sample_link_types() -> List[LinkTypeMetadata]:
    """Create sample LinkTypeMetadata for testing."""
    return [
        LinkTypeMetadata(
            link_type_id="task_has_subtask",
            source_type="Task",
            target_type="Task",
            cardinality="1:N",
            direction=LinkDirection.DIRECTED,
            on_delete=CascadePolicy.CASCADE,
            description="Parent task to subtask relationship",
        ),
        LinkTypeMetadata(
            link_type_id="task_depends_on_task",
            source_type="Task",
            target_type="Task",
            cardinality="N:N",
            direction=LinkDirection.DIRECTED,
            on_delete=CascadePolicy.RESTRICT,
            backing_table_name="task_dependencies",
            description="Task dependency relationship",
        ),
        LinkTypeMetadata(
            link_type_id="task_assigned_to_user",
            source_type="Task",
            target_type="User",
            cardinality="N:1",
            direction=LinkDirection.DIRECTED,
            on_delete=CascadePolicy.SET_NULL,
            description="Task assignee relationship",
        ),
        LinkTypeMetadata(
            link_type_id="user_owns_project",
            source_type="User",
            target_type="Project",
            cardinality="1:N",
            direction=LinkDirection.DIRECTED,
            on_delete=CascadePolicy.CASCADE,
            description="User project ownership",
        ),
        LinkTypeMetadata(
            link_type_id="project_contains_task",
            source_type="Project",
            target_type="Task",
            cardinality="1:N",
            direction=LinkDirection.DIRECTED,
            on_delete=CascadePolicy.CASCADE,
            description="Project task containment",
        ),
    ]


@pytest.fixture
def populated_registry(
    empty_registry: OntologyRegistry,
    sample_link_types: List[LinkTypeMetadata],
) -> OntologyRegistry:
    """Create a registry populated with sample link types."""
    for lt in sample_link_types:
        empty_registry.register_link_type(lt)
    return empty_registry


# =============================================================================
# LINK TYPE METADATA TESTS
# =============================================================================

class TestLinkTypeMetadata:
    """Tests for LinkTypeMetadata validation."""

    def test_create_basic_link_type(self):
        """Test creating a basic LinkTypeMetadata."""
        lt = LinkTypeMetadata(
            link_type_id="test_link",
            source_type="ObjectA",
            target_type="ObjectB",
            cardinality="1:N",
        )
        assert lt.link_type_id == "test_link"
        assert lt.source_type == "ObjectA"
        assert lt.target_type == "ObjectB"
        assert lt.cardinality == "1:N"
        assert lt.is_many_to_many is False

    def test_many_to_many_detection(self):
        """Test N:N cardinality detection."""
        lt = LinkTypeMetadata(
            link_type_id="nn_link",
            source_type="A",
            target_type="B",
            cardinality="N:N",
            backing_table_name="a_b_links",
        )
        assert lt.is_many_to_many is True

    def test_link_type_with_constraints(self):
        """Test LinkTypeMetadata with constraints."""
        constraints = LinkTypeConstraints(
            min_cardinality=1,
            max_cardinality=10,
        )
        lt = LinkTypeMetadata(
            link_type_id="constrained_link",
            source_type="A",
            target_type="B",
            cardinality="1:N",
            constraints=constraints,
        )
        assert lt.constraints.min_cardinality == 1
        assert lt.constraints.max_cardinality == 10

    def test_link_type_with_cascade_policies(self):
        """Test LinkTypeMetadata with cascade policies."""
        lt = LinkTypeMetadata(
            link_type_id="cascade_link",
            source_type="Parent",
            target_type="Child",
            cardinality="1:N",
            on_source_delete=CascadePolicy.CASCADE,
            on_source_update=CascadePolicy.NO_ACTION,
        )
        # on_delete and on_update are aliases for on_source_delete/on_source_update
        assert lt.on_delete == CascadePolicy.CASCADE
        assert lt.on_update == CascadePolicy.NO_ACTION
        assert lt.on_source_delete == CascadePolicy.CASCADE
        assert lt.on_source_update == CascadePolicy.NO_ACTION

    def test_link_type_with_reverse(self):
        """Test LinkTypeMetadata with reverse link."""
        lt = LinkTypeMetadata(
            link_type_id="parent_has_child",
            source_type="Parent",
            target_type="Child",
            cardinality="1:N",
            reverse_link_id="child_belongs_to_parent",
        )
        assert lt.reverse_link_id == "child_belongs_to_parent"


# =============================================================================
# ONTOLOGY REGISTRY TESTS
# =============================================================================

class TestOntologyRegistryLinks:
    """Tests for OntologyRegistry link operations."""

    def test_register_link_type(self, empty_registry: OntologyRegistry):
        """Test registering a link type."""
        lt = LinkTypeMetadata(
            link_type_id="test_link",
            source_type="A",
            target_type="B",
            cardinality="1:N",
        )
        empty_registry.register_link_type(lt)
        assert "test_link" in empty_registry.list_link_types()

    def test_register_duplicate_raises_error(self, empty_registry: OntologyRegistry):
        """Test that registering duplicate link type raises error."""
        lt = LinkTypeMetadata(
            link_type_id="duplicate_link",
            source_type="A",
            target_type="B",
            cardinality="1:N",
        )
        empty_registry.register_link_type(lt)

        with pytest.raises(ValueError, match="already registered"):
            empty_registry.register_link_type(lt)

    def test_get_link_type(self, populated_registry: OntologyRegistry):
        """Test retrieving a registered link type."""
        lt = populated_registry.get_link_type("task_has_subtask")
        assert lt is not None
        assert lt.source_type == "Task"
        assert lt.target_type == "Task"

    def test_get_nonexistent_link_type(self, empty_registry: OntologyRegistry):
        """Test retrieving non-existent link type returns None."""
        lt = empty_registry.get_link_type("nonexistent")
        assert lt is None

    def test_list_link_types(self, populated_registry: OntologyRegistry):
        """Test listing all registered link types."""
        link_types = populated_registry.list_link_types()
        assert len(link_types) == 5
        assert "task_has_subtask" in link_types
        assert "task_depends_on_task" in link_types

    def test_list_link_types_for_object(self, populated_registry: OntologyRegistry):
        """Test finding link types for a specific object."""
        task_links = populated_registry.list_link_types_for_object("Task")
        # Task is involved in 4 links
        assert len(task_links) == 4

    def test_get_outgoing_links(self, populated_registry: OntologyRegistry):
        """Test getting outgoing links for an object type."""
        outgoing = populated_registry.get_outgoing_links("Task")
        link_ids = [lt.link_type_id for lt in outgoing]
        assert "task_has_subtask" in link_ids
        assert "task_depends_on_task" in link_ids
        assert "task_assigned_to_user" in link_ids

    def test_get_incoming_links(self, populated_registry: OntologyRegistry):
        """Test getting incoming links for an object type."""
        incoming = populated_registry.get_incoming_links("Task")
        link_ids = [lt.link_type_id for lt in incoming]
        assert "task_has_subtask" in link_ids  # Self-referential
        assert "project_contains_task" in link_ids


# =============================================================================
# EXPORT TESTS
# =============================================================================

class TestExportLinksJson:
    """Tests for export_links_json functionality."""

    def test_export_links_json(self, populated_registry: OntologyRegistry):
        """Test exporting link types to JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "links.json"
            populated_registry.export_links_json(path)

            assert path.exists()
            data = json.loads(path.read_text())

            # Check structure
            assert "$schema" in data
            assert "version" in data
            assert "generated_at" in data
            assert "link_types" in data
            assert "statistics" in data
            assert "object_graph" in data

    def test_export_link_types_content(self, populated_registry: OntologyRegistry):
        """Test content of exported link types."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "links.json"
            populated_registry.export_links_json(path)

            data = json.loads(path.read_text())
            link_types = data["link_types"]

            assert "task_has_subtask" in link_types
            task_subtask = link_types["task_has_subtask"]
            assert task_subtask["source_type"] == "Task"
            assert task_subtask["target_type"] == "Task"
            assert task_subtask["cardinality"] == "1:N"
            assert task_subtask["on_delete"] == "cascade"

    def test_export_statistics(self, populated_registry: OntologyRegistry):
        """Test statistics in exported JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "links.json"
            populated_registry.export_links_json(path)

            data = json.loads(path.read_text())
            stats = data["statistics"]

            assert stats["total"] == 5
            assert "by_cardinality" in stats
            assert stats["by_cardinality"]["1:N"] == 3
            assert stats["by_cardinality"]["N:N"] == 1
            assert stats["by_cardinality"]["N:1"] == 1

    def test_export_object_graph(self, populated_registry: OntologyRegistry):
        """Test object graph in exported JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "links.json"
            populated_registry.export_links_json(path)

            data = json.loads(path.read_text())
            graph = data["object_graph"]

            assert "Task" in graph
            assert "outgoing" in graph["Task"]
            assert "incoming" in graph["Task"]


# =============================================================================
# LINK INTROSPECTOR TESTS
# =============================================================================

class TestLinkIntrospector:
    """Tests for LinkIntrospector functionality."""

    def test_get_node(self, populated_registry: OntologyRegistry):
        """Test getting a graph node."""
        introspector = LinkIntrospector(populated_registry)
        node = introspector.get_node("Task")

        assert node is not None
        assert node.object_type == "Task"
        assert len(node.outgoing_links) > 0
        assert len(node.incoming_links) > 0

    def test_get_neighbors(self, populated_registry: OntologyRegistry):
        """Test getting neighboring object types."""
        introspector = LinkIntrospector(populated_registry)
        neighbors = introspector.get_neighbors("Task")

        assert "User" in neighbors
        assert "Project" in neighbors

    def test_get_neighbors_directional(self, populated_registry: OntologyRegistry):
        """Test getting neighbors with direction filter."""
        introspector = LinkIntrospector(populated_registry)

        outgoing = introspector.get_neighbors("User", direction="outgoing")
        assert "Project" in outgoing

        incoming = introspector.get_neighbors("User", direction="incoming")
        assert "Task" in incoming

    def test_find_paths(self, populated_registry: OntologyRegistry):
        """Test finding paths between object types."""
        introspector = LinkIntrospector(populated_registry)
        paths = introspector.find_paths("User", "Task", max_depth=3)

        assert len(paths) > 0
        # User -> Project -> Task path should exist
        indirect_paths = [p for p in paths if p.length == 2]
        assert len(indirect_paths) > 0

    def test_get_reachable_objects(self, populated_registry: OntologyRegistry):
        """Test getting all reachable objects."""
        introspector = LinkIntrospector(populated_registry)
        reachable = introspector.get_reachable_objects("User")

        assert "Project" in reachable
        assert "Task" in reachable
        assert reachable["Project"] == 1  # Direct
        assert reachable["Task"] == 2  # Indirect (User -> Project -> Task)

    def test_detect_cycles(self, populated_registry: OntologyRegistry):
        """Test cycle detection in link graph."""
        introspector = LinkIntrospector(populated_registry)
        cycles = introspector.detect_cycles()

        # Task -> Task (self-referential) creates cycles
        assert len(cycles) > 0

    def test_has_cycle(self, populated_registry: OntologyRegistry):
        """Test has_cycle convenience method."""
        introspector = LinkIntrospector(populated_registry)
        assert introspector.has_cycle() is True

    def test_analyze_cascade_impact(self, populated_registry: OntologyRegistry):
        """Test cascade impact analysis."""
        introspector = LinkIntrospector(populated_registry)
        impact = introspector.analyze_cascade_impact("Task")

        # Task has CASCADE to subtasks
        assert "Task" in impact
        assert any("CASCADE" in i for i in impact["Task"])

    def test_get_cascade_chain(self, populated_registry: OntologyRegistry):
        """Test getting cascade chain."""
        introspector = LinkIntrospector(populated_registry)
        chain = introspector.get_cascade_chain("User")

        assert "User" in chain
        assert "Project" in chain  # User -> Project (CASCADE)
        assert "Task" in chain  # Project -> Task (CASCADE)

    def test_analyze(self, populated_registry: OntologyRegistry):
        """Test comprehensive analysis."""
        introspector = LinkIntrospector(populated_registry)
        analysis = introspector.analyze()

        assert isinstance(analysis, LinkAnalysis)
        assert analysis.total_objects > 0
        assert analysis.total_links == 5
        assert len(analysis.cycles) > 0  # Has self-referential Task links

    def test_to_graphviz(self, populated_registry: OntologyRegistry):
        """Test Graphviz export."""
        introspector = LinkIntrospector(populated_registry)
        dot = introspector.to_graphviz()

        assert "digraph OntologyLinks" in dot
        assert "Task" in dot
        assert "User" in dot
        assert "->" in dot

    def test_to_mermaid(self, populated_registry: OntologyRegistry):
        """Test Mermaid export."""
        introspector = LinkIntrospector(populated_registry)
        mermaid = introspector.to_mermaid()

        assert "graph LR" in mermaid
        assert "-->" in mermaid


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestLinkRegistryIntegration:
    """Integration tests for link registry functionality."""

    def test_full_workflow(self):
        """Test complete workflow from registration to introspection."""
        # Create fresh registry
        registry = OntologyRegistry()

        # Register link types
        lt1 = LinkTypeMetadata(
            link_type_id="a_to_b",
            source_type="A",
            target_type="B",
            cardinality="1:N",
            on_delete=CascadePolicy.CASCADE,
        )
        lt2 = LinkTypeMetadata(
            link_type_id="b_to_c",
            source_type="B",
            target_type="C",
            cardinality="1:N",
            on_delete=CascadePolicy.CASCADE,
        )
        lt3 = LinkTypeMetadata(
            link_type_id="c_to_a",
            source_type="C",
            target_type="A",
            cardinality="N:1",
            on_delete=CascadePolicy.RESTRICT,
        )

        registry.register_link_type(lt1)
        registry.register_link_type(lt2)
        registry.register_link_type(lt3)

        # Verify registration
        assert len(registry.list_link_types()) == 3

        # Create introspector
        introspector = LinkIntrospector(registry)

        # Find paths
        paths = introspector.find_paths("A", "C")
        assert len(paths) > 0

        # Get reachable
        reachable = introspector.get_reachable_objects("A")
        assert "B" in reachable
        assert "C" in reachable

        # Check cycles (A -> B -> C -> A)
        assert introspector.has_cycle() is True

        # Export
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test_links.json"
            registry.export_links_json(path)
            assert path.exists()

            data = json.loads(path.read_text())
            assert data["statistics"]["total"] == 3
