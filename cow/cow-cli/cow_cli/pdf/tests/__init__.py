"""
COW CLI - PDF Reconstruction Tests

Test suite for the pdf module:
- test_merger.py: MMDMerger unit tests
- test_converter.py: MathpixPDFConverter unit tests (mocked API)
- test_validator.py: ReconstructionValidator unit tests
- test_e2e_reconstruction.py: End-to-end integration tests
"""

from pathlib import Path

# Test fixtures directory
FIXTURES_DIR = Path(__file__).parent / "fixtures"

__all__ = ["FIXTURES_DIR"]
