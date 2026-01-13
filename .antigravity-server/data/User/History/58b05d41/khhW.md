# Implementation: Image Extraction Protocol

Capturing embedded images and their content is a primary objective for high-fidelity HWPX reconstruction. This protocol defines how the `DoclingIngestor` handles and preserves visual elements.

## 1. Current Ingestion Logic

The `DoclingIngestor` identifies images as `PictureItem` objects during the conversion process.

- **Extraction**: The image data is available as a `PIL.Image` object within the `item.image` property.
- **IR Mapping**: The ingestor creates a `Figure` or `Image` IR element.
- **Current Limitation**: As of January 2026, the implementation uses a placeholder path (`embedded_image_stub`).

## 2. High-Fidelity Transition Path

To transition from placeholders to functional image reconstruction, the following protocol is implemented in the parsing verification loop:

### Step A: Materialization
The `PIL.Image` must be saved to a physical file in a dedicated assets directory:
```python
# Conceptual implementation for _process_picture
def _process_picture(self, section: Section, item: PictureItem):
    asset_id = f"img_{uuid.uuid4().hex[:8]}.png"
    asset_path = os.path.join(self.assets_dir, asset_id)
    item.image.save(asset_path)
    section.add_paragraph().elements.append(Figure(path=asset_path))
```

### Step B: Cross-Platform Accessibility
Since the `HwpExecutor` runs on Windows, the asset path must be:
1.  Stored in a location accessible by both WSL and Windows (e.g., `/mnt/c/temp/hwpx_assets/`).
2.  Converted to a Windows path using `wslpath -w` before being passed in the JSON payload.

### Step C: Content Extraction (OCR)
For images containing critical text (e.g., screenshots of tables), the pipeline leverages `EasyOCR` or `Surya` via Docling's OCR engine to ensure that even "burnt-in" text is searchable and potentially reconstructible as native HWPX text/tables.

## 3. Verification of Image Fidelity
The `verify_parsing_quality.py` script audits image extraction by:
- Counting the total number of `ir.Figure` elements found in the document.
- Logging the paths to ensure that the materialize-and-reference loop is functioning.
