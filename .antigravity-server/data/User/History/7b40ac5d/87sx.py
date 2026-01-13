"""Unit tests for HwpUnit conversion utilities."""

import pytest
from lib.owpml.units import (
    mm_to_hwpunit, hwpunit_to_mm,
    pt_to_hwpunit, hwpunit_to_pt,
    inch_to_hwpunit, hwpunit_to_inch,
    px_to_hwpunit, hwpunit_to_px,
    HWPUNIT_PER_INCH, HWPUNIT_PER_PT, HWPUNIT_PER_MM
)


class TestConstants:
    """Test conversion constants."""
    
    def test_hwpunit_per_inch(self):
        assert HWPUNIT_PER_INCH == 7200
    
    def test_hwpunit_per_pt(self):
        assert HWPUNIT_PER_PT == 100
    
    def test_hwpunit_per_mm_approx(self):
        # 7200 / 25.4 ≈ 283.46
        assert abs(HWPUNIT_PER_MM - 283.46) < 0.01


class TestMillimeterConversion:
    """Test mm <-> HwpUnit conversion."""
    
    def test_1mm_to_hwpunit(self):
        assert mm_to_hwpunit(1) == 283
    
    def test_25_4mm_to_hwpunit(self):
        # 25.4mm = 1 inch = 7200 HwpUnit
        assert mm_to_hwpunit(25.4) == 7200
    
    def test_hwpunit_to_mm_roundtrip(self):
        original = 10.0  # mm
        hwpunit = mm_to_hwpunit(original)
        result = hwpunit_to_mm(hwpunit)
        assert abs(result - original) < 0.01


class TestPointConversion:
    """Test pt <-> HwpUnit conversion."""
    
    def test_10pt_to_hwpunit(self):
        assert pt_to_hwpunit(10) == 1000
    
    def test_12pt_to_hwpunit(self):
        assert pt_to_hwpunit(12) == 1200
    
    def test_hwpunit_to_pt_1000(self):
        assert hwpunit_to_pt(1000) == 10.0
    
    def test_pt_roundtrip(self):
        original = 14.5
        hwpunit = pt_to_hwpunit(original)
        result = hwpunit_to_pt(hwpunit)
        assert abs(result - original) < 0.01


class TestInchConversion:
    """Test inch <-> HwpUnit conversion."""
    
    def test_1inch_to_hwpunit(self):
        assert inch_to_hwpunit(1) == 7200
    
    def test_hwpunit_to_inch_7200(self):
        assert hwpunit_to_inch(7200) == 1.0
    
    def test_inch_roundtrip(self):
        original = 2.5
        hwpunit = inch_to_hwpunit(original)
        result = hwpunit_to_inch(hwpunit)
        assert abs(result - original) < 0.001


class TestPixelConversion:
    """Test px <-> HwpUnit conversion."""
    
    def test_96px_at_96dpi(self):
        # 96px at 96 DPI = 1 inch = 7200 HwpUnit
        assert px_to_hwpunit(96, dpi=96) == 7200
    
    def test_hwpunit_to_px_7200_at_96dpi(self):
        assert hwpunit_to_px(7200, dpi=96) == 96
    
    def test_px_at_72dpi(self):
        # 72px at 72 DPI = 1 inch = 7200 HwpUnit
        assert px_to_hwpunit(72, dpi=72) == 7200


class TestEdgeCases:
    """Test edge cases."""
    
    def test_zero_values(self):
        assert mm_to_hwpunit(0) == 0
        assert pt_to_hwpunit(0) == 0
        assert inch_to_hwpunit(0) == 0
    
    def test_negative_values(self):
        assert mm_to_hwpunit(-10) == -2835
    
    def test_float_precision(self):
        # Small values should still work
        result = mm_to_hwpunit(0.1)
        assert result == 28  # ~28.3
