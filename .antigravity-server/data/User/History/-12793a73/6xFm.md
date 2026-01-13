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

## 3. Usage & Integration Pattern
The validator is integrated directly into the `HwpxDocumentBuilder._save()` method within [`lib/owpml/document_builder.py`](file:///home/palantir/hwpx/lib/owpml/document_builder.py).

### 3.1 Integrated Call
After the package is normalized, the validator is invoked to catch structural anomalies:

```python
# lib/owpml/document_builder.py
try:
    from lib.owpml.validator import validate_hwpx
    is_valid, messages = validate_hwpx(output_path)
    if not is_valid:
        print(f"[HwpxDocumentBuilder] Validation FAILED:")
        for msg in messages:
            print(f"  {msg}")
    elif messages:
        # Log warnings but continue
        for msg in messages:
            if 'WARNING' in msg:
                 print(f"[HwpxDocumentBuilder] {msg}")
except Exception as exc:
    print(f"[HwpxDocumentBuilder] Warning: validation failed: {exc}")
```

## 4. Verification & Testing
The validation logic is verified by [`tests/test_validator.py`](file:///home/palantir/hwpx/tests/test_validator.py).

### 4.1 Results (Jan 2026 Audit)
- **Skeleton.hwpx (Golden Baseline)**: ✅ **Valid**. Confirms that the OWPML structure used as a template is 100% compliant.
- **output_pilot.hwpx (Generated)**: ✅ **Valid**. Successfully detected minor OCF ordering warnings which prompted an audit of the `PackageNormalizer`.
- **sample_3x3_table.hwpx (Sample)**: ✅ **Valid**. Verified table generation and cell address mapping (Jan 9, 2026).
- **ID Integrity**: ✅ **Verified**. Successfully identifies orphaned `charPrIDRef` or `paraPrIDRef` entries in generated sections.

### 4.2 Known Warning Patterns
- **Mimetype Placement**: OCF requires `mimetype` to be the very first entry in the ZIP. If the build process appends files in a non-deterministic order, the validator issues a `[WARNING] [mimetype] mimetype should be the first file in the archive`.
- **Mimetype Compression**: Must be `ZIP_STORED`. The validator identifies `[WARNING] [mimetype] mimetype should be stored uncompressed` if incorrectly compressed by the utility library.

### 4.3 Renderability vs. Validity
As of Jan 9, 2026, it is established that **XML Structural Validity** (passing `etree` parsing) does NOT guarantee **Hancom Office Renderability**.

- **The Prefix Paradox Resolved**: Initial findings that standard prefixes were mandatory were debunked by files using `ns0` aliases working while `hp`-prefixed ones crashed. The true crash vector was the **absence of `<hp:cellSpan>`** in table cells. The Hancom Office renderer is highly sensitive to the internal child-element structure of tables, but resilient to prefix aliasing as long as the namespaces are declared.
- **Structural Completeness**: Elements like `hp:cellSpan` (in `hp:tc`) and `hp:linesegarray` (in `hp:p`) must be present to satisfy the native renderer's object model.
