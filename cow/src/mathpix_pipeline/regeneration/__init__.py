"""
Stage F: Regeneration Module for Math Image Parsing Pipeline v2.0.

This module handles regeneration of mathematical content from semantic graphs:
- LaTeX output generation with template support
- SVG and TikZ diagram generation
- Delta comparison with original content
- Quality assessment and validation

Schema Version: 2.0.0

Usage:
    from mathpix_pipeline.regeneration import (
        RegenerationEngine,
        LaTeXGenerator,
        SVGGenerator,
        DeltaComparer,
    )

    # Create engine
    engine = RegenerationEngine()

    # Regenerate from semantic graph
    result = await engine.regenerate(semantic_graph)

    # Get LaTeX output
    latex = result.spec.get_latex()

    # Get SVG output
    svg = result.spec.get_svg()
"""

# Exceptions
from .exceptions import (
    RegenerationError,
    TemplateError,
    LaTeXGenerationError,
    SVGGenerationError,
    DeltaComparisonError,
    UnsupportedNodeTypeError,
)

# LaTeX Generator
from .latex_generator import (
    LaTeXGenerator,
    LaTeXConfig,
    create_latex_generator,
    NODE_TYPE_LATEX,
)

# SVG Generator
from .svg_generator import (
    SVGGenerator,
    SVGConfig,
    create_svg_generator,
    NODE_STYLES,
)

# Delta Comparer
from .delta_comparer import (
    DeltaComparer,
    DeltaConfig,
    create_delta_comparer,
    NODE_TO_CATEGORY,
)

# Engine
from .engine import (
    RegenerationEngine,
    RegenerationConfig,
    EngineResult,
    create_regeneration_engine,
)


# Version
__version__ = "2.0.0"


__all__ = [
    # Version
    "__version__",

    # === Exceptions ===
    "RegenerationError",
    "TemplateError",
    "LaTeXGenerationError",
    "SVGGenerationError",
    "DeltaComparisonError",
    "UnsupportedNodeTypeError",

    # === LaTeX Generator ===
    "LaTeXGenerator",
    "LaTeXConfig",
    "create_latex_generator",
    "NODE_TYPE_LATEX",

    # === SVG Generator ===
    "SVGGenerator",
    "SVGConfig",
    "create_svg_generator",
    "NODE_STYLES",

    # === Delta Comparer ===
    "DeltaComparer",
    "DeltaConfig",
    "create_delta_comparer",
    "NODE_TO_CATEGORY",

    # === Engine ===
    "RegenerationEngine",
    "RegenerationConfig",
    "EngineResult",
    "create_regeneration_engine",
]
