# cow/core/layout_design.py
"""Loop C: Layout design analysis via Gemini (L1+L2).

Analyzes original page layout and produces a text report describing:
column configuration, box styles, diagram placement, typography, etc.

Opus (L3) receives this text report and presents it to the user
for approval/modification before generating the LaTeX template.
"""

import logging
from dataclasses import dataclass

from cow.core.gemini_loop import GeminiQualityLoop, LoopResult

logger = logging.getLogger("cow.core.layout_design")


@dataclass
class LayoutDesignReport:
    """Layout analysis report from Loop C.

    Attributes:
        report: Text description of the layout design.
        confidence: Analysis confidence (0.0-1.0).
        iterations: Number of Loop A iterations.
        converged: Whether Loop A converged.
    """

    report: str = ""
    confidence: float = 0.0
    iterations: int = 0
    converged: bool = False


def analyze_layout(
    image_path: str,
    loop_params: dict | None = None,
) -> LayoutDesignReport:
    """Analyze original page layout via Loop A (L1+L2).

    Args:
        image_path: Path to original page image (PNG, 600 DPI).
        loop_params: Optional GeminiQualityLoop parameters.

    Returns:
        LayoutDesignReport with text description of layout.
    """
    params = loop_params or {}

    loop = GeminiQualityLoop(
        image_model=params.get("image_model", "gemini-3-pro-image-preview"),
        reasoning_model=params.get("reasoning_model", "gemini-3-pro-preview"),
        api_key=params.get("api_key"),
    )

    task_prompt = (
        "Analyze the layout and design of this document page.\n"
        "Describe in detail:\n"
        "1. Column configuration (single-column, two-column, minipage)\n"
        "2. Problem/question box styling (framed, tcolorbox, plain, indented)\n"
        "3. Diagram placement strategy (inline, float, margin, right-aligned)\n"
        "4. Font size estimate and line spacing\n"
        "5. Page margins (narrow, normal, wide)\n"
        "6. Header/footer presence and content\n"
        "7. Section/problem numbering style (1., (1), Q1, etc.)\n"
        "8. Any special visual elements (watermarks, logos, borders)\n\n"
        "Return a structured text report, NOT JSON."
    )

    validation_prompt = (
        "Validate this layout analysis against the original image.\n"
        "Check for:\n"
        "1. Accuracy of column count detection\n"
        "2. Correct identification of box/frame styles\n"
        "3. Reasonable font size and spacing estimates\n"
        "4. Completeness — are any major layout features missed?\n"
        "Score confidence 0-1."
    )

    result: LoopResult = loop.run(
        image_path=image_path,
        task_prompt=task_prompt,
        validation_prompt=validation_prompt,
        temperature=params.get("temperature", 0.1),
        max_iterations=params.get("max_iterations", 3),
        confidence_threshold=params.get("confidence_threshold", 0.9),
    )

    return LayoutDesignReport(
        report=result.result if isinstance(result.result, str) else str(result.result),
        confidence=result.confidence,
        iterations=result.iterations,
        converged=result.converged,
    )
