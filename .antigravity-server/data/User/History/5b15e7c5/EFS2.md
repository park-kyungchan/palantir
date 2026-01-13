# HWPX Pipeline: E2E Pilot Test Results (sample.pdf)

## 1. Test Overview
- **Target File**: `hwpx/sample.pdf` (Complex math workbook with tables and formulas)
- **Engine**: HWPX Reconstruction Pipeline v1.5
- **Mode**: Local (`--no-ocr`, using Docling for structural ingestion)
- **Date**: 2026-01-08

## 2. Execution Details
The pipeline was run with unbuffered output to monitor progress in real-time.

**Command**:
```bash
cd /home/palantir/hwpx && source .venv/bin/activate && python -u main.py sample.pdf -o output_pilot.json --no-ocr
```

**Key Log Output**:
```text
Starting HWPX Pipeline...
Input: /home/palantir/hwpx/sample.pdf
Output: output_pilot.json
...
Compiling IR to HWP Actions...
[Compiler] Compile Start. Sections: 1
[Compiler] Processing Section 0, elements: 18
Saving JSON output to: output_pilot.json
Building reconstruction script: output_pilot.py
Generating Native HWPX: output_pilot.hwpx
[HwpxDocumentBuilder] Building document with 54 actions...
[HwpxDocumentBuilder] Saved to output_pilot.hwpx
Success! Generated 54 actions.
```

## 3. Artifact Verification

### 3.1 File System Check
| Artifact | Size | Description |
|---|---|---|
| `output_pilot.json` | 5,663 bytes | The intermediate HwpAction sequence. |
| `output_pilot.py` | 15,163 bytes | The win32com reconstruction script (Digital Twin). |
| `output_pilot.hwpx` | 8,539 bytes | The final native OWPML package. |

### 3.2 Internal XML Audit (output_pilot.hwpx)
Verification of `Contents/section0.xml` confirmed the use of the high-fidelity `HwpxDocumentBuilder`:
- **Nested Structure**: Elements are correctly wrapped in `<ns1:p>` and `<ns1:run>`.
- **Page Setup**: `<ns1:pagePr>` correctly applied margins and paper size (A4).
- **Styling**: `paraPrIDRef` and `charPrIDRef` correspond to definitions in `header.xml`.

### 3.3 Reconstruction Logic (output_pilot.py)
The generated Python script showed correct handling of paragraph shapes (indents) and text insertion:
- `hwp.HParameterSet.HParaShape.Item('Indent') = hwp.PointToSet(-20)`
- `hwp.HAction.Execute('InsertText', hwp.HParameterSet.HInsertText.HSet)`

## 4. Conclusion
The pilot test confirms that the HWPX Pipeline successfully bridges the gap between layout analysis (Docling) and native document generation (HwpxDocumentBuilder). The 54 actions accurately represent the 18 elements identified in the input section, including complex scientific notation and multi-paragraph problems.

**Status**: ✅ **PASS**
