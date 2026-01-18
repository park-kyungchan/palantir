"""
SVG Generator for Stage F (Regeneration).

Generates SVG and TikZ output from semantic graph nodes:
- Pure SVG generation for web display
- TikZ code for LaTeX integration
- Coordinate transformations
- Style management

Module Version: 1.0.0
"""

import logging
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

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
)
from .exceptions import SVGGenerationError

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

# Default SVG dimensions
DEFAULT_WIDTH = 800
DEFAULT_HEIGHT = 600
DEFAULT_VIEWBOX = "0 0 800 600"

# Node type to SVG rendering style
NODE_STYLES: Dict[NodeType, Dict[str, str]] = {
    NodeType.POINT: {"fill": "#2196F3", "r": "4"},
    NodeType.LINE: {"stroke": "#333", "stroke-width": "2"},
    NodeType.LINE_SEGMENT: {"stroke": "#333", "stroke-width": "2"},
    NodeType.CIRCLE: {"stroke": "#E91E63", "stroke-width": "2", "fill": "none"},
    NodeType.POLYGON: {"stroke": "#4CAF50", "stroke-width": "2", "fill": "rgba(76,175,80,0.1)"},
    NodeType.ANGLE: {"stroke": "#FF9800", "stroke-width": "1.5"},
    NodeType.CURVE: {"stroke": "#9C27B0", "stroke-width": "2", "fill": "none"},
    NodeType.AXIS: {"stroke": "#666", "stroke-width": "1"},
    NodeType.LABEL: {"fill": "#333", "font-size": "14"},
}

# TikZ color mapping
TIKZ_COLORS: Dict[str, str] = {
    "#2196F3": "blue",
    "#333": "black",
    "#E91E63": "magenta",
    "#4CAF50": "green",
    "#FF9800": "orange",
    "#9C27B0": "purple",
    "#666": "gray",
}


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class SVGConfig:
    """Configuration for SVG generator.

    Attributes:
        width: Default canvas width
        height: Default canvas height
        margin: Margin around content
        scale: Coordinate scale factor
        coordinate_transform: Transform coordinates ('cartesian', 'svg', 'none')
        show_grid: Show background grid
        show_axes: Show coordinate axes
        font_family: Font for text elements
        font_size: Default font size
        styles: Custom styles override
        tikz_scale: Scale factor for TikZ output
    """
    width: int = DEFAULT_WIDTH
    height: int = DEFAULT_HEIGHT
    margin: int = 50
    scale: float = 50.0  # Pixels per unit
    coordinate_transform: str = "cartesian"
    show_grid: bool = False
    show_axes: bool = True
    font_family: str = "Arial, sans-serif"
    font_size: int = 14
    styles: Dict[NodeType, Dict[str, str]] = field(default_factory=dict)
    tikz_scale: float = 1.0


# =============================================================================
# SVG Generator
# =============================================================================

