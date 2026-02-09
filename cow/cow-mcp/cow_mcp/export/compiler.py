"""XeLaTeX subprocess compilation with error handling and Mathpix backup.

Compiles LaTeX to PDF using xelatex, with:
- Font availability checks
- Multi-pass compilation for cross-references
- Auto-fix for common compilation errors
- Mathpix /v3/converter as fallback (D-5)
"""

import asyncio
import os
import re
import shutil
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import Optional

import httpx

from cow_mcp.models.export import ExportResult

logger = logging.getLogger("cow-mcp.export.compiler")

# Required fonts for Korean math documents
REQUIRED_FONTS = {
    "Noto Serif CJK KR": "noto-serif-cjk-kr",
    "Noto Sans CJK KR": "noto-sans-cjk-kr",
    "Noto Sans Mono CJK KR": "noto-sans-mono-cjk-kr",
}

# Fallback font chain
FALLBACK_FONTS = [
    ("Nanum Myeongjo", "NanumMyeongjo"),
    ("UnBatang", "UnBatang"),
]


class XeLatexCompiler:
    """Compile LaTeX to PDF using XeLaTeX."""

    XELATEX_CMD = "xelatex"
    MAX_COMPILE_PASSES = 3
    TIMEOUT_SECONDS = 120

    async def compile(
        self,
        latex_path: str,
        output_dir: Optional[str] = None,
    ) -> ExportResult:
        """Compile a LaTeX file to PDF using xelatex.

        Args:
            latex_path: Path to the .tex file.
            output_dir: Output directory for the PDF. Defaults to same dir as .tex.

        Returns:
            ExportResult with pdf_path, compilation_log, warnings.
        """
        tex_path = Path(latex_path)
        if not tex_path.exists():
            return ExportResult(
                pdf_path="",
                method="xelatex",
                page_count=0,
                compilation_log=f"File not found: {latex_path}",
                warnings=[f"File not found: {latex_path}"],
            )

        if output_dir:
            out_dir = Path(output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
        else:
            out_dir = tex_path.parent

        # Check xelatex availability
        if not shutil.which(self.XELATEX_CMD):
            return ExportResult(
                pdf_path="",
                method="xelatex",
                page_count=0,
                compilation_log="xelatex not found in PATH",
                warnings=["xelatex binary not found — install TeX Live"],
            )

        # Compile (up to MAX_COMPILE_PASSES for cross-references)
        full_log = []
        warnings = []
        success = False

        for pass_num in range(1, self.MAX_COMPILE_PASSES + 1):
            log, return_code = await self._run_xelatex(tex_path, out_dir)
            full_log.append(f"=== Pass {pass_num} ===\n{log}")

            if return_code == 0:
                success = True
                # Check if rerun needed (cross-references)
                if "Rerun to get cross-references right" not in log:
                    break
            else:
                # Try auto-fix on first failure
                if pass_num == 1:
                    fixed = self._auto_fix_errors(log, str(tex_path))
                    if fixed:
                        warnings.append("Auto-fix applied, retrying compilation")
                        continue
                break

        compilation_log = "\n".join(full_log)

        # Parse warnings from log
        for line in compilation_log.splitlines():
            if "LaTeX Warning:" in line or "Package" in line and "Warning" in line:
                warnings.append(line.strip())

        pdf_path = out_dir / tex_path.with_suffix(".pdf").name
        if success and pdf_path.exists():
            file_size = pdf_path.stat().st_size
            page_count = self._count_pdf_pages(pdf_path)
            return ExportResult(
                pdf_path=str(pdf_path),
                method="xelatex",
                page_count=page_count,
                compilation_log=compilation_log,
                warnings=warnings,
                file_size_bytes=file_size,
            )
        else:
            return ExportResult(
                pdf_path="",
                method="xelatex",
                page_count=0,
                compilation_log=compilation_log,
                warnings=warnings + ["Compilation failed — no PDF produced"],
            )

    async def _run_xelatex(self, tex_path: Path, output_dir: Path) -> tuple[str, int]:
        """Run a single xelatex pass."""
        cmd = [
            self.XELATEX_CMD,
            "-interaction=nonstopmode",
            "-halt-on-error",
            f"-output-directory={output_dir}",
            str(tex_path),
        ]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=str(tex_path.parent),
            )
            stdout, _ = await asyncio.wait_for(
                proc.communicate(), timeout=self.TIMEOUT_SECONDS
            )
            return stdout.decode("utf-8", errors="replace"), proc.returncode or 0
        except asyncio.TimeoutError:
            proc.kill()
            return "Compilation timed out", 1
        except Exception as e:
            return f"Compilation error: {e}", 1

    async def check_fonts(self) -> dict[str, bool]:
        """Check availability of required Korean fonts via fc-list."""
        results = {}
        try:
            proc = await asyncio.create_subprocess_exec(
                "fc-list", "--format=%{family}\n",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            available_fonts = stdout.decode("utf-8", errors="replace")

            for font_name in REQUIRED_FONTS:
                results[font_name] = font_name in available_fonts

        except FileNotFoundError:
            for font_name in REQUIRED_FONTS:
                results[font_name] = False

        return results

    def _auto_fix_errors(self, log: str, latex_path: str) -> bool:
        """Attempt to auto-fix common compilation errors.

        Returns True if a fix was applied.
        """
        tex = Path(latex_path).read_text(encoding="utf-8")
        original = tex

        # Fix: Font not found → fall back to available font
        font_missing = re.search(r"Font .*(Noto.*CJK KR).* not found", log)
        if font_missing:
            missing_font = font_missing.group(1)
            for fallback_name, fallback_font in FALLBACK_FONTS:
                tex = tex.replace(missing_font, fallback_name)
            logger.warning(f"Auto-fix: replaced missing font '{missing_font}' with fallback")

        # Fix: Undefined control sequence for common issues
        if "Undefined control sequence" in log and "\\pgfplotsset" in log:
            if "\\usepackage{pgfplots}" not in tex:
                tex = tex.replace(
                    "\\usepackage{tikz}",
                    "\\usepackage{tikz}\n\\usepackage{pgfplots}",
                )
                logger.warning("Auto-fix: added missing pgfplots package")

        if tex != original:
            Path(latex_path).write_text(tex, encoding="utf-8")
            return True

        return False

    def _count_pdf_pages(self, pdf_path: Path) -> int:
        """Count pages in a PDF file."""
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(pdf_path))
            return len(reader.pages)
        except Exception:
            return 1

    async def mathpix_convert(self, mmd_content: str) -> ExportResult:
        """Convert MMD to PDF using Mathpix /v3/converter as backup.

        Args:
            mmd_content: Mathpix Markdown content.

        Returns:
            ExportResult with the converted PDF path.
        """
        app_id = os.environ.get("MATHPIX_APP_ID", "")
        app_key = os.environ.get("MATHPIX_APP_KEY", "")

        if not app_id or not app_key:
            return ExportResult(
                pdf_path="",
                method="mathpix_converter",
                page_count=0,
                compilation_log="MATHPIX_APP_ID and MATHPIX_APP_KEY not configured",
                warnings=["Mathpix credentials missing"],
            )

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.mathpix.com/v3/converter",
                    headers={
                        "app_id": app_id,
                        "app_key": app_key,
                        "Content-Type": "application/json",
                    },
                    json={
                        "mmd": mmd_content,
                        "formats": {"pdf": True},
                    },
                )
                response.raise_for_status()
                data = response.json()

                # Mathpix returns a conversion ID for polling
                conversion_id = data.get("pdf_id") or data.get("conversion_id", "")

                if not conversion_id:
                    return ExportResult(
                        pdf_path="",
                        method="mathpix_converter",
                        page_count=0,
                        compilation_log=f"Unexpected response: {data}",
                        warnings=["No conversion ID returned"],
                    )

                # Poll for completion
                pdf_bytes = await self._poll_mathpix_pdf(client, conversion_id, app_id, app_key)

                if pdf_bytes:
                    output_path = Path(tempfile.mktemp(suffix=".pdf", prefix="cow_mathpix_"))
                    output_path.write_bytes(pdf_bytes)
                    return ExportResult(
                        pdf_path=str(output_path),
                        method="mathpix_converter",
                        page_count=self._count_pdf_pages(output_path),
                        compilation_log="Mathpix conversion successful",
                        file_size_bytes=len(pdf_bytes),
                    )
                else:
                    return ExportResult(
                        pdf_path="",
                        method="mathpix_converter",
                        page_count=0,
                        compilation_log="Mathpix conversion timed out",
                        warnings=["PDF conversion did not complete within timeout"],
                    )

        except httpx.HTTPStatusError as e:
            return ExportResult(
                pdf_path="",
                method="mathpix_converter",
                page_count=0,
                compilation_log=f"Mathpix API error: {e.response.status_code} {e.response.text}",
                warnings=[f"Mathpix API error: {e.response.status_code}"],
            )
        except Exception as e:
            return ExportResult(
                pdf_path="",
                method="mathpix_converter",
                page_count=0,
                compilation_log=f"Mathpix conversion error: {e}",
                warnings=[str(e)],
            )

    async def _poll_mathpix_pdf(
        self,
        client: httpx.AsyncClient,
        conversion_id: str,
        app_id: str,
        app_key: str,
        max_attempts: int = 30,
        interval: float = 2.0,
    ) -> Optional[bytes]:
        """Poll Mathpix for completed PDF conversion."""
        for _ in range(max_attempts):
            await asyncio.sleep(interval)
            try:
                response = await client.get(
                    f"https://api.mathpix.com/v3/converter/{conversion_id}",
                    headers={"app_id": app_id, "app_key": app_key},
                )
                response.raise_for_status()

                content_type = response.headers.get("content-type", "")
                if "application/pdf" in content_type:
                    return response.content

                data = response.json()
                status = data.get("status", "")
                if status == "completed" and "pdf_url" in data:
                    pdf_response = await client.get(data["pdf_url"])
                    pdf_response.raise_for_status()
                    return pdf_response.content
                elif status in ("error", "failed"):
                    logger.error(f"Mathpix conversion failed: {data}")
                    return None
            except Exception as e:
                logger.warning(f"Polling error: {e}")
                continue

        return None


__all__ = ["XeLatexCompiler"]
