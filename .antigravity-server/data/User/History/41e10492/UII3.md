# Implementation: WSL Environment Configuration

The WSL-based ingestion pipeline faces specific configuration hurdles due to modern Linux distribution constraints and heavy library dependencies.

## 1. Externally Managed Environments (PEP 668)

In recent Ubuntu/Debian versions (like the one used in the `palantir` workstation), `pip install` on the system Python is blocked with an `externally-managed-environment` error.

### Problem
Attempting to install `docling` or `easyocr` directly results in a failure pointing to PEP 668.

### Solutions
1.  **Virtual Environments (Verified)**: Create a project-specific venv. This successfully bypassed the PEP 668 restriction on the Palantir workstation.
    ```bash
    # Step-by-step verified initialization
    python3 -m venv .venv
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -r requirements.txt
    .venv/bin/pip install easyocr
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

## 3. Infrastructure & Storage Requirements

The high-fidelity parsing pipeline leverages GPU-accelerated libraries for OCR and layout analysis, which imposes significant infrastructure requirements:

- **Storage Footprint**: The `.venv` can exceed **3-5GB** due to heavy machine learning dependencies:
    - `torch`: ~900MB
    - `nvidia-cudnn-cu12`: ~700MB
    - `nvidia-cublas-cu12`: ~600MB
    - `nvidia-cuda-nvrtc-cu12`: ~100MB
- **RAM Constraints**: Sequential processing (one file at a time) is mandatory on workstations with **16GB RAM** or less to avoid OOM (Out Of Memory) errors during model loading and document conversion.
- **Initialization Time**: First-time environment setup can take 10-20 minutes depending on network bandwidth, as it pulls multiple large binary blobs from PyPI/NVIDIA.

## 4. Workstation Git Configuration

When performing Git operations (commit/push) from the workstation CLI for the first time, an "Author identity unknown" error may occur if the global configuration is missing.

### Problem
`fatal: empty ident name (for <palantir@kc-palantir.localdomain>) not allowed`

### Solution
Configure the project-specific or global identity before committing:
```bash
git config --global user.email "your-email@example.com"
git config --global user.name "Your Name"
```
Or set it locally within the repo:
```bash
git config user.email "hwpx-reconstruction@internal.palantir"
git config user.name "HWPX Reconstruction Engine"
```

