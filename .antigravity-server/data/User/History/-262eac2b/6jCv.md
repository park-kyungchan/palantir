# LaTeX to HWP Equation Conversion Rules

The pipeline includes a dedicated `LatexToHwpConverter` (`lib/owpml/equation_converter.py`) to translate standard LaTeX math notation into the proprietary Hancom Office equation script format.

## 1. Core Conversion Logic
The converter handles structural differences through regex-based pattern matching and recursion for nested elements.

### 1.1 Fractions
- **LaTeX**: `\frac{a}{b}` or `\dfrac{a}{b}`
- **HWP**: `{a} OVER {b}`
- **Logic**: Iterative regex replacement to handle nested fractions.

### 1.2 Roots
- **LaTeX**: `\sqrt{x}` -> **HWP**: `SQRT{x}`
- **LaTeX**: `\sqrt[n]{x}` -> **HWP**: `^n SQRT{x}`

### 1.3 Delimiters
Automatically translates `\left` and `\right` brackets into HWP's `LEFT` and `RIGHT` modifiers:
- `\left(` -> `LEFT(`
- `\right]` -> `RIGHT]`
- `\left|` -> `LEFT|`

## 2. Command Mapping Table
| Entity Type | LaTeX Command | HWP Script Equivalent |
|---|---|---|
| **Operators** | `\times`, `\div`, `\pm` | `TIMES`, `DIV`, `PLUSMINUS` |
| **Logic/Sets** | `\forall`, `\exists`, `\in` | `FORALL`, `EXIST`, `IN` |
| **Arrows** | `\rightarrow`, `\Rightarrow` | `rarrow`, `RARROW` |
| **Integrals** | `\int`, `\iint`, `\sum` | `INT`, `DINT`, `SUM` |
| **Greek (Lower)**| `\alpha`, `\beta`, `\gamma` | `alpha`, `beta`, `gamma` |
| **Greek (Upper)**| `\Gamma`, `\Delta`, `\Phi` | `Gamma`, `Delta`, `Phi` |

## 3. Accents & Decorators
Handled via `DECORATOR_MAP`:
- `\hat{x}` -> `hat x`
- `\bar{x}` -> `bar x`
- `\vec{x}` -> `vec x`
- `\overline{x}` -> `bar x`

## 4. OWPML Integration
The resulting HWP script is wrapped in the `<hp:eqEdit>` structure within the HWPX package:
```xml
<hp:eqEdit numberingType="EQUATION" version="2" baseLine="BASE">
    <hp:script>... HWP Script ...</hp:script>
</hp:eqEdit>
```
*Note: `linesegarray` is intentionally omitted to allow the HWPX viewer to auto-calculate the layout, avoiding render artifacts.*
