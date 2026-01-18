"""
Orion ODA V4.0 - Link Introspector
===================================
Runtime introspection utility for LinkType relationships.

Palantir Pattern:
- Link introspection enables graph traversal queries
- Path finding between object types
- Cycle detection for referential integrity
- Impact analysis for cascade operations

This module provides:
- LinkIntrospector: Main introspection utility
- LinkGraphNode: Graph representation of object types
- LinkPath: Path between object types
- LinkAnalysis: Analysis results

Schema Version: 4.0.0
"""

from __future__ import annotations

import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from lib.oda.ontology.types.link_types import (
    CascadePolicy,
    LinkDirection,
    LinkTypeMetadata,
)

logger = logging.getLogger(__name__)


class PathType(Enum):
    """Type of path between objects."""
    DIRECT = "direct"
    INDIRECT = "indirect"
    BIDIRECTIONAL = "bidirectional"
    CYCLIC = "cyclic"


@dataclass
class LinkGraphNode:
    """
    Represents an ObjectType in the link graph.

    Attributes:
        object_type: Name of the ObjectType
        outgoing_links: LinkTypes where this object is source
        incoming_links: LinkTypes where this object is target
    """
    object_type: str
    outgoing_links: List[str] = field(default_factory=list)
    incoming_links: List[str] = field(default_factory=list)

    @property
    def degree(self) -> int:
        """Total number of link connections."""
        return len(self.outgoing_links) + len(self.incoming_links)

    @property
    def out_degree(self) -> int:
        """Number of outgoing links."""
        return len(self.outgoing_links)

    @property
    def in_degree(self) -> int:
        """Number of incoming links."""
        return len(self.incoming_links)


@dataclass
class LinkPath:
    """
    Represents a path between two ObjectTypes.

    Attributes:
        source: Starting ObjectType
        target: Ending ObjectType
        path: List of (link_type_id, direction) tuples
        path_type: Type of path (direct, indirect, etc.)
        length: Number of hops
    """
    source: str
    target: str
    path: List[Tuple[str, str]] = field(default_factory=list)
    path_type: PathType = PathType.DIRECT
    length: int = 0

    def __post_init__(self):
        self.length = len(self.path)


@dataclass
class LinkAnalysis:
    """
    Results of link analysis operations.

    Attributes:
        analyzed_at: Timestamp of analysis
        total_objects: Number of ObjectTypes in graph
        total_links: Number of LinkTypes
        cycles: Detected cycles in the graph
        orphaned_links: Links with invalid source/target
        cascade_chains: Longest cascade chains
    """
    total_objects: int = 0
    total_links: int = 0
    cycles: List[List[str]] = field(default_factory=list)
    orphaned_links: List[str] = field(default_factory=list)
    cascade_chains: Dict[str, List[str]] = field(default_factory=dict)
    hub_objects: List[str] = field(default_factory=list)  # High connectivity
    leaf_objects: List[str] = field(default_factory=list)  # Low connectivity


