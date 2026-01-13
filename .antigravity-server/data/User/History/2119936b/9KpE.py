"""
Math Workbook Action Templates

Reusable action sequences for generating math workbook documents.
Based on OWPML architecture and common patterns from sample.pdf.

Usage:
    from lib.templates.math_workbook import MathWorkbookTemplates as T
    
    actions = [
        *T.border_box_start(),
        *T.two_column_layout(),
        *T.problem_header(4),
        *T.equation_inline("x^2 + y^2 = r^2"),
        ...
        *T.column_break(),
        *T.problem_header(7),
        ...
        *T.two_column_end(),
    ]
"""

from typing import List, Dict, Any
from lib.models import (
    HwpAction, InsertText, SetParaShape, InsertEquation,
    MultiColumn, SetFontBold, SetFontSize
)


class MathWorkbookTemplates:
    """
    Pre-built action sequences for math workbook document patterns.
    All methods return List[HwpAction] for easy composition.
    """
    
    # === Layout Templates ===
    
    @staticmethod
    def two_column_layout(gap_hwpunit: int = 850) -> List[HwpAction]:
        """
        Start 2-column layout.
        Args:
            gap_hwpunit: Gap between columns (1mm ≈ 283 HwpUnit)
        """
        return [
            MultiColumn(count=2, same_size=True, gap=gap_hwpunit)
        ]
    
    @staticmethod
    def two_column_end() -> List[HwpAction]:
        """End multi-column layout, return to single column."""
        return [
            MultiColumn(count=1, same_size=True, gap=0)
        ]
    
    @staticmethod
    def column_break() -> List[Dict[str, Any]]:
        """Insert column break (move to next column)."""
        return [
            {"action_type": "BreakColumn"}
        ]
    
    @staticmethod
    def border_box_start(border_type: str = "Solid", width: str = "0.4mm", color: str = "#000000") -> List[Dict[str, Any]]:
        """
        Start a border box enclosure.
        Note: Uses raw dict as CreateBorderBox model needs to be added.
        """
        return [
            {
                "action_type": "CreateBorderBox",
                "border_type": border_type,
                "border_width": width,
                "border_color": color
            }
        ]
    
    # === Problem Structure Templates ===
    
    @staticmethod
    def problem_header(problem_number: int) -> List[HwpAction]:
        """
        Generate problem number with hanging indent.
        Example: "4. " with left margin and negative indent.
        """
        return [
            SetParaShape(left_margin=20, right_margin=0, indent=-20, line_spacing=160),
            InsertText(text=f"{problem_number}. ")
        ]
    
    @staticmethod
    def subproblem(sub_number: int) -> List[HwpAction]:
        """
        Generate subproblem number.
        Example: "(1) " with hanging indent.
        """
        return [
            SetParaShape(left_margin=20, right_margin=0, indent=-20, line_spacing=160),
            InsertText(text=f"({sub_number}) ")
        ]
    
    @staticmethod
    def body_text(text: str) -> List[HwpAction]:
        """Insert normal body text."""
        return [
            SetParaShape(left_margin=0, right_margin=0, indent=0, line_spacing=160),
            InsertText(text=text)
        ]
    
    @staticmethod
    def equation_inline(latex_script: str) -> List[HwpAction]:
        """Insert inline equation."""
        return [
            InsertEquation(script=latex_script)
        ]
    
    @staticmethod
    def line_break() -> List[HwpAction]:
        """Insert line break with reset paragraph style."""
        return [
            SetParaShape(left_margin=0, right_margin=0, indent=0, line_spacing=160),
            InsertText(text="\r\n")
        ]
    
    # === Answer Templates ===
    
    @staticmethod
    def answer_box(answer_text: str, font_size: float = 14.0) -> List[HwpAction]:
        """
        Format answer with bold and larger font.
        """
        return [
            SetFontBold(is_bold=True),
            SetFontSize(size=font_size),
            InsertText(text=answer_text),
            SetFontBold(is_bold=False),
            SetFontSize(size=10.0)  # Reset to default
        ]
    
    @staticmethod
    def answer_simple(answer_text: str) -> List[HwpAction]:
        """Simple answer without special formatting."""
        return [
            InsertText(text=answer_text)
        ]
    
    # === Composite Templates ===
    
    @staticmethod
    def problem_with_equation(
        problem_number: int,
        condition_latex: str,
        body_text: str
    ) -> List[HwpAction]:
        """
        Complete problem template:
        "N. [equation] 일 때, [body_text]"
        """
        actions = []
        actions.extend(MathWorkbookTemplates.problem_header(problem_number))
        actions.extend(MathWorkbookTemplates.equation_inline(condition_latex))
        actions.append(InsertText(text=f" {body_text}"))
        actions.extend(MathWorkbookTemplates.line_break())
        return actions
    
    @staticmethod
    def subproblem_with_equation(
        sub_number: int,
        equation_latex: str,
        answer: str = None
    ) -> List[HwpAction]:
        """
        Subproblem template:
        "(N) [equation]"
        Optionally followed by answer.
        """
        actions = []
        actions.extend(MathWorkbookTemplates.subproblem(sub_number))
        actions.extend(MathWorkbookTemplates.equation_inline(equation_latex))
        actions.extend(MathWorkbookTemplates.line_break())
        
        if answer:
            actions.extend(MathWorkbookTemplates.answer_box(answer))
            actions.extend(MathWorkbookTemplates.line_break())
        
        return actions


# Convenience alias
T = MathWorkbookTemplates
