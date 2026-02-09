# cow/core/compile.py
"""XeLaTeX compilation with Korean font support (kotex + Noto CJK KR).

Simplified from v1.0 compiler.py:
- Removed Mathpix converter fallback (AD-9 fail-stop)
- Removed async (synchronous subprocess.run)
- Kept multi-pass compilation for cross-references
- Kept auto-fix for common errors (font fallback, missing packages)
"""

import logging
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger("cow.core.compile")

XELATEX_CMD = "xelatex"
MAX_PASSES = 3
TIMEOUT_SECONDS = 120


@dataclass
class CompileResult:
    """XeLaTeX compilation result.

    Attributes:
        pdf_path: Path to generated PDF (empty on failure).
        success: Whether compilation succeeded.
        error_log: Full compilation log (useful for debugging).
        warnings: List of LaTeX warnings.
    """

    pdf_path: str = ""
    success: bool = False
    error_log: str = ""
    warnings: list = field(default_factory=list)


def compile_latex(
    tex_path: str,
    output_dir: str | None = None,
) -> CompileResult:
    """Compile a .tex file to PDF using XeLaTeX.

    Runs up to 3 passes for cross-reference resolution.
    Attempts auto-fix on first failure (font substitution, missing packages).

    Args:
        tex_path: Path to the .tex file.
        output_dir: Output directory. Defaults to same directory as .tex.

    Returns:
        CompileResult with pdf_path (if success), logs, and warnings.
    """
    tex_file = Path(tex_path)
    if not tex_file.exists():
        return CompileResult(
            error_log=f"File not found: {tex_path}",
            warnings=[f"File not found: {tex_path}"],
        )

    if not shutil.which(XELATEX_CMD):
        return CompileResult(
            error_log="xelatex not found in PATH",
            warnings=["xelatex binary not found — install texlive-xetex"],
        )

    out_dir = Path(output_dir) if output_dir else tex_file.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    full_log_parts = []
    warnings = []

    for pass_num in range(1, MAX_PASSES + 1):
        cmd = [
            XELATEX_CMD,
            "-interaction=nonstopmode",
            "-halt-on-error",
            f"-output-directory={out_dir}",
            str(tex_file),
        ]

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SECONDS,
                cwd=str(tex_file.parent),
            )
            log = proc.stdout
            returncode = proc.returncode
        except subprocess.TimeoutExpired:
            log = "Compilation timed out"
            returncode = 1

        full_log_parts.append(f"=== Pass {pass_num} ===\n{log}")

        if returncode == 0:
            if "Rerun to get cross-references right" not in log:
                break
        else:
            if pass_num == 1:
                if _auto_fix_errors(log, str(tex_file)):
                    warnings.append("Auto-fix applied, retrying")
                    continue
            break

    full_log = "\n".join(full_log_parts)

    # Extract warnings
    for line in full_log.splitlines():
        if "LaTeX Warning:" in line:
            warnings.append(line.strip())

    pdf_path = out_dir / tex_file.with_suffix(".pdf").name
    if pdf_path.exists():
        return CompileResult(
            pdf_path=str(pdf_path),
            success=True,
            error_log=full_log,
            warnings=warnings,
        )
    else:
        return CompileResult(
            error_log=full_log,
            warnings=warnings + ["Compilation failed — no PDF produced"],
        )


def _auto_fix_errors(log: str, tex_path: str) -> bool:
    """Attempt auto-fix for common compilation errors."""
    tex = Path(tex_path).read_text(encoding="utf-8")
    original = tex

    # Fix: Missing font -> fallback to Nanum Myeongjo
    if "not found" in log.lower() and "Noto" in log:
        tex = tex.replace("Noto Serif CJK KR", "Nanum Myeongjo")
        tex = tex.replace("Noto Sans CJK KR", "Nanum Gothic")
        logger.warning("Auto-fix: replaced Noto CJK fonts with Nanum fallback")

    # Fix: Missing pgfplots package
    if "Undefined control sequence" in log and "pgfplotsset" in log:
        if "\\usepackage{pgfplots}" not in tex:
            tex = tex.replace(
                "\\usepackage{tikz}",
                "\\usepackage{tikz}\n\\usepackage{pgfplots}\n\\pgfplotsset{compat=1.18}",
            )
            logger.warning("Auto-fix: added missing pgfplots package")

    if tex != original:
        Path(tex_path).write_text(tex, encoding="utf-8")
        return True
    return False
