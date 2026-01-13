# HWPX Native: OWPML & Spec Compliance (KS X 6101)

This document outlines the requirements and implementation details for generating native HWPX (XML) files that are 100% compatible with Hancom Office 2024.

## 1. Specification Compliance
All XML construction follows the **KS X 6101** national standard. We avoid "simulated" formatting and instead use native OWPML elements.

### 1.1 HwpUnit Conversion Formulas
**1 HwpUnit = 1/7200 inch** (approx. 0.00353mm).

| Conversion | Formula | Example |
|---|---|---|
| HwpUnit → pt | `pt = hwpunit / 100` | 1000 HwpUnit = 10pt |
| HwpUnit → mm | `mm = hwpunit / 283.46` | 283 HwpUnit ≈ 1mm |
| pt → HwpUnit | `hwpunit = pt * 100` | 12pt = 1200 HwpUnit |
| mm → HwpUnit | `hwpunit = mm * 283.46` | 25.4mm = 7200 HwpUnit |

## 2. Template-Based Reconstruction (TBR)
Due to the OWPML header's extreme complexity (IDs for fonts, styles, borders), the engine uses a "Golden Template".
- **Source**: `Skeleton.hwpx` (official base).
- **Process**: Copy all ZIP parts except `Contents/section0.xml`.
- **Dynamic Content**: Inject generated paragraph and run data into `section0.xml`.

## 3. Control Elements (`hp:ctrl`)
Critical layout and mathematical objects are **Controls**, not attributes.
- **Columns (`hp:colPr`)**: Must be inserted after `<hp:secPr>` in the first run of a section. Use attributes `colCount`, `type="NEWSPAPER"`, `sameSz="1"`, and `sameGap`.
- **Equations (`hp:eqEdit`)**: Requires transpilation from LaTeX -> HWP Script -> `<hp:eqEdit>` (see Section 4).
- **Tables (`hp:tbl`)**: Hierarchical structure with `<hp:tr>` (rows) and `<hp:tc>` (cells).

### 3.1 Table Merge Logic (KS X 6101)
Cell merging is handled by the `<hp:cellSpan>` child element within `<hp:tc>`, not by attributes on the cell itself.

```xml
<hp:tc>
  <hp:cellAddr colAddr="0" rowAddr="0"/>
  <hp:cellSpan colSpan="2" rowSpan="3"/>
</hp:tc>
```

**Key Requirement**: HWPX does not allow "ghost cells" in merged regions. If cells are merged, the number of `<hp:tc>` elements in the row decreases. Logical coordinates must be tracked via `cellAddr`.

## 4. HWP Equation Script Reference
proprietary scripting syntax used in `<hp:script>` tags.

| Token | Description | Example |
|---|---|---|
| `OVER` | Fraction | `{a+b} over {a-b}` |
| `SQRT` | Square root | `sqrt{x^2+1}` |
| `^` / `_` | Sup / Sub | `x^2 + a_n` |
| `LEFT(` | Dynamic Paren | `LEFT( x RIGHT)` |
| `MATRIX` | Grid | `MATRIX { a & b # c & d }` |

## 5. Generator Implementation Details
The `HWPGenerator` (`lib/owpml/generator.py`) handles:
1. **Namespace Mapping**: Registers OWPML namespaces (ha, hp, hs, hc, etc.).
2. **Body Construction**: Manually builds XML strings for stability, ensuring `secPr` and `colPr` are placed in the first paragraph.
3. **ID Management**: Synchronizes paragraph shapes (`paraPrIDRef`) with the template's header.

## 6. Stability Checklist
- **Mimetype**: Must be `Stored` (uncompressed) as the first file in the ZIP.
- **Root Links**: `META-INF/container.rdf` must link ZIP parts to their OWPML roles.
- **Lineseg**: Every paragraph must have a skeletal `<hp:linesegarray>` for renderer stability.
