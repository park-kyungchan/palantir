# Equation Implementation Logic (Phase 7)

## 1. Overview
HWPX equations utilize a proprietary script format ("HWP Equation Script") embedded within a `<hp:eqEdit>` control. Conversion from common formats like LaTeX is required for scientific document reconstruction.

## 2. LaTeX to HWP Script Conversion
Conversion is handled by `lib/owpml/equation_converter.py` using a pattern-matching approach for the Hancom Office equation specification (Revision 1.3).

### 2.1 Mapping Examples
| LaTeX | HWP Equation Script |
| :--- | :--- |
| `\frac{a}{b}` | `{a} OVER {b}` |
| `\sqrt{x}` | `SQRT{x}` |
| `\sum_{i=1}^{n}` | `SUM_{i=1}^{n}` |
| `\alpha` | `alpha` |
| `\int` | `INT` |

### 2.2 Nested Structure Handling
The converter handles nested fractions via recursive application of regex patterns to ensure complex expressions like `\frac{\frac{a}{b}}{c}` are correctly transformed to `{{a} OVER {b}} OVER {c}`.

## 3. OWPML Structure (`hp:eqEdit`)
Equations are hosted within a `<hp:ctrl>` inside a `<hp:run>`.

```xml
<hp:p id="...">
  <hp:run charPrIDRef="0">
    <hp:ctrl>
      <hp:eqEdit version="2" baseLine="BOTTOM" textColor="#000000" baseUnit="PUNKT">
        <hp:script>{a} OVER {b}</hp:script>
      </hp:eqEdit>
    </hp:ctrl>
  </hp:run>
</hp:p>
```

### 3.1 Properties
- **version**: Usually "2".
- **baseLine**: Defines vertical alignment (e.g., "BOTTOM").
- **baseUnit**: Typically "PUNKT" (points).
- **textColor**: Hex color representation.

## 4. Integration Challenges
- **Line Segments**: Equations often require accurate `<hp:lineseg>` entries in the parent paragraph's `<hp:linesegarray>` to ensure proper rendering in viewers. Current implementation uses a placeholder with `42520` (full width) units.
- **Unsupported Commands**: Commands like `\begin{align}` or `\matrix` require specific script mappings (`MATRIX` in HWP) that are currently under-researched.

## 5. Preliminary Research Findings (January 2026)
- **Script Syntax**: HWP script is whitespace-sensitive and case-insensitive for some commands but sensitive for others.
- **Character Encoding**: The `<hp:script>` content must be plain text with entities escaped if necessary, though most math characters are ASCII-translatable in the script format.
