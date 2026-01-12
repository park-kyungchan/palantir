"""
Compatibility module for scripts -> lib.oda migration.

DEPRECATED: Import from lib.oda instead of scripts.
This module provides backward compatibility during migration.

Example:
    # Old (deprecated):
    from scripts.ontology.registry import ActionRegistry

    # New (recommended):
    from lib.oda.ontology.registry import ActionRegistry
"""
import warnings
import sys
from pathlib import Path

# Add lib to path if not present
lib_path = str(Path(__file__).parent.parent / "lib")
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)

# Emit deprecation warning on import
warnings.warn(
    "Importing from 'scripts' is deprecated. Use 'lib.oda' instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export everything from lib.oda
from lib.oda import *
