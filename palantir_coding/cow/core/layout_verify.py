# cow/core/layout_verify.py
"""Loop D: Layout verification via Gemini (L1+L2).

Converts compiled PDF -> PNG, sends to Gemini for visual quality check.
Detects: text/diagram overlap, truncation, alignment issues.

Opus (L3) receives the text report and presents it to the user
for approval, or applies fixes and recompiles.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path

from pdf2image import convert_from_path

from cow.core.gemini_loop import GeminiQualityLoop, LoopResult

logger = logging.getLogger("cow.core.layout_verify")


@dataclass
class LayoutVerifyReport:
    """Layout verification report from Loop D.

    Attributes:
        passed: Whether the layout passed verification.
        issues: List of specific issues found.
        report: Full text report from Gemini.
        confidence: Verification confidence (0.0-1.0).
        page_image: Path to the PNG used for verification.
    """

    passed: bool = False
    issues: list = field(default_factory=list)
    report: str = ""
    confidence: float = 0.0
    page_image: str = ""


def verify_layout(
    pdf_path: str,
    loop_params: dict | None = None,
    page_number: int = 1,
    dpi: int = 300,
) -> LayoutVerifyReport:
    """Verify compiled PDF layout via Loop A (L1+L2).

    Converts the specified page to PNG and sends to Gemini for analysis.

    Args:
        pdf_path: Path to compiled PDF.
        loop_params: Optional GeminiQualityLoop parameters.
        page_number: Page to verify (1-indexed).
        dpi: Resolution for PDF->PNG conversion (300 for verification).

    Returns:
        LayoutVerifyReport with pass/fail, issues, and text report.
    """
    params = loop_params or {}

    # Convert PDF page to PNG
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        return LayoutVerifyReport(
            passed=False,
            issues=[f"PDF not found: {pdf_path}"],
            report=f"PDF not found: {pdf_path}",
        )

    images = convert_from_path(
        str(pdf_file),
        first_page=page_number,
        last_page=page_number,
        dpi=dpi,
    )
    if not images:
        return LayoutVerifyReport(
            passed=False,
            issues=["PDF->PNG conversion produced no images"],
            report="PDF->PNG conversion failed",
        )

    # Save temp PNG for Gemini
    page_png = str(pdf_file.parent / f"_verify_page_{page_number}.png")
    images[0].save(page_png)

    loop = GeminiQualityLoop(
        image_model=params.get("image_model", "gemini-3-pro-image-preview"),
        reasoning_model=params.get("reasoning_model", "gemini-3-pro-preview"),
        api_key=params.get("api_key"),
    )

    task_prompt = (
        "Analyze this compiled PDF page for layout quality.\n"
        "Check for:\n"
        "1. Text/diagram overlap — any elements blocking each other\n"
        "2. Page overflow — content cut off at margins\n"
        "3. Content truncation — missing text at page boundaries\n"
        "4. Alignment issues — misaligned columns, uneven spacing\n"
        "5. Diagram rendering quality — clear, proportional, well-placed\n"
        "6. Overall visual fidelity — clean, professional appearance\n\n"
        "Return a structured text report. Start with PASS or FAIL, "
        "then list specific issues if any."
    )

    validation_prompt = (
        "Validate this layout verification against the PDF page.\n"
        "Check: Are the reported issues real? Are there missed issues?\n"
        "Is the pass/fail determination correct?\n"
        "Score confidence 0-1."
    )

    result: LoopResult = loop.run(
        image_path=page_png,
        task_prompt=task_prompt,
        validation_prompt=validation_prompt,
        temperature=params.get("temperature", 0.1),
        max_iterations=params.get("max_iterations", 3),
        confidence_threshold=params.get("confidence_threshold", 0.9),
    )

    report_text = result.result if isinstance(result.result, str) else str(result.result)
    passed = report_text.strip().upper().startswith("PASS")
    issues = []
    if not passed:
        # Extract issue lines from report
        for line in report_text.split("\n"):
            line = line.strip()
            if line and not line.upper().startswith("FAIL") and not line.upper().startswith("PASS"):
                issues.append(line)

    return LayoutVerifyReport(
        passed=passed,
        issues=issues,
        report=report_text,
        confidence=result.confidence,
        page_image=page_png,
    )
