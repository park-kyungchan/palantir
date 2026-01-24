---
name: docx-automation
description: |
  Generate DOCX documents from pipeline results or structured data.
  Uses python-docx library for Word document generation.
  Supports template-based reports, batch exports, and custom styling.
  Use when user asks to create Word documents, export reports, or generate DOCX files.
user-invocable: true
disable-model-invocation: false
context: standard
model: opus
allowed-tools:
  - Read
  - Bash
  - Write
argument-hint: "generate <source> | from-json <data.json> | report <image_id>"
version: "2.1.0"
---

# DOCX Automation Skill

## Purpose

Generate Microsoft Word documents from:
- Pipeline export results (mathpix_pipeline)
- Structured data (JSON/YAML/Dict)
- Template-based generation for reports

## Prerequisites

```bash
pip install python-docx>=0.8.11
```

## Usage

### Command Line

```bash
# Generate DOCX from pipeline results
/docx generate <source_file> [--output <output.docx>]

# Convert JSON data to formatted DOCX
/docx from-json <data.json> --output report.docx

# Generate report from pipeline data
/docx report <image_id> --format detailed
```

### Programmatic Usage

```python
from mathpix_pipeline.export.exporters.docx_exporter import (
    DOCXExporter,
    DOCXExporterConfig,
)
from mathpix_pipeline.schemas.export import ExportOptions

# Initialize exporter with custom config
config = DOCXExporterConfig(
    output_dir=Path("./exports"),
    font_name="Arial",
    font_size_pt=12,
    include_header=True,
    include_footer=True,
)
exporter = DOCXExporter(config)

# Export pipeline data
options = ExportOptions(
    include_metadata=True,
    include_provenance=True,
)
spec = exporter.export(data, options, image_id="img_001")
print(f"Exported to: {spec.file_path}")
```

## Actions

### generate
Generate DOCX from pipeline results using DOCXExporter.

**Parameters:**
- `source_file`: Path to source data (JSON, pickle, or pipeline result)
- `--output`: Output file path (optional, auto-generated if not provided)
- `--config`: Custom configuration file path

### from-json
Convert structured JSON to formatted DOCX document.

**Parameters:**
- `data_file`: Path to JSON data file
- `--output`: Output DOCX file path (required)
- `--template`: Document template to use

### report
Generate a detailed report from pipeline processing results.

**Parameters:**
- `image_id`: Pipeline image identifier
- `--format`: Report format (summary, detailed, full)
- `--include-images`: Include image references

## Configuration Options

### DOCXExporterConfig

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `output_dir` | Path | `./exports` | Output directory |
| `page_width_inches` | float | 8.5 | Page width |
| `page_height_inches` | float | 11.0 | Page height |
| `margin_inches` | float | 1.0 | Page margins |
| `font_name` | str | Times New Roman | Body font |
| `font_size_pt` | int | 11 | Body font size |
| `heading_font_name` | str | Arial | Heading font |
| `include_toc` | bool | False | Table of contents |
| `include_header` | bool | True | Document header |
| `include_footer` | bool | True | Page numbers |

## Integration with Pipeline

The DOCXExporter integrates with the mathpix_pipeline export system:

```python
from mathpix_pipeline.export.exporters import DOCXExporter
from mathpix_pipeline.schemas.export import ExportFormat

# Check format support
assert ExportFormat.DOCX.value == "docx"

# Use in export pipeline
exporter = DOCXExporter()
result = exporter.export(
    data=regeneration_spec,
    options=ExportOptions(),
    image_id="processed_image_001"
)
```

## Output Structure

Generated DOCX documents include:

1. **Title Section**
   - Document title (from image_id or export_id)
   - Center-aligned heading

2. **Content Section**
   - Outputs (if available)
   - Graph nodes (if available)
   - Equations with LaTeX representation

3. **Metadata Section** (optional)
   - Generation timestamp
   - Source data attributes

4. **Provenance Section** (optional)
   - Creation timestamp
   - Pipeline version
   - Completed stages

## Error Handling

```python
try:
    spec = exporter.export(data, options, image_id)
except ImportError as e:
    # python-docx not installed
    print("Install python-docx: pip install python-docx")
except ExporterError as e:
    # Export failed
    print(f"Export error: {e.message}")
    print(f"Details: {e.details}")
```

## Examples

### Basic Export

```python
from pathlib import Path
from mathpix_pipeline.export.exporters.docx_exporter import DOCXExporter
from mathpix_pipeline.schemas.export import ExportOptions

exporter = DOCXExporter()
data = {"equations": [{"latex": "E = mc^2", "text": "Energy equals..."}]}
options = ExportOptions(include_metadata=True)
spec = exporter.export(data, options, "einstein_formula")
```

### Custom Styling

```python
from mathpix_pipeline.export.exporters.docx_exporter import (
    DOCXExporter,
    DOCXExporterConfig,
)

config = DOCXExporterConfig(
    font_name="Calibri",
    font_size_pt=10,
    heading_font_name="Calibri Light",
    margin_inches=0.75,
)
exporter = DOCXExporter(config)
```

### Batch Export

```python
for image_id, data in pipeline_results.items():
    spec = exporter.export(data, options, image_id)
    print(f"Exported {image_id}: {spec.file_size} bytes")
```

## See Also

- `/pdf` - PDF export skill
- `/latex` - LaTeX export skill
- `mathpix_pipeline.export.exporters.base` - Base exporter class

---

## Parameter Module Compatibility (V2.1.0)

> `/build/parameters/` 모듈과의 호환성 체크리스트

| Module | Status | Notes |
|--------|--------|-------|
| `model-selection.md` | ✅ | `model: opus` 설정 |
| `context-mode.md` | ✅ | `context: standard` 사용 |
| `tool-config.md` | ✅ | V2.1.0: Read, Bash, Write 지정 |
| `hook-config.md` | N/A | Skill 내 Hook 없음 |
| `permission-mode.md` | N/A | Skill에는 해당 없음 |
| `task-params.md` | N/A | 내부 Task 위임 없음 |

### Version History

| Version | Change |
|---------|--------|
| 1.1.1 | DOCX generation with python-docx |
| 2.1.0 | V2.1.19 Spec 호환, allowed-tools 배열 형식 수정 |
