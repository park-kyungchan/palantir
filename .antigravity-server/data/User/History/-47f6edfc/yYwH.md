# AI Model Management & Offline Operation

To ensure deterministic performance and avoid runtime timeouts (e.g., `timeout 120` in WSL), the HWPX pipeline strictly enforces a **Pre-download & Cache** strategy for all AI model dependencies.

## 1. Supported Model Engines
The pipeline manages weights for the following engines:
- **Docling**: Layout, TableFormer, DocumentFigureClassifier.
- **EasyOCR**: Language-specific recognition models (Korean, English).
- **DocLayout-YOLO**: Page layout analysis.
- **Surya**: (Optional) Text detection and recognition.

## 2. Model Pre-downloading (CLI)
Before running the pipeline in restricted or high-latency environments, execute the following commands within the virtual environment:

### 2.1 IBM Docling
```bash
source .venv/bin/activate
docling-tools models download
```
- **Target Path**: `~/.cache/docling/models/`
- **Estimated Size**: ~500MB - 2GB depending on configuration.

### 2.2 EasyOCR
EasyOCR models are typically downloaded on first use to `~/.EasyOCR/model/`. It is recommended to verify this directory contains the `ko_g2` and `english_g2` weights.

## 3. Pipeline Configuration (Offline Mode)
Ingestors must be explicitly configured to use the local artifacts path to skip HuggingFace Hub checks.

### 3.1 Docling Configuration
In `lib/ingestors/docling_ingestor.py`, the `PdfPipelineOptions` should be initialized with the local path:

```python
import os
from docling.datamodel.pipeline_options import PdfPipelineOptions

artifacts_path = os.path.expanduser("~/.cache/docling/models")

pipeline_options = PdfPipelineOptions()
if os.path.isdir(artifacts_path):
    pipeline_options.artifacts_path = artifacts_path
```

## 4. Troubleshooting
- **DNS Failures**: If the agent attempts to connect to `huggingface.co`, verify the `artifacts_path` is correctly set and pointing to a directory containing the expected model snapshots.
- **Partial Downloads**: Use `du -sh ~/.cache/docling/models` to ensure the model size matches expectations (e.g., >500MB).
- **WSL Pathing**: Ensure `~/.cache` is within the Linux filesystem (not `/mnt/c/`) for optimal I/O performance.

---
**Status**: ACTIVE. Enforced as part of the Jan 2026 Stability Update.
