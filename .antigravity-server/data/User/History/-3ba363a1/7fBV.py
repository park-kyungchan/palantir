"""
HwpUnit Conversion Utilities

HWPX uses HwpUnit (1/7200 inch) as the base unit for all dimensions.
This module provides conversion functions between HwpUnit and common units.

Reference: KS X 6101 / hwpx_progrmmatic.md (Line 155-167)

Conversion constants:
- 1 HwpUnit = 1/7200 inch ≈ 0.00353mm
- 7200 HwpUnit = 1 inch = 25.4mm = 72pt
- 100 HwpUnit = 1pt
- 283.46 HwpUnit ≈ 1mm
"""

from typing import Union

# Conversion constants
HWPUNIT_PER_INCH = 7200
HWPUNIT_PER_PT = 100
HWPUNIT_PER_MM = 283.46457  # 7200 / 25.4


def mm_to_hwpunit(mm: Union[int, float]) -> int:
    """
    Convert millimeters to HwpUnit.
    
    Args:
        mm: Value in millimeters
        
    Returns:
        Value in HwpUnit (rounded to integer)
        
    Example:
        >>> mm_to_hwpunit(1)
        283
        >>> mm_to_hwpunit(25.4)  # 1 inch
        7200
    """
    return round(mm * HWPUNIT_PER_MM)


def hwpunit_to_mm(hwpunit: int) -> float:
    """
    Convert HwpUnit to millimeters.
    
    Args:
        hwpunit: Value in HwpUnit
        
    Returns:
        Value in millimeters
        
    Example:
        >>> hwpunit_to_mm(7200)
        25.4
    """
    return hwpunit / HWPUNIT_PER_MM


def pt_to_hwpunit(pt: Union[int, float]) -> int:
    """
    Convert points to HwpUnit.
    
    Args:
        pt: Value in points (1pt = 1/72 inch)
        
    Returns:
        Value in HwpUnit
        
    Example:
        >>> pt_to_hwpunit(10)
        1000
        >>> pt_to_hwpunit(12)
        1200
    """
    return round(pt * HWPUNIT_PER_PT)


def hwpunit_to_pt(hwpunit: int) -> float:
    """
    Convert HwpUnit to points.
    
    Args:
        hwpunit: Value in HwpUnit
        
    Returns:
        Value in points
        
    Example:
        >>> hwpunit_to_pt(1000)
        10.0
    """
    return hwpunit / HWPUNIT_PER_PT


def inch_to_hwpunit(inch: Union[int, float]) -> int:
    """
    Convert inches to HwpUnit.
    
    Args:
        inch: Value in inches
        
    Returns:
        Value in HwpUnit
        
    Example:
        >>> inch_to_hwpunit(1)
        7200
    """
    return round(inch * HWPUNIT_PER_INCH)


def hwpunit_to_inch(hwpunit: int) -> float:
    """
    Convert HwpUnit to inches.
    
    Args:
        hwpunit: Value in HwpUnit
        
    Returns:
        Value in inches
        
    Example:
        >>> hwpunit_to_inch(7200)
        1.0
    """
    return hwpunit / HWPUNIT_PER_INCH


def px_to_hwpunit(px: int, dpi: int = 96) -> int:
    """
    Convert pixels to HwpUnit at given DPI.
    
    Args:
        px: Value in pixels
        dpi: Screen resolution (default 96 DPI)
        
    Returns:
        Value in HwpUnit
        
    Example:
        >>> px_to_hwpunit(96, dpi=96)  # 1 inch at 96 DPI
        7200
    """
    inches = px / dpi
    return inch_to_hwpunit(inches)


def hwpunit_to_px(hwpunit: int, dpi: int = 96) -> int:
    """
    Convert HwpUnit to pixels at given DPI.
    
    Args:
        hwpunit: Value in HwpUnit
        dpi: Screen resolution (default 96 DPI)
        
    Returns:
        Value in pixels (rounded)
        
    Example:
        >>> hwpunit_to_px(7200, dpi=96)
        96
    """
    inches = hwpunit_to_inch(hwpunit)
    return round(inches * dpi)
