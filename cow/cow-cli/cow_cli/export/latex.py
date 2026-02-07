"""
COW CLI - LaTeX Exporter

Export separated documents to LaTeX format.
"""
from pathlib import Path
from typing import Optional
from io import StringIO
from enum import Enum

from cow_cli.export.base import BaseExporter, ExportFormat, ExportOptions, ExportResult
from cow_cli.semantic.schemas import (
    SeparatedDocument,
    ContentElement,
    LayoutElement,
    ElementType,
)


class DocumentClass(str, Enum):
    """LaTeX document classes."""
    ARTICLE = "article"
    REPORT = "report"
    BOOK = "book"
    STANDALONE = "standalone"


class LaTeXExporter(BaseExporter):
    """
    LaTeX format exporter.

    Creates a compilable LaTeX document.
    """

    format = ExportFormat.LATEX

    PREAMBLE_TEMPLATE = r"""
\documentclass[{options}]{{{docclass}}}

% Encoding
\usepackage[utf8]{{inputenc}}
\usepackage[T1]{{fontenc}}

% Math packages
\usepackage{{amsmath}}
\usepackage{{amssymb}}
\usepackage{{amsfonts}}

% Graphics
\usepackage{{graphicx}}
\usepackage{{float}}

% Tables
\usepackage{{booktabs}}
\usepackage{{array}}
\usepackage{{longtable}}

% Code listings
\usepackage{{listings}}
\lstset{{
    basicstyle=\ttfamily\small,
    breaklines=true,
    frame=single,
}}

% Hyperlinks
\usepackage{{hyperref}}
\hypersetup{{
    colorlinks=true,
    linkcolor=blue,
    urlcolor=blue,
}}

% Custom commands
\newcommand{{\cowsource}}[1]{{\texttt{{#1}}}}

"""

    def __init__(
        self,
        options: Optional[ExportOptions] = None,
        document_class: DocumentClass = DocumentClass.ARTICLE,
        class_options: str = "12pt,a4paper",
        include_images: bool = False,
        standalone: bool = False,
    ):
        """
        Initialize LaTeX exporter.

        Args:
            options: Export options
            document_class: LaTeX document class
            class_options: Document class options
            include_images: Include image references
            standalone: Minimal standalone document
        """
        super().__init__(options)
        self.document_class = document_class
        self.class_options = class_options
        self.include_images = include_images
        self.standalone = standalone

    def export(self, document: SeparatedDocument, output_path: Path) -> ExportResult:
        """
        Export document to LaTeX.

        Args:
            document: The separated document
            output_path: Destination file path

        Returns:
            ExportResult with status
        """
        warnings = []
        output_path = self.ensure_extension(output_path)

        # Validate
        validation_errors = self.validate_document(document)
        if validation_errors:
            warnings.extend(validation_errors)

        try:
            # Build LaTeX content
            latex_content = self._build_latex(document)

            # Write
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(latex_content, encoding="utf-8")

            return ExportResult(
                success=True,
                output_path=output_path,
                format=self.format,
                bytes_written=len(latex_content.encode("utf-8")),
                warnings=warnings,
            )

        except Exception as e:
            return ExportResult(
                success=False,
                error=str(e),
                warnings=warnings,
            )

    def _build_latex(self, document: SeparatedDocument) -> str:
        """Build the LaTeX content."""
        output = StringIO()

        # Preamble
        if not self.standalone:
            output.write(self._build_preamble())
            output.write("\n\\begin{document}\n\n")

        # Title
        title = self._escape_latex(
            Path(document.image_path).stem.replace("_", " ").title()
        )
        output.write(f"\\title{{{title}}}\n")
        output.write("\\date{\\today}\n")
        output.write("\\maketitle\n\n")

        # Source info
        output.write(f"\\cowsource{{{self._escape_latex(document.image_path)}}}\n\n")

        # Content
        output.write(self._build_content(document))

        # End document
        if not self.standalone:
            output.write("\n\\end{document}\n")

        return output.getvalue()

    def _build_preamble(self) -> str:
        """Build LaTeX preamble."""
        return self.PREAMBLE_TEMPLATE.format(
            docclass=self.document_class.value,
            options=self.class_options,
        )

    def _build_content(self, document: SeparatedDocument) -> str:
        """Build the main content."""
        output = StringIO()

        current_section = None

        for content_elem in document.content.elements:
            layout_elem = document.layout.get_element_by_id(
                content_elem.layout_ref or content_elem.id
            )

            elem_type = layout_elem.type if layout_elem else ElementType.TEXT

            # Section headers
            if elem_type != current_section:
                section_name = elem_type.replace("_", " ").title() if isinstance(elem_type, str) else str(elem_type).replace("_", " ").title()
                output.write(f"\n\\section{{{section_name}}}\n\n")
                current_section = elem_type

            # Render element
            output.write(self._render_element(content_elem, layout_elem))
            output.write("\n\n")

        return output.getvalue()

    def _render_element(
        self,
        content: ContentElement,
        layout: Optional[LayoutElement],
    ) -> str:
        """Render a single element to LaTeX."""
        elem_type = layout.type if layout else ElementType.TEXT

        # Title
        if elem_type == ElementType.TITLE:
            return self._render_title(content)

        # Section headers
        if elem_type == ElementType.SECTION_HEADER:
            return self._render_section(content)

        # Math
        if elem_type == ElementType.MATH:
            return self._render_math(content)

        # Table
        if elem_type == ElementType.TABLE:
            return self._render_table(content)

        # Code
        if elem_type in (ElementType.CODE, ElementType.PSEUDOCODE):
            return self._render_code(content)

        # Diagram
        if elem_type in (ElementType.DIAGRAM, ElementType.CHART):
            return self._render_figure(content, layout)

        # Default: text
        return self._render_text(content)

    def _render_title(self, content: ContentElement) -> str:
        """Render title."""
        text = self._escape_latex(content.text or "")
        return f"\\title{{{text}}}"

    def _render_section(self, content: ContentElement) -> str:
        """Render section header."""
        text = self._escape_latex(content.text or "")
        return f"\\subsection{{{text}}}"

    def _render_math(self, content: ContentElement) -> str:
        """Render math element."""
        latex = content.latex or content.latex_styled or ""

        if not latex:
            text = content.text or ""
            return self._escape_latex(text)

        # Check if it's display or inline math
        if "\n" in latex or len(latex) > 60:
            # Display math
            return f"\\begin{{equation}}\n{latex}\n\\end{{equation}}"
        else:
            # Could be part of paragraph - use align for display
            return f"\\begin{{align}}\n{latex}\n\\end{{align}}"

    def _render_table(self, content: ContentElement) -> str:
        """Render table element."""
        # Try TSV data first
        for data in content.data:
            if data.type.value == "tsv":
                return self._tsv_to_latex_table(data.value)

        # Fallback to text
        text = content.text or ""
        return f"\\begin{{verbatim}}\n{text}\n\\end{{verbatim}}"

    def _tsv_to_latex_table(self, tsv: str) -> str:
        """Convert TSV to LaTeX table."""
        lines = tsv.strip().split("\n")
        if not lines:
            return ""

        # Determine columns
        first_row = lines[0].split("\t")
        num_cols = len(first_row)
        col_spec = "l" * num_cols

        output = StringIO()
        output.write("\\begin{table}[H]\n")
        output.write("\\centering\n")
        output.write(f"\\begin{{tabular}}{{{col_spec}}}\n")
        output.write("\\toprule\n")

        for i, line in enumerate(lines):
            cells = line.split("\t")
            escaped_cells = [self._escape_latex(cell) for cell in cells]
            row = " & ".join(escaped_cells) + " \\\\"
            output.write(row + "\n")

            if i == 0:
                output.write("\\midrule\n")

        output.write("\\bottomrule\n")
        output.write("\\end{tabular}\n")
        output.write("\\end{table}")

        return output.getvalue()

    def _render_code(self, content: ContentElement) -> str:
        """Render code element."""
        code = content.text or ""
        return f"\\begin{{lstlisting}}\n{code}\n\\end{{lstlisting}}"

    def _render_figure(
        self,
        content: ContentElement,
        layout: Optional[LayoutElement],
    ) -> str:
        """Render figure/diagram placeholder."""
        output = StringIO()
        output.write("\\begin{figure}[H]\n")
        output.write("\\centering\n")

        if self.include_images and layout and layout.region:
            # Placeholder for image
            output.write(f"% Image region: {layout.region.width}x{layout.region.height}\n")
            output.write("\\fbox{\\parbox{0.8\\textwidth}{\\centering [Figure/Diagram]}}\n")
        else:
            output.write("\\fbox{\\parbox{0.8\\textwidth}{\\centering [Figure/Diagram]}}\n")

        # Caption from text if available
        if content.text:
            caption = self._escape_latex(content.text[:100])
            output.write(f"\\caption{{{caption}}}\n")

        output.write("\\end{figure}")

        return output.getvalue()

    def _render_text(self, content: ContentElement) -> str:
        """Render text element."""
        text = content.text or content.text_display or ""

        # Check for inline math
        if content.latex and not text:
            return f"${content.latex}$"

        return self._escape_latex(text)

    def _escape_latex(self, text: str) -> str:
        """Escape special LaTeX characters."""
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


__all__ = ["LaTeXExporter", "DocumentClass"]
