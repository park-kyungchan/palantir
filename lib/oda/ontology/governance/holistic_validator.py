"""
ODA V3.0 - Holistic Validator
==============================

Validates architectural compliance at module level.
Ensures Clean Architecture principles are enforced.
"""

from __future__ import annotations

import ast
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set

from lib.oda.ontology.governance.violations import (
    Violation,
    ViolationReport,
    ViolationSeverity,
    ViolationType,
)

logger = logging.getLogger(__name__)


class HolisticValidator:
    """
    Validates architectural compliance across the ODA codebase.
    
    Enforces:
    1. Clean Architecture layer direction (Domain -> App -> Infra)
    2. No forbidden imports
    3. Module boundary respect
    """
    
    # Layer hierarchy (lower can import from higher)
    LAYER_HIERARCHY = {
        "domain": 0,      # ontology/, cognitive/
        "application": 1,  # runtime/, simulation/
        "infrastructure": 2,  # relay/, observe/, api/
    }
    
    # Module to layer mapping
    MODULE_LAYERS: Dict[str, str] = {
        "ontology": "domain",
        "cognitive": "domain",
        "aip_logic": "domain",
        "runtime": "application",
        "simulation": "application",
        "relay": "infrastructure",
        "observe": "infrastructure",
        "api": "infrastructure",
        "tools": "infrastructure",
        "data": "infrastructure",
        "osdk": "application",
        "llm": "infrastructure",
    }
    
    # Allowed exceptions (e.g., type imports)
    ALLOWED_VIOLATIONS = {
        ("domain", "infrastructure", "TYPE_CHECKING"),  # typing imports OK
    }
    
    @classmethod
    def validate_module(
        cls,
        module_path: Path,
        strict: bool = False
    ) -> ViolationReport:
        """
        Validate a Python module for architectural compliance.
        
        Args:
            module_path: Path to the Python file
            strict: If True, warnings become errors
            
        Returns:
            ViolationReport with violations
        """
        report = ViolationReport(target=str(module_path))
        
        if not module_path.exists() or module_path.suffix != '.py':
            return report
        
        try:
            source = module_path.read_text()
            tree = ast.parse(source)
            
            # Determine this module's layer
            source_layer = cls._get_layer_for_path(module_path)
            if not source_layer:
                return report
            
            # Check all imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        cls._check_import(
                            source_layer,
                            alias.name,
                            module_path,
                            report,
                            strict
                        )
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        cls._check_import(
                            source_layer,
                            node.module,
                            module_path,
                            report,
                            strict,
                            is_type_checking=cls._is_in_type_checking(node, tree)
                        )
        except SyntaxError as e:
            logger.warning(f"Could not parse {module_path}: {e}")
        except Exception as e:
            logger.debug(f"Error validating {module_path}: {e}")
        
        return report
    
    @classmethod
    def _get_layer_for_path(cls, path: Path) -> Optional[str]:
        """Determine which layer a file belongs to."""
        parts = path.parts
        for part in parts:
            if part in cls.MODULE_LAYERS:
                return cls.MODULE_LAYERS[part]
        return None
    
    @classmethod
    def _check_import(
        cls,
        source_layer: str,
        import_path: str,
        file_path: Path,
        report: ViolationReport,
        strict: bool,
        is_type_checking: bool = False
    ) -> None:
        """Check if an import violates layer boundaries."""
        # Only check scripts.* imports
        if not import_path.startswith("scripts."):
            return
        
        # Extract module name
        parts = import_path.split(".")
        if len(parts) < 2:
            return
        
        target_module = parts[1]
        target_layer = cls.MODULE_LAYERS.get(target_module)
        
        if not target_layer:
            return
        
        source_level = cls.LAYER_HIERARCHY.get(source_layer, 0)
        target_level = cls.LAYER_HIERARCHY.get(target_layer, 0)
        
        # Check: Higher layers should not import from lower layers
        # Domain (0) should not import from Infrastructure (2)
        if target_level > source_level:
            # Check allowed exceptions
            if is_type_checking and (source_layer, target_layer, "TYPE_CHECKING") in cls.ALLOWED_VIOLATIONS:
                return
            
            report.add(Violation(
                type=ViolationType.LAYER_VIOLATION,
                severity=ViolationSeverity.ERROR if strict else ViolationSeverity.WARNING,
                location=str(file_path),
                message=f"Layer violation: {source_layer} imports from {target_layer} ({import_path})",
                suggestion=f"Move shared code to a higher layer or use dependency injection",
                metadata={"from": source_layer, "to": target_layer, "import": import_path}
            ))
    
    @classmethod
    def _is_in_type_checking(cls, node: ast.ImportFrom, tree: ast.Module) -> bool:
        """Check if import is inside TYPE_CHECKING block."""
        for top_node in ast.walk(tree):
            if isinstance(top_node, ast.If):
                # Check if this is a TYPE_CHECKING guard
                if isinstance(top_node.test, ast.Name) and top_node.test.id == "TYPE_CHECKING":
                    for child in ast.walk(top_node):
                        if child is node:
                            return True
        return False
    
    @classmethod
    def validate_directory(
        cls,
        directory: Path,
        strict: bool = False
    ) -> ViolationReport:
        """
        Validate all Python files in a directory.
        
        Args:
            directory: Directory to validate
            strict: If True, warnings become errors
            
        Returns:
            Merged ViolationReport for all files
        """
        report = ViolationReport(target=str(directory))
        
        for py_file in directory.rglob("*.py"):
            if "__pycache__" in str(py_file) or ".venv" in str(py_file):
                continue
            
            file_report = cls.validate_module(py_file, strict)
            report.merge(file_report)
        
        return report
