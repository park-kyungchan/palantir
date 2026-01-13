# OWPML Validation Logic (Jan 2026 Implementation)

## 1. Overview
As part of the **KS X 6101:2024 compliance** initiative, an automated validation layer was implemented to ensure that generated HWPX files are structurally sound and internally consistent before distribution.

## 2. Component: `OWPMLValidator`
The validator is implemented in [`lib/owpml/validator.py`](file:///home/palantir/hwpx/lib/owpml/validator.py). It performs four primary categories of checks:

### 2.1 Package Structure (OCF Compliance)
Ensures the HWPX ZIP archive contains all mandatory components required by the Open Container Format:
- `mimetype`
- `version.xml`
- `Contents/content.hpf`
- `Contents/header.xml`
- `Contents/section0.xml`
- `META-INF/container.xml`

### 2.2 Mimetype Constraints
Following strict OCF and OWPML standards:
- **Placement**: The `mimetype` file MUST be the first file in the ZIP archive.
- **Compression**: The file MUST be stored using the `ZIP_STORED` method (no compression).
- **Content**: Must contain exactly `application/hwp+zip`.

### 2.3 XML Well-formedness
Scans all `.xml` and `.hpf` files in the package to verify they are valid XML.

### 2.4 ID Reference Integrity
This is the most critical logic for document stability. The validator cross-references IDs used in content sections (`section[n].xml`) against definitions in the central registry (`header.xml`).

| Reference Attribute | Target Definition |
|---------------------|-------------------|
| `charPrIDRef` | `<hh:charPr>` |
| `paraPrIDRef` | `<hh:paraPr>` |
| `borderFillIDRef` | `<hh:borderFill>` |
| `styleIDRef` | `<hh:style>` |
| `tabPrIDRef` | `<hh:tabPr>` |
| `numberingIDRef` | `<hh:numbering>` |

**Note**: ID "0" is treated as a standard fallback and does not trigger warnings if missing from the header, as it often refers to system defaults.

## 3. Usage Pattern
The validator can be used as a standalone CLI tool or integrated into the `HwpxDocumentBuilder` pipeline.

```python
from lib.owpml.validator import validate_hwpx

is_valid, messages = validate_hwpx("output.hwpx")
if not is_valid:
    print("Validation failed:")
    for msg in messages:
        print(f"  {msg}")
```

## 4. Verification & Testing
The validation logic is verified by [`tests/test_validator.py`](file:///home/palantir/hwpx/tests/test_validator.py).
- **Golden Baseline**: `Skeleton.hwpx` is used as the ground-truth valid document.
- **Regression**: All generated `output*.hwpx` files are periodically scanned for structural errors.

### Results (Jan 2026):
- **Skeleton.hwpx**: ✅ Valid
- **Namespace Handling**: ✅ Correctly handles URI-prefixed tags.
- **Mimetype**: ✅ Successfully detects compression or ordering violations.
