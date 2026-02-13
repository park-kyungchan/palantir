# cow/cli.py
"""COW Pipeline v2.0 CLI — Claude Code integration layer.

Opus (Claude Code) calls this via Bash tool:
  python cow/cli.py <command> [options]

All commands output JSON to stdout. Errors go to stderr.
Exit codes: 0 = success, 1 = fail-stop (model unavailable), 2 = runtime error.
"""

import argparse
import json
import sys
import logging
from pathlib import Path

logger = logging.getLogger("cow.cli")


def _output(data: dict, exit_code: int = 0) -> None:
    """Write JSON to stdout and exit."""
    json.dump(data, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    sys.exit(exit_code)


def _error(message: str, exit_code: int = 2) -> None:
    """Write error to stderr and exit."""
    sys.stderr.write(f"ERROR: {message}\n")
    json.dump({"error": message}, sys.stdout)
    sys.stdout.write("\n")
    sys.exit(exit_code)


def cmd_validate_models(args: argparse.Namespace) -> None:
    """Validate model availability (AD-9 fail-stop check)."""
    from cow.config.models import ModelConfig, ModelUnavailableError

    config = ModelConfig(
        image_model=args.image_model,
        reasoning_model=args.reasoning_model,
    )
    try:
        config.validate()
        _output({"status": "ok", "models": {
            "image": config.image_model,
            "reasoning": config.reasoning_model,
        }})
    except ModelUnavailableError as e:
        _error(f"Model unavailable: {e.model_id}. {e.detail}", exit_code=1)


def cmd_ocr(args: argparse.Namespace) -> None:
    """Run OCR extraction."""
    from cow.config.models import ModelUnavailableError

    try:
        if args.method == "gemini":
            from cow.core.ocr import extract_gemini
            result = extract_gemini(args.image, loop_params={
                "image_model": args.image_model,
                "reasoning_model": args.reasoning_model,
                "temperature": args.temperature,
                "max_iterations": args.max_iterations,
            })
        elif args.method == "mathpix":
            from cow.core.ocr import extract_mathpix
            result = extract_mathpix(args.image)
        else:
            _error(f"Unknown OCR method: {args.method}")
            return

        _output({
            "text": result.text,
            "confidence": result.confidence,
            "method": result.method,
            "iterations": result.iterations,
        })
    except ModelUnavailableError as e:
        _error(f"Model unavailable: {e.model_id}. {e.detail}", exit_code=1)
    except Exception as e:
        _error(str(e))


def cmd_diagram_detect(args: argparse.Namespace) -> None:
    """Detect diagrams in an image."""
    from cow.core.diagram import detect_diagrams
    from cow.config.models import ModelUnavailableError

    try:
        results = detect_diagrams(args.image, loop_params={
            "image_model": args.image_model,
            "reasoning_model": args.reasoning_model,
        })
        _output({"diagrams": [
            {"id": r.id, "bbox": {"x": r.x, "y": r.y, "w": r.width, "h": r.height},
             "desc": r.description, "confidence": r.confidence}
            for r in results
        ]})
    except ModelUnavailableError as e:
        _error(f"Model unavailable: {e.model_id}. {e.detail}", exit_code=1)
    except Exception as e:
        _error(str(e))


def cmd_diagram_crop(args: argparse.Namespace) -> None:
    """Crop diagram regions from an image."""
    from cow.core.diagram import crop_diagrams, BboxResult

    try:
        bboxes_data = json.loads(Path(args.bboxes).read_text())
        bboxes = [BboxResult(**b) for b in bboxes_data]
        paths = crop_diagrams(args.image, bboxes, padding=args.padding)
        _output({"crops": paths})
    except Exception as e:
        _error(str(e))


def cmd_diagram_verify(args: argparse.Namespace) -> None:
    """Verify cropped diagram quality."""
    from cow.core.diagram import verify_crops
    from cow.config.models import ModelUnavailableError

    try:
        results = verify_crops(args.crops, loop_params={
            "image_model": args.image_model,
            "reasoning_model": args.reasoning_model,
        })
        _output({"results": [
            {"path": r.path, "pass": r.passed, "issues": r.issues,
             "confidence": r.confidence}
            for r in results
        ]})
    except ModelUnavailableError as e:
        _error(f"Model unavailable: {e.model_id}. {e.detail}", exit_code=1)
    except Exception as e:
        _error(str(e))


def cmd_layout_analyze(args: argparse.Namespace) -> None:
    """Analyze page layout."""
    from cow.core.layout_design import analyze_layout
    from cow.config.models import ModelUnavailableError

    try:
        result = analyze_layout(args.image, loop_params={
            "image_model": args.image_model,
            "reasoning_model": args.reasoning_model,
        })
        _output({
            "report": result.report,
            "confidence": result.confidence,
            "iterations": result.iterations,
            "converged": result.converged,
        })
    except ModelUnavailableError as e:
        _error(f"Model unavailable: {e.model_id}. {e.detail}", exit_code=1)
    except Exception as e:
        _error(str(e))


def cmd_layout_verify(args: argparse.Namespace) -> None:
    """Verify compiled PDF layout."""
    from cow.core.layout_verify import verify_layout
    from cow.config.models import ModelUnavailableError

    try:
        result = verify_layout(args.pdf, loop_params={
            "image_model": args.image_model,
            "reasoning_model": args.reasoning_model,
        })
        _output({
            "pass": result.passed,
            "issues": result.issues,
            "report": result.report,
            "confidence": result.confidence,
        })
    except ModelUnavailableError as e:
        _error(f"Model unavailable: {e.model_id}. {e.detail}", exit_code=1)
    except Exception as e:
        _error(str(e))


def cmd_compile(args: argparse.Namespace) -> None:
    """Compile LaTeX to PDF."""
    from cow.core.compile import compile_latex

    result = compile_latex(args.tex, output_dir=args.output_dir)
    _output({
        "pdf_path": result.pdf_path,
        "success": result.success,
        "error_log": result.error_log if not result.success else "",
        "warnings": result.warnings,
    })


def cmd_preprocess(args: argparse.Namespace) -> None:
    """Convert PDF to PNG pages."""
    from pdf2image import convert_from_path

    try:
        pdf_path = Path(args.pdf)
        if not pdf_path.exists():
            _error(f"PDF not found: {args.pdf}")
            return

        images = convert_from_path(str(pdf_path), dpi=args.dpi)
        output_dir = pdf_path.parent
        pages = []
        for i, img in enumerate(images, 1):
            page_path = str(output_dir / f"{pdf_path.stem}_p{i}.png")
            img.save(page_path)
            pages.append({
                "page": i,
                "path": page_path,
                "width": img.width,
                "height": img.height,
            })

        _output({"pages": pages})
    except Exception as e:
        _error(str(e))


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="cow",
        description="COW Pipeline v2.0 — PDF Reconstruction & Editing SDK",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Common model arguments
    def add_model_args(p: argparse.ArgumentParser) -> None:
        p.add_argument("--image-model", default="gemini-3-pro-image-preview")
        p.add_argument("--reasoning-model", default="gemini-3-pro-preview")

    # validate-models
    p_validate = subparsers.add_parser("validate-models", help="Check model availability")
    add_model_args(p_validate)
    p_validate.set_defaults(func=cmd_validate_models)

    # ocr
    p_ocr = subparsers.add_parser("ocr", help="OCR extraction")
    p_ocr.add_argument("--image", required=True, help="Path to image file")
    p_ocr.add_argument("--method", choices=["gemini", "mathpix"], required=True)
    add_model_args(p_ocr)
    p_ocr.add_argument("--temperature", type=float, default=0.1)
    p_ocr.add_argument("--max-iterations", type=int, default=3)
    p_ocr.set_defaults(func=cmd_ocr)

    # diagram detect
    p_diag = subparsers.add_parser("diagram", help="Diagram operations")
    diag_sub = p_diag.add_subparsers(dest="diagram_cmd", required=True)

    p_detect = diag_sub.add_parser("detect", help="Detect diagrams")
    p_detect.add_argument("--image", required=True)
    add_model_args(p_detect)
    p_detect.set_defaults(func=cmd_diagram_detect)

    p_crop = diag_sub.add_parser("crop", help="Crop diagram regions")
    p_crop.add_argument("--image", required=True)
    p_crop.add_argument("--bboxes", required=True, help="Path to JSON bbox file")
    p_crop.add_argument("--padding", type=int, default=15)
    p_crop.set_defaults(func=cmd_diagram_crop)

    p_verify = diag_sub.add_parser("verify", help="Verify cropped diagrams")
    p_verify.add_argument("--crops", nargs="+", required=True, help="Paths to crop PNGs")
    add_model_args(p_verify)
    p_verify.set_defaults(func=cmd_diagram_verify)

    # layout
    p_layout = subparsers.add_parser("layout", help="Layout operations")
    layout_sub = p_layout.add_subparsers(dest="layout_cmd", required=True)

    p_analyze = layout_sub.add_parser("analyze", help="Analyze page layout")
    p_analyze.add_argument("--image", required=True)
    add_model_args(p_analyze)
    p_analyze.set_defaults(func=cmd_layout_analyze)

    p_lverify = layout_sub.add_parser("verify", help="Verify compiled PDF layout")
    p_lverify.add_argument("--pdf", required=True)
    add_model_args(p_lverify)
    p_lverify.set_defaults(func=cmd_layout_verify)

    # compile
    p_compile = subparsers.add_parser("compile", help="Compile LaTeX to PDF")
    p_compile.add_argument("--tex", required=True, help="Path to .tex file")
    p_compile.add_argument("--output-dir", default=None)
    p_compile.set_defaults(func=cmd_compile)

    # preprocess
    p_preprocess = subparsers.add_parser("preprocess", help="PDF to PNG conversion")
    p_preprocess.add_argument("--pdf", required=True, help="Path to PDF file")
    p_preprocess.add_argument("--dpi", type=int, default=600)
    p_preprocess.set_defaults(func=cmd_preprocess)

    # Parse and execute
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(name)s: %(message)s",
        stream=sys.stderr,  # Logs to stderr, JSON to stdout
    )
    args.func(args)


if __name__ == "__main__":
    main()
