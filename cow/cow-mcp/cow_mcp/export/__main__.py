"""COW Export MCP Server — XeLaTeX + kotex PDF generation."""

import json
import traceback
import tempfile
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from cow_mcp.models.compose import CompositionResult
from cow_mcp.export.latex import LatexGenerator
from cow_mcp.export.compiler import XeLatexCompiler

mcp = FastMCP("cow-export")
generator = LatexGenerator()
compiler = XeLatexCompiler()


@mcp.tool()
async def cow_generate_latex(composition: str, template: str | None = None) -> str:
    """Generate a LaTeX document from a CompositionResult.

    Takes the output of the COMPOSE stage and produces a complete LaTeX document
    with XeLaTeX + kotex preamble for Korean math/science content.

    Args:
        composition: JSON string of a CompositionResult (from COMPOSE stage).
        template: Optional custom LaTeX preamble template.
    """
    try:
        comp = CompositionResult.model_validate_json(composition)
        result = generator.generate(comp, template=template)

        # Save LaTeX source to a temp file for compilation
        tex_dir = Path(tempfile.mkdtemp(prefix="cow_latex_"))
        tex_path = tex_dir / "document.tex"
        tex_path.write_text(result.content, encoding="utf-8")

        return json.dumps({
            "latex_source": result.model_dump(),
            "tex_path": str(tex_path),
            "packages": result.packages,
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "traceback": traceback.format_exc()})


@mcp.tool()
async def cow_compile_pdf(latex_path: str, output_dir: str | None = None) -> str:
    """Compile a LaTeX file to PDF using XeLaTeX.

    Runs xelatex with Korean font support (Noto CJK KR via kotex).
    Automatically retries for cross-references and attempts auto-fix on errors.

    Args:
        latex_path: Absolute path to the .tex file.
        output_dir: Optional output directory for the PDF.
    """
    try:
        # Check fonts first
        fonts = await compiler.check_fonts()
        missing_fonts = [f for f, available in fonts.items() if not available]

        result = await compiler.compile(latex_path, output_dir)
        response = result.model_dump()
        if missing_fonts:
            response["font_warnings"] = [f"Missing font: {f}" for f in missing_fonts]
        return json.dumps(response, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "traceback": traceback.format_exc()})


@mcp.tool()
async def cow_mathpix_mmd_to_pdf(mmd_content: str) -> str:
    """Convert Mathpix Markdown to PDF using Mathpix /v3/converter.

    Backup method when XeLaTeX compilation fails. Sends MMD content to Mathpix API
    for server-side PDF generation. Requires MATHPIX_APP_ID and MATHPIX_APP_KEY.

    Args:
        mmd_content: Mathpix Markdown content to convert to PDF.
    """
    try:
        result = await compiler.mathpix_convert(mmd_content)
        return json.dumps(result.model_dump(), ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "traceback": traceback.format_exc()})


if __name__ == "__main__":
    mcp.run(transport="stdio")