class SVGGenerator:
    """Generate SVG and TikZ output from semantic graph elements.

    Supports:
    - Pure SVG for web/display
    - TikZ code for LaTeX documents
    - Coordinate system transformations
    - Custom styling per node type

    Usage:
        generator = SVGGenerator()

        # Generate SVG
        svg = generator.generate_svg(graph)

        # Generate TikZ
        tikz = generator.generate_tikz(graph)

        # Full output object
        output = generator.generate_output(graph, OutputFormat.SVG)
    """

    def __init__(self, config: Optional[SVGConfig] = None):
        """Initialize SVG generator.

        Args:
            config: Generator configuration. Uses defaults if None.
        """
        self.config = config or SVGConfig()

        # Merge custom styles with defaults
        self.styles = {**NODE_STYLES, **self.config.styles}

        self._stats = {
            "svgs_generated": 0,
            "tikz_generated": 0,
            "elements_rendered": 0,
            "errors": 0,
        }

        logger.debug(
            f"SVGGenerator initialized: {self.config.width}x{self.config.height}, "
            f"scale={self.config.scale}"
        )

    @property
    def stats(self) -> Dict[str, int]:
        """Get generation statistics."""
        return self._stats.copy()

    def _transform_coords(
        self,
        x: float,
        y: float,
    ) -> Tuple[float, float]:
        """Transform mathematical coordinates to SVG coordinates.

        Applies scaling and coordinate system transformation.

        Args:
            x: Mathematical X coordinate
            y: Mathematical Y coordinate

        Returns:
            Tuple of (svg_x, svg_y)
        """
        if self.config.coordinate_transform == "cartesian":
            # Cartesian: Y-up, origin at center
            svg_x = self.config.width / 2 + x * self.config.scale
            svg_y = self.config.height / 2 - y * self.config.scale
        elif self.config.coordinate_transform == "svg":
            # SVG native: Y-down, origin at top-left
            svg_x = x * self.config.scale + self.config.margin
            svg_y = y * self.config.scale + self.config.margin
        else:
            # No transform
            svg_x = x
            svg_y = y

        return svg_x, svg_y

    def _inverse_transform_coords(
        self,
        svg_x: float,
        svg_y: float,
    ) -> Tuple[float, float]:
        """Transform SVG coordinates to mathematical coordinates.

        Args:
            svg_x: SVG X coordinate
            svg_y: SVG Y coordinate

        Returns:
            Tuple of (math_x, math_y)
        """
        if self.config.coordinate_transform == "cartesian":
            x = (svg_x - self.config.width / 2) / self.config.scale
            y = (self.config.height / 2 - svg_y) / self.config.scale
        elif self.config.coordinate_transform == "svg":
            x = (svg_x - self.config.margin) / self.config.scale
            y = (svg_y - self.config.margin) / self.config.scale
        else:
            x, y = svg_x, svg_y

        return x, y

    def _create_svg_root(self) -> ET.Element:
        """Create SVG root element with proper namespace and viewBox.

        Returns:
            SVG root Element
        """
        viewbox = f"0 0 {self.config.width} {self.config.height}"

        svg = ET.Element("svg", {
            "xmlns": "http://www.w3.org/2000/svg",
            "width": str(self.config.width),
            "height": str(self.config.height),
            "viewBox": viewbox,
        })

        # Add defs for reusable elements
        defs = ET.SubElement(svg, "defs")

        # Arrow marker for axes
        marker = ET.SubElement(defs, "marker", {
            "id": "arrowhead",
            "markerWidth": "10",
            "markerHeight": "7",
            "refX": "9",
            "refY": "3.5",
            "orient": "auto",
        })
        ET.SubElement(marker, "polygon", {
            "points": "0 0, 10 3.5, 0 7",
            "fill": "#666",
        })

        return svg

    def _add_grid(self, svg: ET.Element) -> None:
        """Add background grid to SVG.

        Args:
            svg: SVG root element
        """
        grid_group = ET.SubElement(svg, "g", {"class": "grid", "opacity": "0.2"})

        # Major grid lines every unit
        for i in range(-10, 11):
            x1, y1 = self._transform_coords(i, -10)
            x2, y2 = self._transform_coords(i, 10)
            ET.SubElement(grid_group, "line", {
                "x1": str(x1), "y1": str(y1),
                "x2": str(x2), "y2": str(y2),
                "stroke": "#ccc",
                "stroke-width": "1",
            })

            x1, y1 = self._transform_coords(-10, i)
            x2, y2 = self._transform_coords(10, i)
            ET.SubElement(grid_group, "line", {
                "x1": str(x1), "y1": str(y1),
                "x2": str(x2), "y2": str(y2),
                "stroke": "#ccc",
                "stroke-width": "1",
            })

    def _add_axes(self, svg: ET.Element) -> None:
        """Add coordinate axes to SVG.

        Args:
            svg: SVG root element
        """
        axes_group = ET.SubElement(svg, "g", {"class": "axes"})

        # X-axis
        x1, y1 = self._transform_coords(-10, 0)
        x2, y2 = self._transform_coords(10, 0)
        ET.SubElement(axes_group, "line", {
            "x1": str(x1), "y1": str(y1),
            "x2": str(x2), "y2": str(y2),
            "stroke": "#666",
            "stroke-width": "1.5",
            "marker-end": "url(#arrowhead)",
        })

        # Y-axis
        x1, y1 = self._transform_coords(0, -10)
        x2, y2 = self._transform_coords(0, 10)
        ET.SubElement(axes_group, "line", {
            "x1": str(x1), "y1": str(y1),
            "x2": str(x2), "y2": str(y2),
            "stroke": "#666",
            "stroke-width": "1.5",
            "marker-end": "url(#arrowhead)",
        })

        # Axis labels
        lx, ly = self._transform_coords(9.5, -0.5)
        ET.SubElement(axes_group, "text", {
            "x": str(lx), "y": str(ly),
            "font-family": self.config.font_family,
            "font-size": "12",
            "fill": "#666",
        }).text = "x"

        lx, ly = self._transform_coords(0.3, 9.5)
        ET.SubElement(axes_group, "text", {
            "x": str(lx), "y": str(ly),
            "font-family": self.config.font_family,
            "font-size": "12",
            "fill": "#666",
        }).text = "y"

    def _render_node_svg(
        self,
        svg: ET.Element,
        node: SemanticNode,
    ) -> bool:
        """Render a single node to SVG.

        Args:
            svg: SVG element to add to
            node: Node to render

        Returns:
            True if rendering succeeded
        """
        props = node.properties
        style = self.styles.get(node.node_type, {})

        try:
            if node.node_type == NodeType.POINT:
                if props.coordinates:
                    x, y = props.coordinates.get("x", 0), props.coordinates.get("y", 0)
                    svg_x, svg_y = self._transform_coords(x, y)

                    ET.SubElement(svg, "circle", {
                        "cx": str(svg_x),
                        "cy": str(svg_y),
                        "r": style.get("r", "4"),
                        "fill": style.get("fill", "#2196F3"),
                    })

                    # Label
                    label = props.point_label or node.label
                    ET.SubElement(svg, "text", {
                        "x": str(svg_x + 8),
                        "y": str(svg_y - 8),
                        "font-family": self.config.font_family,
                        "font-size": str(self.config.font_size),
                        "fill": "#333",
                    }).text = label

                    return True

            elif node.node_type == NodeType.LINE:
                if props.slope is not None and props.y_intercept is not None:
                    m, b = props.slope, props.y_intercept
                    # Draw line from x=-10 to x=10
                    x1, y1 = -10, m * (-10) + b
                    x2, y2 = 10, m * 10 + b

                    svg_x1, svg_y1 = self._transform_coords(x1, y1)
                    svg_x2, svg_y2 = self._transform_coords(x2, y2)

                    ET.SubElement(svg, "line", {
                        "x1": str(svg_x1), "y1": str(svg_y1),
                        "x2": str(svg_x2), "y2": str(svg_y2),
                        "stroke": style.get("stroke", "#333"),
                        "stroke-width": style.get("stroke-width", "2"),
                    })
                    return True

            elif node.node_type == NodeType.CIRCLE:
                if props.center and props.radius:
                    h, k = props.center.get("x", 0), props.center.get("y", 0)
                    r = props.radius

                    svg_cx, svg_cy = self._transform_coords(h, k)
                    svg_r = r * self.config.scale

                    ET.SubElement(svg, "circle", {
                        "cx": str(svg_cx),
                        "cy": str(svg_cy),
                        "r": str(svg_r),
                        "stroke": style.get("stroke", "#E91E63"),
                        "stroke-width": style.get("stroke-width", "2"),
                        "fill": style.get("fill", "none"),
                    })
                    return True

            elif node.node_type == NodeType.LABEL:
                if node.bbox:
                    svg_x, svg_y = self._transform_coords(node.bbox.x, node.bbox.y)
                    ET.SubElement(svg, "text", {
                        "x": str(svg_x),
                        "y": str(svg_y),
                        "font-family": self.config.font_family,
                        "font-size": str(self.config.font_size),
                        "fill": style.get("fill", "#333"),
                    }).text = node.label
                    return True

            # For unsupported types, add as a comment/metadata
            logger.debug(f"Node type {node.node_type} not directly rendered to SVG")
            return False

        except Exception as e:
            logger.warning(f"Failed to render node {node.id}: {e}")
            return False

    def generate_svg(self, graph: SemanticGraph) -> str:
        """Generate complete SVG from semantic graph.

        Args:
            graph: SemanticGraph to render

        Returns:
            SVG string

        Raises:
            SVGGenerationError: If generation fails
        """
        try:
            svg = self._create_svg_root()

            # Add optional grid
            if self.config.show_grid:
                self._add_grid(svg)

            # Add optional axes
            if self.config.show_axes:
                self._add_axes(svg)

            # Content group
            content = ET.SubElement(svg, "g", {"class": "content"})

            # Render all nodes
            rendered = 0
            for node in graph.nodes:
                if self._render_node_svg(content, node):
                    rendered += 1
                    self._stats["elements_rendered"] += 1

            self._stats["svgs_generated"] += 1

            # Convert to string
            return ET.tostring(svg, encoding="unicode")

        except Exception as e:
            self._stats["errors"] += 1
            raise SVGGenerationError(
                f"Failed to generate SVG: {e}",
                output_type="svg",
            )

    def generate_tikz(self, graph: SemanticGraph) -> str:
        """Generate TikZ code from semantic graph.

        Creates TikZ code that can be included in LaTeX documents.

        Args:
            graph: SemanticGraph to render

        Returns:
            TikZ code string
        """
        lines = []
        scale = self.config.tikz_scale

        # TikZ picture with options
        lines.append(f"\\begin{{tikzpicture}}[scale={scale}]")

        # Draw axes if enabled
        if self.config.show_axes:
            lines.append("  % Coordinate axes")
            lines.append("  \\draw[->] (-5,0) -- (5,0) node[right] {$x$};")
            lines.append("  \\draw[->] (0,-5) -- (0,5) node[above] {$y$};")

        # Draw grid if enabled
        if self.config.show_grid:
            lines.append("  % Grid")
            lines.append("  \\draw[help lines, gray!20] (-5,-5) grid (5,5);")

        # Render nodes
        lines.append("  % Nodes")
        for node in graph.nodes:
            tikz_code = self._render_node_tikz(node)
            if tikz_code:
                lines.append(f"  {tikz_code}")

        lines.append("\\end{tikzpicture}")

        self._stats["tikz_generated"] += 1

        return "\n".join(lines)

    def _render_node_tikz(self, node: SemanticNode) -> Optional[str]:
        """Render a single node to TikZ code.

        Args:
            node: Node to render

        Returns:
            TikZ code string or None
        """
        props = node.properties

        if node.node_type == NodeType.POINT:
            if props.coordinates:
                x = props.coordinates.get("x", 0)
                y = props.coordinates.get("y", 0)
                label = props.point_label or node.label
                return f"\\filldraw[blue] ({x},{y}) circle (2pt) node[above right] {{${label}$}};"

        elif node.node_type == NodeType.LINE:
            if props.slope is not None and props.y_intercept is not None:
                m, b = props.slope, props.y_intercept
                y1 = m * (-5) + b
                y2 = m * 5 + b
                return f"\\draw (-5,{y1}) -- (5,{y2});"

        elif node.node_type == NodeType.CIRCLE:
            if props.center and props.radius:
                h = props.center.get("x", 0)
                k = props.center.get("y", 0)
                r = props.radius
                return f"\\draw[magenta] ({h},{k}) circle ({r});"

        elif node.node_type == NodeType.LABEL:
            if node.bbox:
                x, y = node.bbox.x, node.bbox.y
                return f"\\node at ({x},{y}) {{${node.label}$}};"

        return None

    def generate_output(
        self,
        graph: SemanticGraph,
        format: OutputFormat = OutputFormat.SVG,
    ) -> RegenerationOutput:
        """Generate complete output object for a semantic graph.

        Args:
            graph: SemanticGraph to regenerate
            format: Output format (SVG or TIKZ)

        Returns:
            RegenerationOutput with content
        """
        start_time = time.time()
        warnings = []

        if format == OutputFormat.SVG:
            try:
                content = self.generate_svg(graph)
            except SVGGenerationError as e:
                content = f"<!-- Error: {e} -->"
                warnings.append(str(e))
        elif format == OutputFormat.TIKZ:
            try:
                content = self.generate_tikz(graph)
            except Exception as e:
                content = f"% Error: {e}"
                warnings.append(str(e))
        else:
            raise SVGGenerationError(
                f"Unsupported format for SVGGenerator: {format}",
                output_type=format.value,
            )

        generation_time = (time.time() - start_time) * 1000

        # Calculate confidence
        total_nodes = len(graph.nodes)
        confidence = 1.0 - (len(warnings) / max(total_nodes, 1))

        return RegenerationOutput(
            format=format,
            content=content,
            confidence=max(0.0, confidence),
            generation_time_ms=generation_time,
            element_count=total_nodes,
            completeness_score=confidence,
            warnings=warnings,
        )


# =============================================================================
# Factory Function
# =============================================================================

def create_svg_generator(
    config: Optional[SVGConfig] = None,
    **kwargs,
) -> SVGGenerator:
    """Factory function to create SVGGenerator.

    Args:
        config: Optional SVGConfig
        **kwargs: Config overrides

    Returns:
        Configured SVGGenerator instance
    """
    if config is None:
        config = SVGConfig(**kwargs)
    return SVGGenerator(config=config)


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "SVGGenerator",
    "SVGConfig",
    "create_svg_generator",
    "NODE_STYLES",
]
