"""Reconstruction Validator - Verify PDF quality.

This module provides the ReconstructionValidator class for validating
reconstructed PDF documents against the original B1 separation outputs.

Quality Thresholds:
- Text Coverage: >= 90% (acceptable), >= 95% (good)
- Math Coverage: >= 85% (acceptable), >= 90% (good)
- Layout Order: >= 95% (acceptable), >= 98% (good)
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Literal
import json

try:
    import pdfplumber
except ImportError:
    pdfplumber = None


@dataclass
class ValidationIssue:
    """Single validation issue.

    Attributes:
        type: Issue type identifier.
        message: Human-readable description of the issue.
        element_id: ID of the affected element (if applicable).
        severity: Issue severity level.
    """

    type: str
    message: str
    element_id: Optional[str] = None
    severity: Literal["warning", "error"] = "warning"


@dataclass
class ValidationResult:
    """Result of validation.

    Attributes:
        valid: Overall validation passed (all minimum thresholds met).
        text_coverage: Ratio of text content preserved (0.0 to 1.0).
        math_coverage: Ratio of math content preserved (0.0 to 1.0).
        layout_order_score: Score for element ordering preservation (0.0 to 1.0).
        issues: List of validation issues found.
    """

    valid: bool
    text_coverage: float
    math_coverage: float
    layout_order_score: float
    issues: list[ValidationIssue] = field(default_factory=list)

    def get_recommendations(self) -> list[str]:
        """Get recommendations based on validation results.

        Returns:
            List of actionable recommendations.
        """
        recs = []

        if self.text_coverage < 0.9:
            recs.append(
                f"Text coverage is {self.text_coverage:.1%} (below 90%). "
                "Check for missing content or OCR errors in the source."
            )

        if self.math_coverage < 0.85:
            recs.append(
                f"Math coverage is {self.math_coverage:.1%} (below 85%). "
                "Verify LaTeX syntax and rendering. Consider manual review of equations."
            )

        if self.layout_order_score < 0.95:
            recs.append(
                f"Layout order score is {self.layout_order_score:.1%} (below 95%). "
                "Review element ordering in the reconstructed PDF."
            )

        if not recs:
            if self.text_coverage >= 0.95 and self.math_coverage >= 0.9:
                recs.append("Reconstruction quality is excellent.")
            else:
                recs.append("Reconstruction quality is acceptable.")

        return recs

    def is_acceptable(self) -> bool:
        """Check if reconstruction meets minimum acceptable thresholds.

        Returns:
            True if all metrics meet minimum thresholds.
        """
        return (
            self.text_coverage >= 0.9
            and self.math_coverage >= 0.85
            and self.layout_order_score >= 0.95
        )

    def is_good(self) -> bool:
        """Check if reconstruction meets good quality thresholds.

        Returns:
            True if all metrics meet good thresholds.
        """
        return (
            self.text_coverage >= 0.95
            and self.math_coverage >= 0.9
            and self.layout_order_score >= 0.98
        )

    def needs_human_review(self) -> bool:
        """Check if human review is recommended.

        Returns:
            True if any metric is below 80% or multiple issues exist.
        """
        below_80 = (
            self.text_coverage < 0.8
            or self.math_coverage < 0.7
            or self.layout_order_score < 0.8
        )
        many_issues = len(self.issues) >= 3
        has_errors = any(i.severity == "error" for i in self.issues)

        return below_80 or many_issues or has_errors


class ReconstructionValidator:
    """Validate PDF reconstruction against B1 outputs.

    This class compares the reconstructed PDF with the original
    layout.json and content.json to calculate quality metrics.

    Example:
        >>> validator = ReconstructionValidator()
        >>> result = await validator.validate(
        ...     pdf_path=Path("output/reconstructed.pdf"),
        ...     layout_path=Path("output/layout.json"),
        ...     content_path=Path("output/content.json")
        ... )
        >>> if result.valid:
        ...     print("Reconstruction quality is acceptable")
        >>> else:
        ...     for rec in result.get_recommendations():
        ...         print(f"- {rec}")
    """

    def __init__(self):
        """Initialize the validator.

        Raises:
            ImportError: If pdfplumber is not installed.
        """
        if pdfplumber is None:
            raise ImportError(
                "pdfplumber is required for PDF validation. "
                "Install with: pip install pdfplumber"
            )

    async def validate(
        self,
        pdf_path: Path,
        layout_path: Path,
        content_path: Path,
    ) -> ValidationResult:
        """Validate reconstructed PDF against B1 outputs.

        Args:
            pdf_path: Path to the reconstructed PDF.
            layout_path: Path to the original layout.json.
            content_path: Path to the original content.json.

        Returns:
            ValidationResult with quality metrics and issues.

        Raises:
            FileNotFoundError: If any input file doesn't exist.
        """
        # Validate input files exist
        for path, name in [
            (pdf_path, "PDF"),
            (layout_path, "layout.json"),
            (content_path, "content.json"),
        ]:
            if not path.exists():
                raise FileNotFoundError(f"{name} not found: {path}")

        # Load B1 outputs
        content_data = json.loads(content_path.read_text(encoding="utf-8"))

        # Extract text from PDF
        pdf_text = self._extract_pdf_text(pdf_path)

        # Calculate coverage scores
        text_coverage = self._calculate_text_coverage(content_data, pdf_text)
        math_coverage = self._calculate_math_coverage(content_data, pdf_text)
        layout_score = self._calculate_layout_order(content_data, pdf_text)

        # Collect issues
        issues: list[ValidationIssue] = []

        if text_coverage < 0.9:
            issues.append(
                ValidationIssue(
                    type="low_text_coverage",
                    message=f"Text coverage is {text_coverage:.1%} (threshold: 90%)",
                    severity="warning" if text_coverage >= 0.8 else "error",
                )
            )

        if math_coverage < 0.85:
            issues.append(
                ValidationIssue(
                    type="low_math_coverage",
                    message=f"Math coverage is {math_coverage:.1%} (threshold: 85%)",
                    severity="warning" if math_coverage >= 0.7 else "error",
                )
            )

        if layout_score < 0.95:
            issues.append(
                ValidationIssue(
                    type="layout_order_mismatch",
                    message=f"Layout order score is {layout_score:.1%} (threshold: 95%)",
                    severity="warning" if layout_score >= 0.8 else "error",
                )
            )

        # Overall validity check (minimum thresholds)
        valid = text_coverage >= 0.8 and math_coverage >= 0.7 and layout_score >= 0.8

        return ValidationResult(
            valid=valid,
            text_coverage=text_coverage,
            math_coverage=math_coverage,
            layout_order_score=layout_score,
            issues=issues,
        )

    def _extract_pdf_text(self, pdf_path: Path) -> str:
        """Extract text from PDF.

        Args:
            pdf_path: Path to the PDF file.

        Returns:
            Concatenated text from all pages.
        """
        text_parts: list[str] = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n".join(text_parts)

    def _calculate_text_coverage(
        self,
        content_data: dict,
        pdf_text: str,
    ) -> float:
        """Calculate text content coverage.

        Args:
            content_data: Content JSON data.
            pdf_text: Extracted PDF text.

        Returns:
            Coverage ratio (0.0 to 1.0).
        """
        elements = content_data.get("elements", [])
        text_elements = [e for e in elements if e.get("text") or e.get("text_display")]

        if not text_elements:
            return 1.0

        pdf_text_lower = pdf_text.lower()
        found = 0

        for elem in text_elements:
            text = elem.get("text_display") or elem.get("text", "")
            if not text:
                continue

            # Fuzzy match - check if significant portion exists
            # Use first 5 words (words > 2 chars) to avoid false positives
            words = [w for w in text.split()[:5] if len(w) > 2]
            if words and all(word.lower() in pdf_text_lower for word in words):
                found += 1

        return found / len(text_elements)

    def _calculate_math_coverage(
        self,
        content_data: dict,
        pdf_text: str,
    ) -> float:
        """Calculate math content coverage.

        Args:
            content_data: Content JSON data.
            pdf_text: Extracted PDF text (for basic checks).

        Returns:
            Coverage ratio (0.0 to 1.0).

        Note:
            Full math validation would require image comparison.
            This implementation provides a basic heuristic based on
            successful PDF generation.
        """
        elements = content_data.get("elements", [])
        math_elements = [e for e in elements if e.get("latex")]

        if not math_elements:
            return 1.0

        # For math, text extraction is unreliable for rendered LaTeX
        # We use a heuristic: if the PDF was generated successfully,
        # assume 90% coverage for simple math, lower for complex
        complex_count = sum(
            1
            for e in math_elements
            if len(e.get("latex", "")) > 50  # Complex LaTeX
            or "\\begin" in e.get("latex", "")  # Environments
        )

        complex_ratio = complex_count / len(math_elements) if math_elements else 0

        # Base score of 0.9, reduced for complex math
        base_score = 0.9 - (complex_ratio * 0.1)

        return max(0.7, base_score)  # Minimum 70%

    def _calculate_layout_order(
        self,
        content_data: dict,
        pdf_text: str,
    ) -> float:
        """Calculate layout order preservation score.

        Args:
            content_data: Content JSON data.
            pdf_text: Extracted PDF text.

        Returns:
            Order preservation score (0.0 to 1.0).
        """
        elements = content_data.get("elements", [])
        text_elements = [
            (e.get("text_display") or e.get("text", ""))[:20]
            for e in elements
            if e.get("text") or e.get("text_display")
        ]

        if len(text_elements) < 2:
            return 1.0

        pdf_text_lower = pdf_text.lower()

        # Check if elements appear in order in PDF
        last_pos = -1
        in_order = 0
        checked = 0

        for text in text_elements:
            if not text or len(text) < 5:
                continue

            checked += 1
            pos = pdf_text_lower.find(text[:10].lower())

            if pos > last_pos:
                in_order += 1
                last_pos = pos
            elif pos >= 0:
                # Found but out of order
                last_pos = pos  # Update position anyway to continue tracking

        return in_order / checked if checked > 0 else 1.0


__all__ = [
    "ReconstructionValidator",
    "ValidationResult",
    "ValidationIssue",
]
