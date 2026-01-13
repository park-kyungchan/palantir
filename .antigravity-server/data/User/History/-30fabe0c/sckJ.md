# KS X 6101 Native Capabilities Integration

The transition from win32com automation to Linux-native HWPX generation requires a shift from "Application-Guided" manipulation to "Spec-Compliant" XML construction. As identified in Phase 12, simple paragraph flags are insufficient for complex Hancom Office rendering.

## 1. The Native Mindset

The "Whack-A-Mole" approach of fixing individual rendering artifacts (e.g., column breaks not working) is replaced by a fundamental alignment with the **KS X 6101** (OWPML) standard.

### 1.1 Structural Hierarchy
Native capabilities are often implemented through a nesting strategy:
1.  **Run-Level Controls**: Formatting that traditionally feels "global" (like multi-column) is often nested inside a specific run (`hp:run`) within the document's body.
2.  **Control Elements (`hp:ctrl`)**: Functions as a container for specialized properties like `hp:colPr` (columns) and `hp:eqEdit` (equations).

### 1.2 The "Spec-First" Mandate
To ensure compatibility with Hancom Office 2024, the pipeline rejects "simulated" formatting (e.g., using spaces for indents or text placeholders for math). All features must map to the corresponding **KS X 6101** XML element.

## 2. Multi-Column Layout (`colPr`)

To enable native multi-column rendering in Hancom Office 2024:
-   **Placement**: Must be inserted into the first paragraph's run, immediately after the section properties (`hp:secPr`).
-   **Required Attributes**:
    -   `colCount`: Number of columns (e.g., "2").
    -   `type`: Usually "NEWSPAPER" for standard flows.
    -   `sameSz`: "1" for equal widths.
    -   `sameGap`: The gutter width in HWPUNIT (e.g., "850").

## 3. Native Equations (`hp:eqEdit`)

Mathematical formulas are rendered by the Hancom engine only when provided as a script within an equation control.
-   **XML Structure**:
    ```xml
    <hp:run>
      <hp:ctrl>
        <hp:eqEdit version="2" baseLine="850">
          <hp:script>x^{2}+y^{2}=r^{2}</hp:script>
        </hp:eqEdit>
      </hp:ctrl>
    </hp:run>
    ```
-   **Script Syntax**: Uses a LaTeX-like but proprietary syntax. Key tokens include `OVER` (fraction), `SQRT` (root), `matrix` (matrix), `pile` (stacking).
-   **Constraints**: Text placeholders or standard MathML do not trigger the native HWP renderer. Direct XML injection of the `hp:script` block is required.

## 4. Section Properties (secPr)

Section properties define page size, margins, and the starting point of column layouts.
- **Nesting**: Must be at the very start of the first run of a section.
- **Critical Attributes**: `spaceColumns` (gutter space), `textDirection`, `tabStop`.

## 4. Implementation Rules for `HwpxDocumentBuilder`

1.  **Zero-Trust Styles**: Do not assume high-level attributes (like `columnBreak`) will trigger layout shifts.
2.  **Control Injection**: Use the `hp:ctrl` element for all specialized layout features.
3.  **Standard Units**: All numeric measurements must be converted to HWPUNIT (1/7200 inch) as per the OWPML spec.
