# HWPX Package Normalization

## 1. Objective
To ensure that generated `.hwpx` files are not just XML-compliant, but also structurally valid according to the Hancom Office 2024 ZIP container requirements. Standard ZIP libraries often produce non-deterministic entry ordering which can cause "Corrupted File" warnings in some versions of Hancom Word.

## 2. The Normalization Logic (`normalize_hwpx_package`)

The normalization process is triggered immediately after document assembly to finalize the file structure.

### 2.1 Critical Entry Ordering
HWPX requires the `mimetype` file to be the **first** entry in the ZIP archive, and it MUST be stored without compression (`ZIP_STORED`).
- **Priority**: `mimetype` (Index 0)
- **Secondary**: `version.xml`, `settings.xml`

### 2.2 Manifest Validation
Ensures `META-INF/manifest.xml` correctly references all internal components:
- `Contents/content.hpf`
- `Contents/header.xml`
- `Contents/section0.xml`

### 2.3 Empty Directory Suppression
Standard HWPX filters sometimes fail if empty directories (like `BinData/` when no images are present) are declared but contain no files. The normalizer prunes these or ensures placeholders exist if required.

## 3. Integration Path

Implemented in `lib/owpml/package_normalizer.py` and integrated into the `HwpxDocumentBuilder`:

```python
# lib/owpml/document_builder.py

def _save(self, output_path: str):
    # ... standard assembly logic ...
    self.pkg.save(output_path)

    # Normalize container ordering and required entries.
    try:
        normalize_hwpx_package(output_path)
    except Exception as exc:
        print(f"[HwpxDocumentBuilder] Warning: package normalization failed: {exc}")
```

## 4. Verification
Verified against Hancom Office 2024 (Windows). Normalized documents load without the "Repair document" prompt.
