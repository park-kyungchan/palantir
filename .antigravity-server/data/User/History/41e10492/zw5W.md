# Implementation: WSL Environment Configuration

The WSL-based ingestion pipeline faces specific configuration hurdles due to modern Linux distribution constraints and heavy library dependencies.

## 1. Externally Managed Environments (PEP 668)

In recent Ubuntu/Debian versions (like the one used in the `palantir` workstation), `pip install` on the system Python is blocked with an `externally-managed-environment` error.

### Problem
Attempting to install `docling` or `easyocr` directly results in a failure pointing to PEP 668.

### Solutions
1.  **Virtual Environments (Recommended)**: Create a project-specific venv to isolate dependencies.
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install docling easyocr pymupdf
    ```
2.  **System Override (Riskier)**: Use the `--break-system-packages` flag if a virtual environment is not feasible in the current workflow context.
    ```bash
    pip install docling --break-system-packages
    ```

## 2. Dependency Management

The `hwpx-automation` project has a `requirements.txt` that separates concerns:
- **Phase 1 (Math Detection)**: `ultralytics`, `huggingface-hub`.
- **Phase 2 (Layout Analysis)**: `doclayout-yolo`.
- **Phase 3 (OCR)**: `surya-ocr`, `paddleocr`.
- **PDF Processing**: `docling`.

**Note**: `pyhwpx` is a Windows-only dependency and should **not** be in the WSL `requirements.txt`. It is managed on the Windows side for OLE automation.
