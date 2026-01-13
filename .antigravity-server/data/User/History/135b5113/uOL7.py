"""
LaTeX to HWP Equation Script Converter

Converts LaTeX math notation to Hancom Office equation script format.
Based on HWP Equation Specification (한글문서파일형식_수식_revision1.3.pdf)

Key differences:
- LaTeX: \frac{a}{b}  →  HWP: {a} OVER {b}
- LaTeX: \sqrt{x}     →  HWP: SQRT{x}
- LaTeX: \sum_{i}^{n} →  HWP: SUM_{i}^{n}
- LaTeX: \int_a^b     →  HWP: INT_a^b
"""

import re
from typing import Tuple, List


class LatexToHwpConverter:
    """Converts LaTeX math expressions to HWP equation script."""
    
    # LaTeX command to HWP command mapping
    COMMAND_MAP = {
        # Fractions
        r'\\frac': 'OVER',
        r'\\dfrac': 'OVER',
        r'\\tfrac': 'OVER',
        
        # Roots
        r'\\sqrt': 'SQRT',
        
        # Sums and products
        r'\\sum': 'SUM',
        r'\\prod': 'PROD',
        r'\\coprod': 'COPROD',
        
        # Integrals
        r'\\int': 'INT',
        r'\\oint': 'OINT',
        r'\\iint': 'DINT',
        r'\\iiint': 'TINT',
        
        # Limits
        r'\\lim': 'lim',
        r'\\limsup': 'limsup',
        r'\\liminf': 'liminf',
        
        # Greek letters (lowercase)
        r'\\alpha': 'alpha',
        r'\\beta': 'beta',
        r'\\gamma': 'gamma',
        r'\\delta': 'delta',
        r'\\epsilon': 'epsilon',
        r'\\varepsilon': 'varepsilon',
        r'\\zeta': 'zeta',
        r'\\eta': 'eta',
        r'\\theta': 'theta',
        r'\\vartheta': 'vartheta',
        r'\\iota': 'iota',
        r'\\kappa': 'kappa',
        r'\\lambda': 'lambda',
        r'\\mu': 'mu',
        r'\\nu': 'nu',
        r'\\xi': 'xi',
        r'\\pi': 'pi',
        r'\\varpi': 'varpi',
        r'\\rho': 'rho',
        r'\\sigma': 'sigma',
        r'\\varsigma': 'varsigma',
        r'\\tau': 'tau',
        r'\\upsilon': 'upsilon',
        r'\\phi': 'phi',
        r'\\varphi': 'varphi',
        r'\\chi': 'chi',
        r'\\psi': 'psi',
        r'\\omega': 'omega',
        
        # Greek letters (uppercase)
        r'\\Gamma': 'Gamma',
        r'\\Delta': 'Delta',
        r'\\Theta': 'Theta',
        r'\\Lambda': 'Lambda',
        r'\\Xi': 'Xi',
        r'\\Pi': 'Pi',
        r'\\Sigma': 'Sigma',
        r'\\Upsilon': 'Upsilon',
        r'\\Phi': 'Phi',
        r'\\Psi': 'Psi',
        r'\\Omega': 'Omega',
        
        # Operators
        r'\\times': 'TIMES',
        r'\\div': 'DIV',
        r'\\pm': 'PLUSMINUS',
        r'\\mp': 'MINUSPLUS',
        r'\\cdot': '*',
        
        # Comparisons
        r'\\leq': 'LEQ',
        r'\\le': 'LEQ',
        r'\\geq': 'GEQ',
        r'\\ge': 'GEQ',
        r'\\neq': 'neq',
        r'\\ne': 'neq',
        r'\\approx': 'APPROX',
        r'\\equiv': 'EQUIV',
        r'\\sim': 'SIM',
        
        # Arrows
        r'\\rightarrow': 'rarrow',
        r'\\to': '->',
        r'\\leftarrow': 'larrow',
        r'\\leftrightarrow': 'lrarrow',
        r'\\Rightarrow': 'RARROW',
        r'\\Leftarrow': 'LARROW',
        
        # Sets
        r'\\in': 'IN',
        r'\\notin': 'notin',
        r'\\subset': 'SUBSET',
        r'\\supset': 'SUPSET',
        r'\\subseteq': 'SUBSETEQ',
        r'\\supseteq': 'SUPSETEQ',
        r'\\cup': 'UNION',
        r'\\cap': 'INTER',
        r'\\emptyset': 'EMPTYSET',
        
        # Logic
        r'\\forall': 'FORALL',
        r'\\exists': 'EXIST',
        r'\\neg': 'LNOT',
        r'\\land': 'WEDGE',
        r'\\lor': 'VEE',
        
        # Special
        r'\\infty': 'inf',
        r'\\partial': 'PARTIAL',
        r'\\nabla': 'TRIANGLE',
        r'\\circ': 'CIRC',
        r'\\cdots': 'cdots',
        r'\\ldots': 'LDOTS',
        r'\\vdots': 'VDOTS',
        r'\\ddots': 'DDOTS',
    }
    
    # Decorators (accents)
    DECORATOR_MAP = {
        r'\\hat': 'hat',
        r'\\bar': 'bar',
        r'\\vec': 'vec',
        r'\\dot': 'dot',
        r'\\ddot': 'ddot',
        r'\\tilde': 'tilde',
        r'\\overline': 'bar',
        r'\\underline': 'under',
    }
    
    def convert(self, latex: str) -> str:
        """
        Convert LaTeX expression to HWP equation script.
        
        Args:
            latex: LaTeX math expression
            
        Returns:
            HWP equation script
        """
        result = latex
        
        # Handle \frac{a}{b} -> {a} OVER {b}
        result = self._convert_frac(result)
        
        # Handle \sqrt[n]{x} -> ^n SQRT{x}
        result = self._convert_sqrt(result)
        
        # Handle \left( \right) -> LEFT( RIGHT)
        result = self._convert_delimiters(result)
        
        # Handle simple command replacements
        for latex_cmd, hwp_cmd in self.COMMAND_MAP.items():
            result = re.sub(latex_cmd + r'(?![a-zA-Z])', hwp_cmd, result)
        
        # Handle decorators \hat{x} -> hat x
        for latex_cmd, hwp_cmd in self.DECORATOR_MAP.items():
            result = re.sub(latex_cmd + r'\{([^}]+)\}', hwp_cmd + r' \1', result)
        
        # Clean up extra backslashes
        result = result.replace('\\', '')
        
        # Clean up double spaces
        result = re.sub(r'\s+', ' ', result)
        
        return result.strip()
    
    def _convert_frac(self, text: str) -> str:
        """Convert \frac{a}{b} to {a} OVER {b}"""
        pattern = r'\\(?:d|t)?frac\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}'
        
        def replacer(match):
            num = match.group(1)
            den = match.group(2)
            return f'{{{num}}} OVER {{{den}}}'
        
        # Apply multiple times for nested fractions
        prev = None
        while prev != text:
            prev = text
            text = re.sub(pattern, replacer, text)
        
        return text
    
    def _convert_sqrt(self, text: str) -> str:
        """Convert \sqrt[n]{x} to ^n SQRT{x}"""
        # Handle \sqrt[n]{x}
        text = re.sub(
            r'\\sqrt\[([^\]]+)\]\{([^}]+)\}',
            r'^{\1}SQRT{\2}',
            text
        )
        # Handle \sqrt{x}
        text = re.sub(r'\\sqrt\{([^}]+)\}', r'SQRT{\1}', text)
        return text
    
    def _convert_delimiters(self, text: str) -> str:
        """Convert \left( \right) to LEFT( RIGHT)"""
        text = re.sub(r'\\left\s*\(', 'LEFT(', text)
        text = re.sub(r'\\right\s*\)', 'RIGHT)', text)
        text = re.sub(r'\\left\s*\[', 'LEFT[', text)
        text = re.sub(r'\\right\s*\]', 'RIGHT]', text)
        text = re.sub(r'\\left\s*\{', 'LEFT{', text)
        text = re.sub(r'\\right\s*\}', 'RIGHT}', text)
        text = re.sub(r'\\left\s*\|', 'LEFT|', text)
        text = re.sub(r'\\right\s*\|', 'RIGHT|', text)
        return text


# Singleton instance
_converter = LatexToHwpConverter()


def latex_to_hwp(latex: str) -> str:
    """
    Convert LaTeX expression to HWP equation script.
    
    Args:
        latex: LaTeX math expression
        
    Returns:
        HWP equation script
        
    Example:
        >>> latex_to_hwp(r"\\frac{a+b}{c}")
        '{a+b} OVER {c}'
    """
    return _converter.convert(latex)
