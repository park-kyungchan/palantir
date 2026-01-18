#!/usr/bin/env python3
"""
Export Verification Script for Math Image Parsing Pipeline v2.0.

This script verifies that all pipeline modules have properly defined
__all__ exports and can be imported without errors.

Usage:
    python scripts/verify_exports.py
    python scripts/verify_exports.py --verbose
    python scripts/verify_exports.py --json

Exit Codes:
    0: All modules verified successfully
    1: One or more modules failed verification
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Add src to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
SRC_PATH = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_PATH))


# Modules to verify - organized by pipeline stage
MODULES_TO_VERIFY = [
    # Core
    "mathpix_pipeline",
    "mathpix_pipeline.logging_config",
    # Schemas
    "mathpix_pipeline.schemas",
    "mathpix_pipeline.schemas.common",
    "mathpix_pipeline.schemas.threshold",
    "mathpix_pipeline.schemas.text_spec",
    "mathpix_pipeline.schemas.vision_spec",
    "mathpix_pipeline.schemas.ingestion",
    "mathpix_pipeline.schemas.alignment",
    "mathpix_pipeline.schemas.semantic_graph",
    "mathpix_pipeline.schemas.regeneration",
    "mathpix_pipeline.schemas.human_review",
    "mathpix_pipeline.schemas.export",
    "mathpix_pipeline.schemas.pipeline",
    # Stage A: Ingestion
    "mathpix_pipeline.ingestion",
    "mathpix_pipeline.ingestion.exceptions",
    "mathpix_pipeline.ingestion.loader",
    "mathpix_pipeline.ingestion.validator",
    "mathpix_pipeline.ingestion.preprocessor",
    "mathpix_pipeline.ingestion.storage",
    # Clients
    "mathpix_pipeline.clients",
    "mathpix_pipeline.clients.mathpix",
    # Utils
    "mathpix_pipeline.utils",
    "mathpix_pipeline.utils.geometry",
    # Stage C: Vision
    "mathpix_pipeline.vision",
    "mathpix_pipeline.vision.exceptions",
    "mathpix_pipeline.vision.detection_layer",
    "mathpix_pipeline.vision.interpretation_layer",
    "mathpix_pipeline.vision.hybrid_merger",
    "mathpix_pipeline.vision.gemini_client",
    "mathpix_pipeline.vision.fallback",
    "mathpix_pipeline.vision.yolo_detector",
    # Stage D: Alignment
    "mathpix_pipeline.alignment",
    "mathpix_pipeline.alignment.matcher",
    "mathpix_pipeline.alignment.inconsistency",
    "mathpix_pipeline.alignment.consistency",
    "mathpix_pipeline.alignment.engine",
    # Stage E: Semantic Graph
    "mathpix_pipeline.semantic_graph",
    "mathpix_pipeline.semantic_graph.node_extractor",
    "mathpix_pipeline.semantic_graph.edge_inferrer",
    "mathpix_pipeline.semantic_graph.validators",
    "mathpix_pipeline.semantic_graph.confidence",
    "mathpix_pipeline.semantic_graph.builder",
    # Stage F: Regeneration
    "mathpix_pipeline.regeneration",
    "mathpix_pipeline.regeneration.exceptions",
    "mathpix_pipeline.regeneration.latex_generator",
    "mathpix_pipeline.regeneration.svg_generator",
    "mathpix_pipeline.regeneration.delta_comparer",
    "mathpix_pipeline.regeneration.engine",
    # Stage G: Human Review
    "mathpix_pipeline.human_review",
    "mathpix_pipeline.human_review.exceptions",
    "mathpix_pipeline.human_review.models",
    "mathpix_pipeline.human_review.models.annotation",
    "mathpix_pipeline.human_review.models.reviewer",
    "mathpix_pipeline.human_review.models.task",
    "mathpix_pipeline.human_review.queue_manager",
    "mathpix_pipeline.human_review.annotation_workflow",
    "mathpix_pipeline.human_review.feedback_loop",
    "mathpix_pipeline.human_review.priority_scorer",
    "mathpix_pipeline.human_review.api",
    "mathpix_pipeline.human_review.api.review_endpoints",
    # Stage H: Export
    "mathpix_pipeline.export",
    "mathpix_pipeline.export.exceptions",
    "mathpix_pipeline.export.storage",
    "mathpix_pipeline.export.engine",
    "mathpix_pipeline.export.exporters",
    "mathpix_pipeline.export.exporters.base",
    "mathpix_pipeline.export.exporters.json_exporter",
    "mathpix_pipeline.export.exporters.pdf_exporter",
    "mathpix_pipeline.export.exporters.latex_exporter",
    "mathpix_pipeline.export.exporters.svg_exporter",
    "mathpix_pipeline.export.api",
    "mathpix_pipeline.export.api.endpoints",
]


@dataclass
class ModuleResult:
    """Result of verifying a single module."""

    module_name: str
    success: bool
    has_all: bool = False
    export_count: int = 0
    exports: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass
class VerificationReport:
    """Overall verification report."""

    total_modules: int
    successful: int
    failed: int
    missing_all: int
    total_exports: int
    results: list[ModuleResult] = field(default_factory=list)

    @property
    def success(self) -> bool:
        """Check if all verifications passed."""
        return self.failed == 0

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary for JSON output."""
        return {
            "summary": {
                "total_modules": self.total_modules,
                "successful": self.successful,
                "failed": self.failed,
                "missing_all": self.missing_all,
                "total_exports": self.total_exports,
                "success": self.success,
            },
            "modules": [
                {
                    "name": r.module_name,
                    "success": r.success,
                    "has_all": r.has_all,
                    "export_count": r.export_count,
                    "exports": r.exports,
                    "error": r.error,
                }
                for r in self.results
            ],
        }


