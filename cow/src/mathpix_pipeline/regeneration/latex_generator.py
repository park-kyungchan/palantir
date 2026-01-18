"""
LaTeX Generator for Stage F (Regeneration).

Generates LaTeX output from semantic graph nodes:
- Equation generation with proper math mode
- Graph/function representation
- TikZ diagram generation
- Template-based rendering with Jinja2

Module Version: 1.0.0
"""

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ..schemas.semantic_graph import (
    SemanticGraph,
    SemanticNode,
    SemanticEdge,
    NodeType,
    EdgeType,
)
from ..schemas.regeneration import (
    OutputFormat,
    RegenerationOutput,
    TemplateContext,
    ElementCategory,
)
from .exceptions import LaTeXGenerationError, TemplateError

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

# Default templates directory
DEFAULT_TEMPLATES_DIR = Path(__file__).parent / "templates"

# Node type to LaTeX command mapping
NODE_TYPE_LATEX: Dict[NodeType, str] = {
    NodeType.POINT: r"\point",
    NodeType.LINE: r"\line",
    NodeType.LINE_SEGMENT: r"\segment",
    NodeType.RAY: r"\ray",
    NodeType.CIRCLE: r"\circle",
    NodeType.POLYGON: r"\polygon",
    NodeType.ANGLE: r"\angle",
    NodeType.EQUATION: r"\equation",
    NodeType.EXPRESSION: r"\expr",
    NodeType.VARIABLE: r"\var",
    NodeType.CONSTANT: r"\const",
    NodeType.FUNCTION: r"\func",
    NodeType.AXIS: r"\axis",
    NodeType.CURVE: r"\curve",
    NodeType.ASYMPTOTE: r"\asymptote",
    NodeType.INTERCEPT: r"\intercept",
    NodeType.LABEL: r"\label",
    NodeType.ANNOTATION: r"\annotation",
    NodeType.REGION: r"\region",
    NodeType.COORDINATE_SYSTEM: r"\coordsys",
}

# Special symbols that need escaping
LATEX_SPECIAL_CHARS: Set[str] = {"#", "$", "%", "&", "_", "{", "}", "~", "^"}


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class LaTeXConfig:
    """Configuration for LaTeX generator.

    Attributes:
        templates_dir: Path to Jinja2 templates directory
        math_mode: Default math mode ('inline', 'display', 'equation')
        include_comments: Include explanatory comments in output
        pretty_print: Format output for readability
        document_class: LaTeX document class for full documents
        packages: Required LaTeX packages
        custom_preamble: Additional preamble content
        tikz_options: Default TikZ diagram options
    """
    templates_dir: Path = DEFAULT_TEMPLATES_DIR
    math_mode: str = "display"
    include_comments: bool = False
    pretty_print: bool = True
    document_class: str = "article"
    packages: List[str] = field(default_factory=lambda: [
        "amsmath",
        "amssymb",
        "tikz",
        "pgfplots",
    ])
    custom_preamble: str = ""
    tikz_options: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# LaTeX Generator
# =============================================================================

