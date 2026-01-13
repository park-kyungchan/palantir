# HWP Equation Script Reference

This reference documents the proprietary scripting language used in Hancom HWP Equation Editor (`hp:eqEdit`). For native HWPX rendering, these scripts must be placed within `<hp:script>` tags inside an `<hp:ctrl>` block.

## 1. Core Operators

| Token | Description | Example |
|-------|-------------|---------|
| `OVER`| Fraction | `{a+b} over {a-b}` |
| `SUP` or `^` | Superscript | `a^2 + b^2` |
| `SUB` or `_` | Subscript | `a_n` |
| `SQRT`| Square root | `sqrt{x^2+1}` |
| `^nsqrt`| n-th root | `^3sqrt{x}` |
| `INT` | Integral | `int from 0 to inf` |
| `SUM` | Summation | `sum_{n=1}^N` |
| `TIMES`| Multiply (×) | `a times b` |
| `DIV` | Divide (÷) | `a div b` |
| `EQALIGN`| Alignment | Use with `&` |
| `~` | Multi-space | `a ~ b` |
| `'` | 1/4 size space | `a ' b` |
| `#` | Line break | Inside matrix or cases |
| `PILE` | Center pile | `pile {a # b}` |
| `LPILE` | Left-aligned pile | `lpile {a # b}` |
| `RPILE` | Right-aligned pile | `rpile {a # b}` |
| `CHOOSE`| Combination | `n choose k` |
| `BINOM` | Binomial coeff | `binom n k` |
| `BIGG`  | Enlarged bracket | `bigg /` |

## 2. Brackets and Scoping

HWP uses specific commands for dynamic bracket sizing:
- **Scoping**: Use `{ }` to group multiple terms for an operator (e.g., `{a+b} OVER c`).
- **Dynamic Sizing**:
  - `LEFT( ... RIGHT)`: Automatically scales parentheses to content height.
  - `LEFT{ ... RIGHT.`: Scales a left brace (leaving the right side open).

## 3. Matrix and Lists

| Command | Description |
|---------|-------------|
| `MATRIX`| General matrix |
| `BMATRIX`| Matrix with `[ ]` |
| `PMATRIX`| Matrix with `( )` |
| `DMATRIX`| Matrix with `| |` |
| `CASES`  | Conditional braces |

**Pattern**: `MATRIX { a & b # c & d }`
- `&` separates columns.
- `#` separates rows.

## 4. Special Symbols

- **Greek Letters**: `Alpha`, `Beta`, `Gamma`, `Delta`, `pi`, `theta` (Capitalized for uppercase).
- **Arrows**: `->` or `rarrow`, `<-` or `larrow`, `<->` or `lrarrow`, `=>` or `RARROW`.
- **Calculus**: `lim`, `Lim` (case sensitive: _lim_ for inline, _Lim_ for large), `partial`, `inf`.
- **Set Theory**: `in`, `notin`, `subset`, `union`, `inter`, `exists`, `forall`.
- **Logic**: `therefore`, `because`, `neq` or `!=`, `approx`, `cong`.

## 5. HWPX XML Integration Example

```xml
<hp:ctrl>
  <hp:eqEdit version="2" baseLine="850">
    <hp:script>
      int from 0 to 3 `^3sqrt{x^2 +1}dx
    </hp:script>
  </hp:eqEdit>
</hp:ctrl>
```
