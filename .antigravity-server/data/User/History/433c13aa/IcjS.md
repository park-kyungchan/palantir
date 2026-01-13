# HWPX Output Engines

## 1. HWPX Builder (Windows Automation)
The primary high-fidelity reconstruction engine. It transpiles `HwpAction` objects into a standalone Python script (`reconstruct.py`) for Windows-native execution via `win32com`.

### 1.1 Control Logic
- **Header**: Automatically injects `RegisterModule` with the security module (`FilePathCheckDLL`) to bypass prompt-based security blocks.
- **Lifecycle**: Strictly follows the `GetDefault` -> `SetItems` -> `Execute` pattern required by Hancom's OLE/COM interface.
- **Escaping**: Handles Korean character encodings and LaTeX reserved characters to ensure script validity.

## 2. Native OWPML Generator (Linux)
An experimental engine designed to produce `.hwpx` files directly on Linux using OWPML XML manipulation.

### 2.1 Strategy
Maps `HwpAction` sequence directly to XML fragments in `section0.xml` and packages them into a ZIP archive with the Hancom `mimetype`.

### 2.2 Architecture
- **Mimetype**: `application/hwp+zip` (Uncompressed, first file in ZIP).
- **Namespaces**: Uses Hancom-specific `hp` (paragraph) and `hs` (section) schemas.

### 2.3 Status: REVIVED (Phase 9 - Success)
Following a deep audit and implementation of the `HeaderManager` (Step 1726-1759), the Native Generator is now fully operational.
- **Audit Findings**: Files were previously "damaged" due to missing mandatory OWPML sections (`docOption`, `charPrList`, `styleList`, `borderFillList`).
- **Remediation**: `HeaderManager` now injects these sections into `header.xml`, including a default "Normal" style (ID 0) and HamChorom Batang font references.
- **Capabilities**: Full support for `SetParaShape` (margins, indentation, line spacing) via the ID-reference model.
- **Verification**: `test_owpml.py` confirmed 100% validity in Hancom Office 2024.
## 3. PDF Output Engine (Phase 8 - Success)
As an alternative to HWPX automation, a direct **PDF Output track** has been implemented to facilitate quick document viewing and verification without requiring Hancom Office.

### 3.1 Strategies
- **Cloud Rendering (Mathpix)**: **Implemented**. Utilizes the Mathpix API's `v3/converter` to convert Mathpix Markdown (MMD) directly back to PDF. **Note**: Reliable asset retrieval requires granular status polling and passing authentication headers even for direct file downloads.
- **Local Rendering (Fallback)**: 
    - **Status**: Limited local environment support (libraries like Pandoc/WeasyPrint are absent).
    - **Matplotlib**: Available as a potential engine for rendering mathematical formulas if needed for local composition.
- **Integration**: The `HWPXPipeline` supports a `generate_pdf=True` flag, which triggers the `PDFGenerator` to bypass the HWP compiler.