def verify_module(module_name: str, verbose: bool = False) -> ModuleResult:
    """
    Verify a single module's exports.

    Args:
        module_name: Fully qualified module name.
        verbose: If True, print detailed information.

    Returns:
        ModuleResult with verification details.
    """
    result = ModuleResult(module_name=module_name, success=False)

    try:
        # Import the module
        module = importlib.import_module(module_name)

        # Check for __all__
        if hasattr(module, "__all__"):
            result.has_all = True
            result.exports = list(module.__all__)
            result.export_count = len(result.exports)

            # Verify all exports actually exist
            missing = []
            for name in result.exports:
                if not hasattr(module, name):
                    missing.append(name)

            if missing:
                result.error = f"Missing exports: {missing}"
            else:
                result.success = True
        else:
            result.has_all = False
            # Still consider it a success if it imports, just note missing __all__
            result.success = True
            result.error = "No __all__ defined"

    except ImportError as e:
        result.error = f"Import error: {e}"
    except Exception as e:
        result.error = f"Unexpected error: {e}"

    return result


def verify_all_modules(
    modules: list[str],
    verbose: bool = False,
) -> VerificationReport:
    """
    Verify all specified modules.

    Args:
        modules: List of module names to verify.
        verbose: If True, print detailed progress.

    Returns:
        VerificationReport with all results.
    """
    results: list[ModuleResult] = []
    successful = 0
    failed = 0
    missing_all = 0
    total_exports = 0

    for module_name in modules:
        if verbose:
            print(f"Checking {module_name}...", end=" ")

        result = verify_module(module_name, verbose)
        results.append(result)

        if result.success:
            successful += 1
            total_exports += result.export_count
            if verbose:
                if result.has_all:
                    print(f"OK ({result.export_count} exports)")
                else:
                    print("OK (no __all__)")
        else:
            failed += 1
            if verbose:
                print(f"FAILED: {result.error}")

        if not result.has_all:
            missing_all += 1

    return VerificationReport(
        total_modules=len(modules),
        successful=successful,
        failed=failed,
        missing_all=missing_all,
        total_exports=total_exports,
        results=results,
    )


def print_summary(report: VerificationReport) -> None:
    """Print human-readable summary."""
    print("\n" + "=" * 60)
    print("EXPORT VERIFICATION SUMMARY")
    print("=" * 60)
    print(f"Total modules checked: {report.total_modules}")
    print(f"Successful:            {report.successful}")
    print(f"Failed:                {report.failed}")
    print(f"Missing __all__:       {report.missing_all}")
    print(f"Total exports:         {report.total_exports}")
    print("=" * 60)

    if report.failed > 0:
        print("\nFAILED MODULES:")
        for result in report.results:
            if not result.success:
                print(f"  - {result.module_name}: {result.error}")

    if report.missing_all > 0:
        print("\nMODULES WITHOUT __all__:")
        for result in report.results:
            if not result.has_all:
                print(f"  - {result.module_name}")

    print()
    if report.success:
        print("STATUS: PASS")
    else:
        print("STATUS: FAIL")


def print_detailed_exports(report: VerificationReport) -> None:
    """Print detailed export list for each module."""
    print("\nDETAILED EXPORTS:")
    print("-" * 60)
    for result in report.results:
        if result.success and result.has_all:
            print(f"\n{result.module_name} ({result.export_count} exports):")
            for export in sorted(result.exports):
                print(f"  - {export}")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Verify pipeline module exports"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print detailed progress",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Show detailed export list for each module",
    )
    parser.add_argument(
        "--module",
        type=str,
        help="Verify a specific module instead of all",
    )
    args = parser.parse_args()

    # Determine which modules to check
    if args.module:
        modules = [args.module]
    else:
        modules = MODULES_TO_VERIFY

    # Run verification
    report = verify_all_modules(modules, verbose=args.verbose)

    # Output results
    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print_summary(report)
        if args.detailed:
            print_detailed_exports(report)

    return 0 if report.success else 1


if __name__ == "__main__":
    sys.exit(main())
