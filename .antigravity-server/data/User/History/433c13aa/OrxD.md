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

### 2.3 Status: DEPRECATED (Phase 6)
As of late Phase 6 / early Phase 7, the **Native Generator is deprecated**.
- **Issue**: Files generated were frequently reported as "Damaged" by Hancom Office 2024.
- **Quality**: Lacked implementation for complex layout properties (indentation, tables, multi-sections).
- **Pivot**: The pipeline shifted emphasis back to the **Windows Builder** used in conjunction with high-fidelity **Mathpix OCR** (Phase 7).
