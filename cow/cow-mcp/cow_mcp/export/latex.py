"""LaTeX document generation with XeLaTeX + kotex for Korean math/science.

Complete rewrite of cow-cli/export/latex.py. Old version used pdfLaTeX with
inputenc/fontenc — incompatible with Korean. This version uses:
- XeLaTeX engine with kotex (auto-loads xetexko — CH-4.4)
- Noto CJK KR fonts
- Full math support (amsmath, amssymb, tikz, pgfplots)
"""

import re
import logging
from typing import Optional

from cow_mcp.models.compose import CompositionResult
from cow_mcp.models.export import LatexSource

logger = logging.getLogger("cow-mcp.export.latex")

# Korean math document preamble (XeLaTeX + kotex)
# CH-4.4: kotex ONLY — do NOT load xetexko separately (kotex auto-loads it)
KOREAN_MATH_PREAMBLE = r"""\documentclass[11pt,a4paper]{article}

% Korean support (auto-loads xetexko under XeLaTeX)
\usepackage{kotex}
\setmainfont{Noto Serif CJK KR}
\setsansfont{Noto Sans CJK KR}
\setmonofont{Noto Sans Mono CJK KR}

% Math packages
\usepackage{amsmath,amssymb}
\usepackage{mathtools}

% Graphics and diagrams
\usepackage{tikz}
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}
\usepackage{graphicx}
\usepackage{float}

% Tables
\usepackage{booktabs,array,longtable}

% Page layout
\usepackage{geometry}
\geometry{margin=2.5cm}

% Hyperlinks
\usepackage{hyperref}
\hypersetup{colorlinks=true,linkcolor=blue,urlcolor=blue}
"""


class LatexGenerator:
    """Generate LaTeX documents from CompositionResult."""

    def generate(
        self,
        composition: CompositionResult,
        template: Optional[str] = None,
    ) -> LatexSource:
        """Generate a complete LaTeX document.

        Args:
            composition: CompositionResult from the COMPOSE stage.
            template: Custom preamble template. Uses Korean math preamble if None.

        Returns:
            LatexSource with content, preamble, body, and packages list.
        """
        preamble = template or KOREAN_MATH_PREAMBLE
        body = self._compose_body(composition)
        content = f"{preamble}\n\\begin{{document}}\n{body}\n\\end{{document}}\n"
        packages = self._extract_packages(preamble)

        return LatexSource(
            content=content,
            preamble=preamble,
            body=body,
            packages=packages,
        )

    def _compose_body(self, composition: CompositionResult) -> str:
        """Convert CompositionResult content to LaTeX body.

        The CompositionResult.latex_source already contains the LaTeX content
        from the COMPOSE stage (Claude native reasoning). This method extracts
        the body portion and applies metadata.
        """
        latex_source = composition.latex_source

        # If latex_source contains \\begin{document}...\\end{document}, extract body
        body_match = re.search(
            r"\\begin\{document\}(.*?)\\end\{document\}",
            latex_source,
            re.DOTALL,
        )
        if body_match:
            body = body_match.group(1).strip()
        else:
            # Assume the entire source is body content
            body = latex_source.strip()

        # Apply metadata
        body = self._apply_metadata(body, composition)

        return body

    def _apply_metadata(self, body: str, composition: CompositionResult) -> str:
        """Prepend metadata commands (title, subject, grade) to body."""
        meta = composition.metadata
        header_lines = []

        if meta.title:
            escaped_title = self._escape_latex(meta.title)
            header_lines.append(f"\\title{{{escaped_title}}}")
            header_lines.append("\\date{\\today}")
            header_lines.append("\\maketitle")

        if meta.subject or meta.grade_level:
            parts = []
            if meta.subject:
                parts.append(f"과목: {self._escape_latex(meta.subject)}")
            if meta.grade_level:
                parts.append(f"학년: {self._escape_latex(meta.grade_level)}")
            header_lines.append(f"\\noindent {' \\hfill '.join(parts)}")
            header_lines.append("\\vspace{1em}")

        if header_lines:
            return "\n".join(header_lines) + "\n\n" + body

        return body

    def _extract_packages(self, preamble: str) -> list[str]:
        """Extract package names from a LaTeX preamble."""
        packages = []
        for match in re.finditer(r"\\usepackage(?:\[.*?\])?\{([^}]+)\}", preamble):
            pkg_str = match.group(1)
            for pkg in pkg_str.split(","):
                packages.append(pkg.strip())
        return packages

    def _escape_latex(self, text: str) -> str:
        """Escape special LaTeX characters in plain text."""
        replacements = [
            ("\\", "\\textbackslash{}"),
            ("&", "\\&"),
            ("%", "\\%"),
            ("$", "\\$"),
            ("#", "\\#"),
            ("_", "\\_"),
            ("{", "\\{"),
            ("}", "\\}"),
            ("~", "\\textasciitilde{}"),
            ("^", "\\textasciicircum{}"),
        ]
        for old, new in replacements:
            text = text.replace(old, new)
        return text


__all__ = ["LatexGenerator", "KOREAN_MATH_PREAMBLE"]
