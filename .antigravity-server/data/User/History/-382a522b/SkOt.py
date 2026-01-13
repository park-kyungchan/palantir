"""
Unit tests for LaTeX to HWP Equation Converter
Focus: Subscripts, Superscripts, Limits, Fractions
"""
import pytest
from lib.owpml.equation_converter import latex_to_hwp

def test_frac():
    assert latex_to_hwp(r"\frac{a}{b}") == "{a} OVER {b}"
    assert latex_to_hwp(r"\frac{a+1}{b-1}") == "{a+1} OVER {b-1}"

def test_nested_frac():
    # \frac{\frac{a}{b}}{c} -> {{a} OVER {b}} OVER {c}
    assert latex_to_hwp(r"\frac{\frac{a}{b}}{c}") == "{{a} OVER {b}} OVER {c}"

def test_sqrt():
    assert latex_to_hwp(r"\sqrt{x}") == "SQRT{x}"
    assert latex_to_hwp(r"\sqrt[3]{x}") == "^{3}SQRT{x}"

def test_sum_limits():
    # \sum_{i=1}^{n} -> SUM_{i=1}^{n}
    # Converter should preserve _ and ^ and {}
    # Input \sum becomes SUM
    assert latex_to_hwp(r"\sum_{i=1}^{n} i") == "SUM_{i=1}^{n} i"
    
def test_int_limits():
    assert latex_to_hwp(r"\int_{0}^{\infty} x dx") == "INT_{0}^{inf} x dx"
    # Note: converter maps \infty -> inf

def test_greek_and_operators():
    assert latex_to_hwp(r"\alpha + \beta \times \gamma") == "alpha + beta TIMES gamma"

def test_complex_equation():
    # Quadratic formula: x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}
    latex = r"x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}"
    expected = "x = {-b PLUSMINUS SQRT{b^2 - 4ac}} OVER {2a}"
    # Note: converter replaces \pm with PLUSMINUS, \sqrt with SQRT
    # b^2 should be preserved as b^2
    assert latex_to_hwp(latex) == expected

if __name__ == "__main__":
    test_frac()
    test_nested_frac()
    test_sqrt()
    print("All basic tests passed!")
