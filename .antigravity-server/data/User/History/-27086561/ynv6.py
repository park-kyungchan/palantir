"""
Tests for OWPML Validator.

Validates the validator against existing HWPX files in the project.
"""

import pytest
import os
from pathlib import Path

from lib.owpml.validator import OWPMLValidator, validate_hwpx, ValidationError


# Get project root
PROJECT_ROOT = Path(__file__).parent.parent


class TestOWPMLValidator:
    """Test suite for OWPMLValidator."""
    
    def test_validator_init(self):
        """Test validator initialization."""
        validator = OWPMLValidator()
        assert validator.errors == []
        assert validator._header_ids == {}
    
    def test_validate_missing_file(self):
        """Test validation of non-existent file."""
        validator = OWPMLValidator()
        is_valid, errors = validator.validate('/nonexistent/file.hwpx')
        
        assert is_valid is False
        assert len(errors) == 1
        assert errors[0].level == 'error'
        assert 'not found' in errors[0].message.lower()
    
    def test_validate_skeleton_hwpx(self):
        """Test validation of Skeleton.hwpx (golden template)."""
        skeleton_path = PROJECT_ROOT / 'Skeleton.hwpx'
        
        if not skeleton_path.exists():
            pytest.skip("Skeleton.hwpx not found")
        
        validator = OWPMLValidator()
        is_valid, errors = validator.validate(str(skeleton_path))
        
        # Skeleton should be valid (it's our golden template)
        assert is_valid is True, f"Skeleton.hwpx should be valid. Errors: {errors}"
    
    def test_validate_output_pilot(self):
        """Test validation of output_pilot.hwpx (generated file)."""
        pilot_path = PROJECT_ROOT / 'output_pilot.hwpx'
        
        if not pilot_path.exists():
            pytest.skip("output_pilot.hwpx not found")
        
        validator = OWPMLValidator()
        is_valid, errors = validator.validate(str(pilot_path))
        
        # Log any warnings for debugging
        for error in errors:
            print(f"  {error}")
        
        # Generated files should at least be structurally valid
        # (may have warnings about IDRef)
        error_count = sum(1 for e in errors if e.level == 'error')
        assert error_count == 0, f"Generated file has errors: {errors}"
    
    def test_convenience_function(self):
        """Test the validate_hwpx convenience function."""
        skeleton_path = PROJECT_ROOT / 'Skeleton.hwpx'
        
        if not skeleton_path.exists():
            pytest.skip("Skeleton.hwpx not found")
        
        is_valid, messages = validate_hwpx(str(skeleton_path))
        
        assert isinstance(is_valid, bool)
        assert isinstance(messages, list)
        assert all(isinstance(m, str) for m in messages)


class TestValidationError:
    """Test ValidationError class."""
    
    def test_error_str_without_location(self):
        """Test error string formatting without location."""
        error = ValidationError('error', 'Test message')
        assert str(error) == '[ERROR] Test message'
    
    def test_error_str_with_location(self):
        """Test error string formatting with location."""
        error = ValidationError('warning', 'Test message', 'Contents/section0.xml')
        assert str(error) == '[WARNING] [Contents/section0.xml] Test message'
    
    def test_error_levels(self):
        """Test different error levels."""
        for level in ['error', 'warning', 'info']:
            error = ValidationError(level, 'Test')
            assert error.level == level


class TestAllOutputFiles:
    """Validate all output*.hwpx files in the project."""
    
    def test_all_output_files(self):
        """Validate all generated HWPX files."""
        output_files = list(PROJECT_ROOT.glob('output*.hwpx'))
        
        if not output_files:
            pytest.skip("No output*.hwpx files found")
        
        results = []
        for hwpx_file in output_files:
            validator = OWPMLValidator()
            is_valid, errors = validator.validate(str(hwpx_file))
            error_count = sum(1 for e in errors if e.level == 'error')
            warning_count = sum(1 for e in errors if e.level == 'warning')
            results.append({
                'file': hwpx_file.name,
                'valid': is_valid,
                'errors': error_count,
                'warnings': warning_count
            })
        
        # Print summary
        print("\n=== Validation Summary ===")
        for r in results:
            status = "✓" if r['valid'] else "✗"
            print(f"  {status} {r['file']}: {r['errors']} errors, {r['warnings']} warnings")
        
        # All files should be structurally valid (no hard errors)
        failed = [r for r in results if not r['valid']]
        assert len(failed) == 0, f"Files with errors: {[f['file'] for f in failed]}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