class LinkIntrospector:
    """
    Runtime introspection utility for LinkType relationships.

    Provides graph-based analysis of the ontology link structure.

    Example:
        ```python
        from lib.oda.ontology.registry import get_registry

        introspector = LinkIntrospector(get_registry())

        # Find path between objects
        paths = introspector.find_paths("Task", "Learner")

        # Get all reachable objects
        reachable = introspector.get_reachable_objects("Task", max_depth=3)

        # Analyze cascade impact
        impact = introspector.analyze_cascade_impact("Task")

        # Detect cycles
        cycles = introspector.detect_cycles()
        ```
    """

    def __init__(self, registry: Any):
        """
        Initialize the introspector.

        Args:
            registry: OntologyRegistry instance
        """
        self.registry = registry
        self._graph: Dict[str, LinkGraphNode] = {}
        self._link_types: Dict[str, LinkTypeMetadata] = {}
        self._build_graph()

    def _build_graph(self) -> None:
        """Build the link graph from registry."""
        self._link_types = self.registry.list_link_types()

        # Build nodes
        for link_id, link_type in self._link_types.items():
            # Ensure source node exists
            if link_type.source_type not in self._graph:
                self._graph[link_type.source_type] = LinkGraphNode(
                    object_type=link_type.source_type
                )

            # Ensure target node exists
            if link_type.target_type not in self._graph:
                self._graph[link_type.target_type] = LinkGraphNode(
                    object_type=link_type.target_type
                )

            # Add link references
            self._graph[link_type.source_type].outgoing_links.append(link_id)
            self._graph[link_type.target_type].incoming_links.append(link_id)

    def refresh(self) -> None:
        """Refresh the graph from the registry."""
        self._graph.clear()
        self._link_types.clear()
        self._build_graph()

    # =========================================================================
    # GRAPH QUERIES
    # =========================================================================

    def get_node(self, object_type: str) -> Optional[LinkGraphNode]:
        """Get the graph node for an ObjectType."""
        return self._graph.get(object_type)

    def list_nodes(self) -> List[LinkGraphNode]:
        """List all graph nodes."""
        return list(self._graph.values())

    def get_link_type(self, link_type_id: str) -> Optional[LinkTypeMetadata]:
        """Get a LinkType by ID."""
        return self._link_types.get(link_type_id)

    def get_neighbors(
        self,
        object_type: str,
        direction: Optional[str] = None,
    ) -> List[str]:
        """
        Get neighboring ObjectTypes.

        Args:
            object_type: Source ObjectType
            direction: "outgoing", "incoming", or None for both

        Returns:
            List of connected ObjectType names
        """
        node = self._graph.get(object_type)
        if not node:
            return []

        neighbors = set()

        if direction in (None, "outgoing"):
            for link_id in node.outgoing_links:
                lt = self._link_types.get(link_id)
                if lt:
                    neighbors.add(lt.target_type)

        if direction in (None, "incoming"):
            for link_id in node.incoming_links:
                lt = self._link_types.get(link_id)
                if lt:
                    neighbors.add(lt.source_type)

        return list(neighbors)

    # =========================================================================
    # PATH FINDING
    # =========================================================================

    def find_paths(
        self,
        source: str,
        target: str,
        max_depth: int = 5,
        follow_direction: bool = True,
    ) -> List[LinkPath]:
        """
        Find all paths between two ObjectTypes.

        Args:
            source: Starting ObjectType
            target: Ending ObjectType
            max_depth: Maximum path length
            follow_direction: If True, only follow link direction

        Returns:
            List of LinkPath objects
        """
        if source not in self._graph or target not in self._graph:
            return []

        paths: List[LinkPath] = []
        self._dfs_paths(
            current=source,
            target=target,
            visited=set(),
            current_path=[],
            paths=paths,
            max_depth=max_depth,
            follow_direction=follow_direction,
        )

        return paths

    def _dfs_paths(
        self,
        current: str,
        target: str,
        visited: Set[str],
        current_path: List[Tuple[str, str]],
        paths: List[LinkPath],
        max_depth: int,
        follow_direction: bool,
    ) -> None:
        """DFS helper for path finding."""
        if len(current_path) > max_depth:
            return

        if current == target and current_path:
            path_type = PathType.DIRECT if len(current_path) == 1 else PathType.INDIRECT
            paths.append(LinkPath(
                source=current_path[0][0] if current_path else current,
                target=target,
                path=list(current_path),
                path_type=path_type,
            ))
            return

        if current in visited:
            return

        visited.add(current)
        node = self._graph.get(current)
        if not node:
            visited.remove(current)
            return

        # Follow outgoing links
        for link_id in node.outgoing_links:
            lt = self._link_types.get(link_id)
            if lt:
                current_path.append((link_id, "forward"))
                self._dfs_paths(
                    lt.target_type, target, visited, current_path,
                    paths, max_depth, follow_direction
                )
                current_path.pop()

        # Follow incoming links if not direction-restricted
        if not follow_direction:
            for link_id in node.incoming_links:
                lt = self._link_types.get(link_id)
                if lt:
                    current_path.append((link_id, "reverse"))
                    self._dfs_paths(
                        lt.source_type, target, visited, current_path,
                        paths, max_depth, follow_direction
                    )
                    current_path.pop()

        visited.remove(current)

    def get_reachable_objects(
        self,
        source: str,
        max_depth: int = 10,
        follow_direction: bool = True,
    ) -> Dict[str, int]:
        """
        Get all ObjectTypes reachable from source with distance.

        Args:
            source: Starting ObjectType
            max_depth: Maximum traversal depth
            follow_direction: If True, only follow link direction

        Returns:
            Dict mapping ObjectType to minimum distance
        """
        if source not in self._graph:
            return {}

        distances: Dict[str, int] = {source: 0}
        queue = deque([(source, 0)])

        while queue:
            current, depth = queue.popleft()

            if depth >= max_depth:
                continue

            node = self._graph.get(current)
            if not node:
                continue

            # Check outgoing links
            for link_id in node.outgoing_links:
                lt = self._link_types.get(link_id)
                if lt and lt.target_type not in distances:
                    distances[lt.target_type] = depth + 1
                    queue.append((lt.target_type, depth + 1))

            # Check incoming links if not direction-restricted
            if not follow_direction:
                for link_id in node.incoming_links:
                    lt = self._link_types.get(link_id)
                    if lt and lt.source_type not in distances:
                        distances[lt.source_type] = depth + 1
                        queue.append((lt.source_type, depth + 1))

        return distances

    # =========================================================================
    # CYCLE DETECTION
    # =========================================================================

    def detect_cycles(self) -> List[List[str]]:
        """
        Detect all cycles in the link graph.

        Returns:
            List of cycles, each cycle is a list of ObjectType names
        """
        cycles: List[List[str]] = []
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        path: List[str] = []

        for node in self._graph:
            if node not in visited:
                self._detect_cycle_dfs(node, visited, rec_stack, path, cycles)

        return cycles

    def _detect_cycle_dfs(
        self,
        node: str,
        visited: Set[str],
        rec_stack: Set[str],
        path: List[str],
        cycles: List[List[str]],
    ) -> None:
        """DFS helper for cycle detection."""
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        graph_node = self._graph.get(node)
        if graph_node:
            for link_id in graph_node.outgoing_links:
                lt = self._link_types.get(link_id)
                if not lt:
                    continue

                neighbor = lt.target_type

                if neighbor not in visited:
                    self._detect_cycle_dfs(neighbor, visited, rec_stack, path, cycles)
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)

        path.pop()
        rec_stack.remove(node)

    def has_cycle(self) -> bool:
        """Check if the link graph has any cycles."""
        return len(self.detect_cycles()) > 0

    # =========================================================================
    # CASCADE ANALYSIS
    # =========================================================================

    def analyze_cascade_impact(
        self,
        object_type: str,
        cascade_policy: Optional[CascadePolicy] = None,
    ) -> Dict[str, List[str]]:
        """
        Analyze cascade delete impact for an ObjectType.

        Args:
            object_type: ObjectType to analyze
            cascade_policy: Filter by specific policy

        Returns:
            Dict of affected ObjectTypes to list of paths
        """
        impact: Dict[str, List[str]] = defaultdict(list)

        node = self._graph.get(object_type)
        if not node:
            return impact

        # Check outgoing links (source being deleted)
        for link_id in node.outgoing_links:
            lt = self._link_types.get(link_id)
            if not lt:
                continue

            if cascade_policy and lt.on_delete != cascade_policy:
                continue

            policy = lt.on_delete or CascadePolicy.RESTRICT
            if policy == CascadePolicy.CASCADE:
                impact[lt.target_type].append(f"CASCADE via {link_id}")
            elif policy == CascadePolicy.SET_NULL:
                impact[lt.target_type].append(f"SET_NULL via {link_id}")
            elif policy == CascadePolicy.RESTRICT:
                impact[lt.target_type].append(f"BLOCKED by {link_id}")

        # Check incoming links (target being deleted)
        for link_id in node.incoming_links:
            lt = self._link_types.get(link_id)
            if not lt:
                continue

            if cascade_policy and lt.on_delete != cascade_policy:
                continue

            policy = lt.on_delete or CascadePolicy.RESTRICT
            if policy == CascadePolicy.CASCADE:
                impact[lt.source_type].append(f"ORPHANED via {link_id}")

        return dict(impact)

    def get_cascade_chain(
        self,
        object_type: str,
        max_depth: int = 10,
    ) -> List[str]:
        """
        Get the full cascade chain for an ObjectType.

        Args:
            object_type: Starting ObjectType
            max_depth: Maximum chain length

        Returns:
            Ordered list of ObjectTypes in cascade order
        """
        chain: List[str] = []
        visited: Set[str] = set()
        self._build_cascade_chain(object_type, chain, visited, max_depth)
        return chain

    def _build_cascade_chain(
        self,
        object_type: str,
        chain: List[str],
        visited: Set[str],
        max_depth: int,
    ) -> None:
        """Build cascade chain recursively."""
        if object_type in visited or len(chain) >= max_depth:
            return

        visited.add(object_type)
        chain.append(object_type)

        node = self._graph.get(object_type)
        if not node:
            return

        for link_id in node.outgoing_links:
            lt = self._link_types.get(link_id)
            if lt and lt.on_delete == CascadePolicy.CASCADE:
                self._build_cascade_chain(lt.target_type, chain, visited, max_depth)

    # =========================================================================
    # ANALYSIS
    # =========================================================================

    def analyze(self) -> LinkAnalysis:
        """
        Perform comprehensive link analysis.

        Returns:
            LinkAnalysis with all metrics
        """
        analysis = LinkAnalysis(
            total_objects=len(self._graph),
            total_links=len(self._link_types),
            cycles=self.detect_cycles(),
        )

        # Find hub objects (high connectivity)
        sorted_by_degree = sorted(
            self._graph.values(),
            key=lambda n: n.degree,
            reverse=True,
        )
        analysis.hub_objects = [
            n.object_type for n in sorted_by_degree[:5]
            if n.degree > 2
        ]

        # Find leaf objects (low connectivity)
        analysis.leaf_objects = [
            n.object_type for n in self._graph.values()
            if n.degree <= 1
        ]

        # Compute cascade chains for all objects
        for obj_type in self._graph:
            chain = self.get_cascade_chain(obj_type)
            if len(chain) > 1:
                analysis.cascade_chains[obj_type] = chain

        return analysis

    def to_graphviz(self) -> str:
        """
        Export the link graph to Graphviz DOT format.

        Returns:
            DOT format string for visualization
        """
        lines = ["digraph OntologyLinks {"]
        lines.append("  rankdir=LR;")
        lines.append("  node [shape=box];")
        lines.append("")

        # Add nodes
        for obj_type in self._graph:
            lines.append(f'  "{obj_type}";')

        lines.append("")

        # Add edges
        for link_id, lt in self._link_types.items():
            label = f"{link_id}\\n({lt.cardinality})"
            style = "dashed" if lt.is_materialized else "solid"
            color = "red" if lt.on_delete == CascadePolicy.CASCADE else "black"
            lines.append(
                f'  "{lt.source_type}" -> "{lt.target_type}" '
                f'[label="{label}", style={style}, color={color}];'
            )

        lines.append("}")
        return "\n".join(lines)

    def to_mermaid(self) -> str:
        """
        Export the link graph to Mermaid diagram format.

        Returns:
            Mermaid format string for visualization
        """
        lines = ["graph LR"]

        # Add edges (nodes are implicit)
        for link_id, lt in self._link_types.items():
            arrow = "-->" if lt.direction == LinkDirection.DIRECTED else "---"
            lines.append(
                f'  {lt.source_type}{arrow}|"{link_id}"|{lt.target_type}'
            )

        return "\n".join(lines)
