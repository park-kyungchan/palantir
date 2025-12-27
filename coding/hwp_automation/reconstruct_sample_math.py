
import os
import json
import logging
from core_bridge import WSLBridge
from lib.models import (
    Open, InsertText, FileSaveAs, 
    SetFontSize, SetFontBold, SetAlign, 
    SetLineSpacing, MultiColumn, InsertEquation,
    SetLetterSpacing
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MathReconstructor")

def decode_pua(text):
    """
    Maps Private Use Area characters found in sample.pdf to standard characters.
    Derived from analysis of 'x^2 + x - 1 = 0' patterns.
    """
    mapping = {
        # Numbers
        "": "0", "": "1", "": "2", "": "3", "": "4",
        "": "5", "": "6", "": "7", "": "8", "": "9",
        # Variables
        "": "x", "": "y", "": "a", "": "b", "": "n",
        # Operators
        "": "+", "": "-", "": "=", "": "/", # Fraction bar often indicates division or fraction context
        "": "sqrt", # Radical
        "": "(", "": ")",
        # Exponents (Superscripts seem to be just position in PDF, 
        # but pure text extraction might flatten them. 
        # We need logic to wrap them if possible, or just output clean text)
    }
    
    for k, v in mapping.items():
        text = text.replace(k, v)
    return text

def format_equation(text):
    """
    Simple heuristic to convert math-heavy lines to HWP Equation Script.
    """
    # If explicit math symbols exist, treat as Equation
    if any(c in text for c in ["=", "+", "-", "sqrt", "^"]):
        # Cleanup for HWP Script
        # HWP Eq uses "ROOT {..}" for sqrt, or "sqrt {..}"
        # It uses "^2" for superscripts.
        # Our extraction flattened "x 2" -> "x2"? 
        # From analysis: "x^2" came out as "x 2" or "x2"?
        # Actually in the log: "" (x2). So we need to infer exponents.
        # Heuristic: "x" followed by number -> x^number (for this specific worksheet context)
        text = text.replace("x2", "x^2").replace("x3", "x^3").replace("x4", "x^4").replace("x5", "x^5")
        text = text.replace("y2", "y^2").replace("y3", "y^3").replace("y4", "y^4").replace("a2", "a^2").replace("b2", "b^2")
        
        # Fractions: "1 / (2n - 1)" logic?
        # The PDF had "over" layout. Text extraction "over" is usually just newline or specific char.
        # Let's simple-case standard polynomial equations.
        return text
    return None

def main():
    bridge = WSLBridge()
    
    # Raw extracted items (representative selection from Page 1 analysis)
    # We reconstruct the layout: 2 Columns.
    
    actions = []
    
    # 1. Document Setup
    actions.append(SetLineSpacing(spacing=180)) # Airy layout for math
    actions.append(MultiColumn(count=2, same_size=True, gap=3000))
    actions.append(SetFontSize(size=15.0))
    actions.append(SetFontBold(is_bold=True))
    actions.append(InsertText(text="1. 다항식의 연산\n\n"))
    
    # 2. Problems
    problems = [
        ("4.", "x^2 + x - 1 = 0일 때, 다음 식의 값을 구하시오."),
        ("(1)", "(x+2)(x-1)(x+4)(x-3) + 5"),
        ("(2)", "x^5 - 5x"), # Simplified for demo
        ("5.", "다음을 만족시키는 n의 값을 구하시오."),
        ("Equation", "(2^2+1)(2^4+1)(2^8+1)(2^16+1)(2^32+1) = 1/(2^n - 1) * 64"), # Interpreted from log logic
        ("6.", "다음 다항식의 전개식에서 모든 계수의 합을 구하시오."),
        ("Equation", "1 + (1+x) + (1+x+x^2)^2 + ... + (1+x+...+x^4)^4"),
        ("8.", "a + b = 4, ab = 2일 때, 다음 식의 값을 구하시오. (단, a >= b)"),
        ("(1)", "a - b"),
        ("(2)", "a^2 - b^2"),
        ("(3)", "a^3 - b^3"),
        ("9.", "x + y = 1, x^3 + y^3 = 19일 때, 다음 식의 값을 구하시오."),
        ("(1)", "xy"),
        ("(2)", "x^2 + y^2")
    ]
    
    for label, content in problems:
        if label == "Equation":
            # Pure Equation Line
            actions.append(InsertEquation(script=content))
            actions.append(InsertText(text="\n"))
        elif label.startswith("("):
            # Sub-problem
            actions.append(SetFontSize(size=11.0))
            actions.append(InsertText(text=f"   {label} "))
            # Check if content needs Eq
            if any(x in content for x in ["^", "=", "+"]):
                actions.append(InsertEquation(script=content))
            else:
                actions.append(InsertText(text=content))
            actions.append(InsertText(text="\n"))
        else:
            # Main Problem number
            actions.append(SetFontSize(size=12.0))
            actions.append(SetFontBold(is_bold=True))
            actions.append(InsertText(text=f"\n{label} "))
            actions.append(SetFontBold(is_bold=False))
            # Split content: Mixed Text + Math
            # "x^2... = 0일 때" -> Eq(x^2...=0) + Text(일 때...)
            # For simplicity, if simple, just Text, if complex, Eq.
            # Here we wrap the initial formula in Eq if present
            if "일 때" in content:
                parts = content.split("일 때")
                formula = parts[0].strip()
                rest = "일 때" + parts[1]
                actions.append(InsertEquation(script=formula))
                actions.append(InsertText(text=f" {rest}\n"))
            else:
                actions.append(InsertText(text=content + "\n"))

    # 4. Save
    output_path = "C:\\Temp\\sample_math_reconstructed.hwpx"
    actions.append(FileSaveAs(path=output_path, format="HWPX"))
    
    # Payload
    payload_path = os.path.abspath("math_reconstruct_payload.json")
    payload_data = [action.model_dump() for action in actions]
    
    with open(payload_path, "w", encoding="utf-8") as f:
        json.dump(payload_data, f, indent=2, ensure_ascii=False)
        
    logger.info(f"Payload ready: {payload_path}")
    
    # Execute
    logger.info("--- Executing Math Reconstruction ---")
    script_path = os.path.abspath("executor_win.py")
    return_code = bridge.run_python_script(script_path, payload_path)
    
    if return_code == 0:
        logger.info(f"Success! Output at: {output_path}")
    else:
        logger.error(f"Failed with code {return_code}")

if __name__ == "__main__":
    main()
