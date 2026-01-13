# Pilot: PDF Reconstruction Track (Pipeless)

## 1. Overview
The "Pipeless" PDF reconstruction track (Phase 8) was implemented to provide a direct path from Mathpix Ingestion to high-fidelity PDF output. This bypasses the complexity of HWP Compiler, HWPX XML generation, and Windows automation when the target format is simply a high-quality PDF.

## 2. Environment Constraints & Resolution
During research, it was found that standard Linux PDF libraries (Pandoc, WeasyPrint) were not available in the WSL2 environment. To resolve this, the pipeline utilizes **Mathpix Cloud Rendering**.

## 3. Implementation: PDFGenerator
The `PDFGenerator` (`lib/generators/pdf_generator.py`) serves as the core engine for this track.

- **API Interface**: Wraps the `https://api.mathpix.com/v3/converter` endpoint.
- **Workflow**:
    1. **Submission**: Sends MMD content with `formats: {"pdf": true}`.
    2. **Granular Polling**: 
        - Mathpix returns `status: "completed"` when the *request* is processed, but the *sub-format generation* (PDF) might still be `processing`.
        - The `PDFGenerator` implementation checks `data["conversion_status"]["pdf"]["status"] == "completed"`.
    3. **Asset Fetching**: Downloads the resulting PDF from the signed Cloud CDN URL.

## 4. Pipeline Integration
The main `HWPXPipeline` class was updated to support a `generate_pdf` branch.

```python
if generate_pdf:
    from lib.generators.pdf_generator import PDFGenerator
    gen = PDFGenerator()
    gen.generate(mmd_content, output_path)
    return [] # Skip Compilation
```

## 5. CLI Usage
Users can trigger the PDF track by passing the `--pdf` flag to the pipeline script:

```bash
python scripts/run_pipeline.py input.pdf output.pdf --pdf
```

## 6. Verification
- **Test Script**: `test_converter.py` verified the async polling logic and retrieved a valid PDF with complex math (`\int_0^\infty x^2 dx`).
- **Production Run**: `reconstructed.pdf` was successfully generated from `sample.pdf`.