class LaTeXGenerator:
    """Generate LaTeX output from semantic graph elements.

    Supports multiple output modes:
    - Single equation/expression generation
    - Complete graph representation
    - TikZ diagram generation
    - Template-based document generation

    Usage:
        generator = LaTeXGenerator()

        # Single node
        latex = generator.generate_equation(node)

        # Full graph
        latex = generator.generate_graph(nodes, edges)

        # TikZ diagram
        tikz = generator.generate_tikz_diagram(graph)
    """

    def __init__(self, config: Optional[LaTeXConfig] = None):
        """Initialize LaTeX generator.

        Args:
            config: Generator configuration. Uses defaults if None.
        """
        self.config = config or LaTeXConfig()
        self._template_env = None
        self._stats = {
            "equations_generated": 0,
            "graphs_generated": 0,
            "diagrams_generated": 0,
            "templates_rendered": 0,
            "errors": 0,
        }

        logger.debug(f"LaTeXGenerator initialized with math_mode={self.config.math_mode}")

    @property
    def stats(self) -> Dict[str, int]:
        """Get generation statistics."""
        return self._stats.copy()

    def _get_template_env(self):
        """Get or create Jinja2 template environment."""
        if self._template_env is None:
            try:
                from jinja2 import Environment, FileSystemLoader, select_autoescape

                self._template_env = Environment(
                    loader=FileSystemLoader(str(self.config.templates_dir)),
                    autoescape=select_autoescape(["html", "xml"]),
                    trim_blocks=True,
                    lstrip_blocks=True,
                )
                # Add custom filters
                self._template_env.filters["latex_escape"] = self._escape_latex
                self._template_env.filters["math_wrap"] = self._wrap_math

            except ImportError:
                logger.warning("Jinja2 not available, template rendering disabled")
                raise TemplateError(
                    "Jinja2 package required for template rendering. "
                    "Install with: pip install jinja2"
                )

        return self._template_env

    def _escape_latex(self, text: str) -> str:
        """Escape special LaTeX characters.

        Args:
            text: Input text

        Returns:
            Text with special characters escaped
        """
        result = text
        for char in LATEX_SPECIAL_CHARS:
            if char in result:
                result = result.replace(char, f"\\{char}")
        return result

    def _wrap_math(self, content: str, mode: Optional[str] = None) -> str:
        """Wrap content in appropriate math delimiters.

        Args:
            content: Math content
            mode: Math mode override

        Returns:
            Content wrapped in math delimiters
        """
        mode = mode or self.config.math_mode

        if mode == "inline":
            return f"${content}$"
        elif mode == "display":
            return f"\\[{content}\\]"
        elif mode == "equation":
            return f"\\begin{{equation}}\n{content}\n\\end{{equation}}"
        else:
            return content

    def generate_equation(
        self,
        node: SemanticNode,
        mode: Optional[str] = None,
    ) -> str:
        """Generate LaTeX for an equation/expression node.

        Args:
            node: SemanticNode of equation/expression type
            mode: Math mode override

        Returns:
            LaTeX string representation

        Raises:
            LaTeXGenerationError: If generation fails
        """
        try:
            # Get LaTeX from node properties
            latex_content = node.properties.latex

            if not latex_content:
                # Try to construct from node data
                latex_content = self._construct_latex_from_node(node)

            if not latex_content:
                raise LaTeXGenerationError(
                    f"No LaTeX content available for node {node.id}",
                    element_id=node.id,
                    element_type=node.node_type.value,
                )

            # Wrap in math mode
            result = self._wrap_math(latex_content, mode)

            self._stats["equations_generated"] += 1
            return result

        except LaTeXGenerationError:
            self._stats["errors"] += 1
            raise
        except Exception as e:
            self._stats["errors"] += 1
            raise LaTeXGenerationError(
                f"Failed to generate equation: {e}",
                element_id=node.id,
                element_type=node.node_type.value,
            )

    def _construct_latex_from_node(self, node: SemanticNode) -> Optional[str]:
        """Attempt to construct LaTeX from node properties.

        Args:
            node: SemanticNode

        Returns:
            Constructed LaTeX string or None
        """
        props = node.properties

        if node.node_type == NodeType.POINT:
            if props.coordinates:
                x = props.coordinates.get("x", 0)
                y = props.coordinates.get("y", 0)
                label = props.point_label or node.label
                return f"{label}({x}, {y})"

        elif node.node_type == NodeType.LINE:
            if props.equation:
                return props.equation
            elif props.slope is not None and props.y_intercept is not None:
                m = props.slope
                b = props.y_intercept
                if b >= 0:
                    return f"y = {m}x + {b}"
                else:
                    return f"y = {m}x - {abs(b)}"

        elif node.node_type == NodeType.CIRCLE:
            if props.center and props.radius:
                h = props.center.get("x", 0)
                k = props.center.get("y", 0)
                r = props.radius
                return f"(x - {h})^2 + (y - {k})^2 = {r}^2"

        elif node.node_type == NodeType.ANGLE:
            if props.measure is not None:
                unit = props.measure_unit or "degrees"
                if unit == "degrees":
                    return f"\\angle = {props.measure}^\\circ"
                else:
                    return f"\\angle = {props.measure}\\text{{ rad}}"

        elif node.node_type in (NodeType.VARIABLE, NodeType.CONSTANT):
            return node.label

        elif node.node_type == NodeType.FUNCTION:
            if props.equation:
                return props.equation
            elif props.function_type:
                return f"f(x) = \\text{{{props.function_type}}}"

        return None

    def generate_graph(
        self,
        nodes: List[SemanticNode],
        edges: List[SemanticEdge],
        include_relationships: bool = True,
    ) -> str:
        """Generate LaTeX representation of a semantic graph.

        Creates a structured LaTeX document with all nodes and their
        relationships represented mathematically.

        Args:
            nodes: List of SemanticNodes
            edges: List of SemanticEdges
            include_relationships: Include edge relationships in output

        Returns:
            Complete LaTeX representation
        """
        lines = []

        if self.config.include_comments:
            lines.append("% Semantic Graph LaTeX Representation")
            lines.append(f"% Nodes: {len(nodes)}, Edges: {len(edges)}")
            lines.append("")

        # Group nodes by type
        nodes_by_type: Dict[NodeType, List[SemanticNode]] = {}
        for node in nodes:
            if node.node_type not in nodes_by_type:
                nodes_by_type[node.node_type] = []
            nodes_by_type[node.node_type].append(node)

        # Generate equations section
        equation_types = {
            NodeType.EQUATION, NodeType.EXPRESSION, NodeType.FUNCTION,
            NodeType.LINE, NodeType.CIRCLE
        }
        equation_nodes = []
        for nt in equation_types:
            equation_nodes.extend(nodes_by_type.get(nt, []))

        if equation_nodes:
            lines.append("\\begin{align*}")
            for i, node in enumerate(equation_nodes):
                try:
                    latex_content = node.properties.latex or self._construct_latex_from_node(node)
                    if latex_content:
                        if i < len(equation_nodes) - 1:
                            lines.append(f"  {latex_content} \\\\")
                        else:
                            lines.append(f"  {latex_content}")
                except Exception as e:
                    logger.warning(f"Failed to generate LaTeX for node {node.id}: {e}")
            lines.append("\\end{align*}")
            lines.append("")

        # Generate points section
        point_nodes = nodes_by_type.get(NodeType.POINT, [])
        if point_nodes:
            if self.config.include_comments:
                lines.append("% Points")
            lines.append("\\begin{itemize}")
            for node in point_nodes:
                latex = self._construct_latex_from_node(node)
                if latex:
                    lines.append(f"  \\item ${latex}$")
            lines.append("\\end{itemize}")
            lines.append("")

        # Generate relationships if requested
        if include_relationships and edges:
            if self.config.include_comments:
                lines.append("% Relationships")
            lines.append("\\begin{itemize}")
            for edge in edges[:20]:  # Limit to prevent huge output
                rel_latex = self._generate_edge_latex(edge, nodes)
                if rel_latex:
                    lines.append(f"  \\item {rel_latex}")
            if len(edges) > 20:
                lines.append(f"  \\item ... and {len(edges) - 20} more relationships")
            lines.append("\\end{itemize}")

        self._stats["graphs_generated"] += 1

        if self.config.pretty_print:
            return "\n".join(lines)
        else:
            return " ".join(lines)

    def _generate_edge_latex(
        self,
        edge: SemanticEdge,
        nodes: List[SemanticNode],
    ) -> Optional[str]:
        """Generate LaTeX for an edge relationship.

        Args:
            edge: SemanticEdge
            nodes: List of all nodes for reference

        Returns:
            LaTeX string or None
        """
        # Find source and target nodes
        source = next((n for n in nodes if n.id == edge.source_id), None)
        target = next((n for n in nodes if n.id == edge.target_id), None)

        if not source or not target:
            return None

        source_label = source.label
        target_label = target.label

        edge_type_text = {
            EdgeType.INTERSECTS: "intersects",
            EdgeType.CONTAINS: "contains",
            EdgeType.CONTAINED_BY: "is contained by",
            EdgeType.PARALLEL_TO: "$\\parallel$",
            EdgeType.PERPENDICULAR_TO: "$\\perp$",
            EdgeType.LABELS: "labels",
            EdgeType.EQUALS: "$=$",
            EdgeType.LIES_ON: "lies on",
            EdgeType.PASSES_THROUGH: "passes through",
            EdgeType.GRAPH_OF: "is graph of",
            EdgeType.ASYMPTOTE_OF: "is asymptote of",
        }

        relation = edge_type_text.get(edge.edge_type, edge.edge_type.value)
        return f"${source_label}$ {relation} ${target_label}$"

    def generate_tikz_diagram(
        self,
        graph: SemanticGraph,
        scale: float = 1.0,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate TikZ diagram from semantic graph.

        Creates a complete TikZ picture representing the graph
        elements and their spatial relationships.

        Args:
            graph: SemanticGraph to render
            scale: Scale factor for coordinates
            options: Additional TikZ options

        Returns:
            TikZ diagram code
        """
        options = options or self.config.tikz_options

        lines = []

        # TikZ picture header
        option_str = ", ".join(f"{k}={v}" for k, v in options.items()) if options else ""
        if option_str:
            lines.append(f"\\begin{{tikzpicture}}[{option_str}, scale={scale}]")
        else:
            lines.append(f"\\begin{{tikzpicture}}[scale={scale}]")

        if self.config.include_comments:
            lines.append(f"  % Generated from SemanticGraph: {graph.image_id}")

        # Draw coordinate system if present
        if graph.coordinate_system:
            lines.append("  % Coordinate axes")
            lines.append("  \\draw[->] (-5,0) -- (5,0) node[right] {$x$};")
            lines.append("  \\draw[->] (0,-5) -- (0,5) node[above] {$y$};")

        # Draw nodes by type
        for node in graph.nodes:
            tikz_code = self._generate_tikz_node(node, scale)
            if tikz_code:
                lines.append(f"  {tikz_code}")

        # Draw edges
        for edge in graph.edges:
            tikz_code = self._generate_tikz_edge(edge, graph.nodes)
            if tikz_code:
                lines.append(f"  {tikz_code}")

        lines.append("\\end{tikzpicture}")

        self._stats["diagrams_generated"] += 1

        return "\n".join(lines)

    def _generate_tikz_node(self, node: SemanticNode, scale: float = 1.0) -> Optional[str]:
        """Generate TikZ code for a single node.

        Args:
            node: SemanticNode to render
            scale: Coordinate scale factor

        Returns:
            TikZ code string or None
        """
        props = node.properties

        if node.node_type == NodeType.POINT:
            if props.coordinates:
                x = props.coordinates.get("x", 0) * scale
                y = props.coordinates.get("y", 0) * scale
                label = props.point_label or node.label
                return f"\\filldraw ({x},{y}) circle (2pt) node[above right] {{${label}$}};"

        elif node.node_type == NodeType.LINE:
            if props.slope is not None and props.y_intercept is not None:
                m = props.slope
                b = props.y_intercept
                x1, x2 = -5 * scale, 5 * scale
                y1 = m * (-5) + b
                y2 = m * 5 + b
                return f"\\draw ({x1},{y1}) -- ({x2},{y2});"

        elif node.node_type == NodeType.CIRCLE:
            if props.center and props.radius:
                h = props.center.get("x", 0) * scale
                k = props.center.get("y", 0) * scale
                r = props.radius * scale
                return f"\\draw ({h},{k}) circle ({r});"

        elif node.node_type == NodeType.CURVE:
            if props.equation:
                # For curves, suggest pgfplots usage
                return f"% Curve: {props.equation} (use pgfplots for rendering)"

        elif node.node_type == NodeType.LABEL:
            if node.bbox:
                x = node.bbox.x * scale
                y = node.bbox.y * scale
                return f"\\node at ({x},{y}) {{${node.label}$}};"

        return None

    def _generate_tikz_edge(
        self,
        edge: SemanticEdge,
        nodes: List[SemanticNode],
    ) -> Optional[str]:
        """Generate TikZ code for an edge.

        Args:
            edge: SemanticEdge
            nodes: List of all nodes

        Returns:
            TikZ code or None
        """
        # Only draw certain edge types visually
        drawable_types = {
            EdgeType.INTERSECTS,
            EdgeType.PARALLEL_TO,
            EdgeType.PERPENDICULAR_TO,
        }

        if edge.edge_type not in drawable_types:
            return None

        source = next((n for n in nodes if n.id == edge.source_id), None)
        target = next((n for n in nodes if n.id == edge.target_id), None)

        if not source or not target:
            return None

        if source.bbox and target.bbox:
            sx, sy = source.bbox.center
            tx, ty = target.bbox.center

            if edge.edge_type == EdgeType.INTERSECTS:
                return f"\\draw[dashed, gray] ({sx},{sy}) -- ({tx},{ty});"

        return None

    def render_template(
        self,
        template_name: str,
        context: TemplateContext,
    ) -> str:
        """Render a Jinja2 template with given context.

        Args:
            template_name: Name of template file (e.g., 'equation.tex.j2')
            context: TemplateContext with rendering data

        Returns:
            Rendered template string

        Raises:
            TemplateError: If template loading or rendering fails
        """
        try:
            env = self._get_template_env()
            template = env.get_template(template_name)

            rendered = template.render(
                nodes=context.nodes,
                edges=context.edges,
                config=self.config,
                **context.custom_vars,
            )

            self._stats["templates_rendered"] += 1
            return rendered

        except TemplateError:
            raise
        except Exception as e:
            self._stats["errors"] += 1
            raise TemplateError(
                f"Failed to render template: {e}",
                template_name=template_name,
                render_context=context.custom_vars,
            )

    def generate_output(
        self,
        graph: SemanticGraph,
        include_tikz: bool = True,
    ) -> RegenerationOutput:
        """Generate complete LaTeX output for a semantic graph.

        Args:
            graph: SemanticGraph to regenerate
            include_tikz: Include TikZ diagram

        Returns:
            RegenerationOutput with LaTeX content
        """
        start_time = time.time()
        warnings = []

        # Generate main content
        latex_parts = []

        # Generate equations/expressions
        try:
            graph_latex = self.generate_graph(
                graph.nodes,
                graph.edges,
                include_relationships=True,
            )
            latex_parts.append(graph_latex)
        except Exception as e:
            warnings.append(f"Graph generation warning: {e}")

        # Generate TikZ if requested
        if include_tikz:
            try:
                tikz_latex = self.generate_tikz_diagram(graph)
                latex_parts.append("")
                latex_parts.append(tikz_latex)
            except Exception as e:
                warnings.append(f"TikZ generation warning: {e}")

        content = "\n".join(latex_parts)
        generation_time = (time.time() - start_time) * 1000

        # Calculate confidence based on completeness
        total_nodes = len(graph.nodes)
        successful = total_nodes - len(warnings)
        confidence = successful / max(total_nodes, 1)

        return RegenerationOutput(
            format=OutputFormat.LATEX,
            content=content,
            confidence=confidence,
            generation_time_ms=generation_time,
            element_count=total_nodes,
            completeness_score=confidence,
            warnings=warnings,
        )


# =============================================================================
# Factory Function
# =============================================================================

def create_latex_generator(
    config: Optional[LaTeXConfig] = None,
    **kwargs,
) -> LaTeXGenerator:
    """Factory function to create LaTeXGenerator.

    Args:
        config: Optional LaTeXConfig
        **kwargs: Config overrides

    Returns:
        Configured LaTeXGenerator instance
    """
    if config is None:
        config = LaTeXConfig(**kwargs)
    return LaTeXGenerator(config=config)


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "LaTeXGenerator",
    "LaTeXConfig",
    "create_latex_generator",
    "NODE_TYPE_LATEX",
]
