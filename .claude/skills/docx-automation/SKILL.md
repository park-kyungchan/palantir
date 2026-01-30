---
name: docx-automation
description: |
  Generate DOCX documents from pipeline results or structured data.
  Uses python-docx library for Word document generation.
  Supports template-based reports, batch exports, and custom styling.
  Use when user asks to create Word documents, export reports, or generate DOCX files.

  Core Capabilities:
  - Pipeline Export: Generate DOCX from mathpix_pipeline results
  - JSON Conversion: Convert structured JSON to formatted DOCX
  - Template Reports: Generate detailed reports with custom styling
  - Batch Export: Process multiple documents in sequence

  Output Format:
  - L1: Generation summary (file path, size, status)
  - L2: Document structure and content overview
  - L3: Full DOCX file

  Pipeline Position:
  - Independent Utility Skill
  - Can be called standalone or post-pipeline
user-invocable: true
disable-model-invocation: false
context: fork
model: opus
allowed-tools:
  - Read
  - Bash
  - Write
  - Task
  - mcp__sequential-thinking__sequentialthinking
argument-hint: "generate <source> | from-json <data.json> | report <image_id> | --workload <slug>"
version: "3.0.0"
hooks:
  Setup:
    - type: command
      command: "source /home/palantir/.claude/skills/shared/workload-files.sh"
      timeout: 5000

# =============================================================================
# P1: Skill as Sub-Orchestrator (Minimal - Utility Skill)
# =============================================================================
agent_delegation:
  enabled: false
  reason: "Utility skill - direct execution for document generation"
  output_paths:
    l1: ".agent/prompts/{slug}/docx-automation/l1_summary.yaml"
    l2: ".agent/prompts/{slug}/docx-automation/l2_index.md"
    l3: ".agent/prompts/{slug}/docx-automation/l3_details/"
  return_format:
    l1: "Generation summary with file path and size (≤500 tokens)"
    l2_path: ".agent/prompts/{slug}/docx-automation/l2_index.md"
    l3_path: ".agent/prompts/{slug}/docx-automation/l3_details/"
    requires_l2_read: false
    next_action_hint: "DOCX file at specified path"

# =============================================================================
# P2: Parallel Agent Configuration (Batch Mode Only)
# =============================================================================
parallel_agent_config:
  enabled: false
  reason: "Sequential document generation preferred for consistency"
  batch_mode:
    description: "For batch exports, process documents sequentially"
    use_when: "Multiple documents requested"

# =============================================================================
# P6: Internal Validation (Document Generation)
# =============================================================================
internal_validation:
  enabled: true
  checks:
    - "Source data is readable and valid"
    - "python-docx library is installed"
    - "Output directory is writable"
  max_retries: 2
---

### Auto-Delegation Trigger (CRITICAL)

> **Reference:** `.claude/skills/shared/auto-delegation.md`
> **Behavior:** When `agent_delegation.enabled: true` AND `default_mode: true`, skill automatically operates as Sub-Orchestrator.

```javascript
// AUTO-DELEGATION CHECK - Execute at skill invocation
// If complex task detected, triggers: analyze → delegate → collect
const delegationDecision = checkAutoDelegation(SKILL_CONFIG, userRequest)
if (delegationDecision.shouldDelegate) {
  const complexity = analyzeTaskComplexity(taskDescription, SKILL_CONFIG)
  return executeDelegation(taskDescription, complexity, SKILL_CONFIG)
}
// Simple tasks execute directly without delegation overhead
```


# DOCX Automation Skill

## Workload Slug 생성 (표준)

```bash
# Source centralized slug generator
source "${WORKSPACE_ROOT:-.}/.claude/skills/shared/slug-generator.sh"
source "${WORKSPACE_ROOT:-.}/.claude/skills/shared/workload-files.sh"

# Slug 결정 (우선순위)
# 1. --workload 인자 (명시적 지정)
# 2. 활성 workload (get_active_workload)
# 3. 새 workload 생성 (기본 동작 - 독립 스킬)

if [[ -n "$WORKLOAD_ARG" ]]; then
    SLUG="$WORKLOAD_ARG"
    echo "📄 Using specified workload: $SLUG"

elif ACTIVE_WORKLOAD=$(get_active_workload) && [[ -n "$ACTIVE_WORKLOAD" ]]; then
    WORKLOAD_ID="$ACTIVE_WORKLOAD"
    SLUG=$(get_active_workload_slug)
    echo "📄 Using active workload: $SLUG"

else
    # 기본 동작: 새 workload 생성 (독립 스킬)
    SOURCE_FILE="${1:-document}"
    TOPIC="docx-${SOURCE_FILE##*/}"
    WORKLOAD_ID=$(generate_workload_id "$TOPIC")
    SLUG=$(generate_slug_from_workload "$WORKLOAD_ID")
    init_workload_directory "$WORKLOAD_ID"
    set_active_workload "$WORKLOAD_ID"
    echo "📄 Created new workload: $SLUG"
fi

# 출력 경로 설정 (워크로드 연계 시)
WORKLOAD_DIR=".agent/prompts/${SLUG}"
# DOCX는 기본적으로 ./exports/ 사용, 워크로드 연계 시 ${WORKLOAD_DIR}/exports/
```

---



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

---



## 7. Standalone Execution (V2.2.0)

> /docx-automation는 독립 유틸리티로 파이프라인 외부에서 실행 가능

### 7.1 독립 실행 모드

```bash
# 독립 실행 (새 workload 생성)
/docx-automation generate synthesis-report

# JSON 데이터 기반
/docx-automation from-json ./data/results.json

# 기존 workload 결과 사용
/docx-automation report user-auth-20260128 --workload user-auth-20260128-143022
```

### 7.2 Workload Context Resolution

```javascript
// Workload 감지 우선순위:
// 1. --workload 인자
// 2. Active workload (_active_workload.yaml)
// 3. 새 workload 생성 (문서 유형 기반)

source /home/palantir/.claude/skills/shared/skill-standalone.sh
const context = init_skill_context("docx-automation", ARGUMENTS, DOCUMENT_TYPE)
```

---



## 8. Handoff Contract (V2.2.0)

> /docx-automation는 독립 유틸리티 (Independent Utility Skill)

### 8.1 Handoff 매핑

| Status | Next Skill | Arguments |
|--------|------------|-----------|
| `completed` | (none) | Document generation complete |

### 8.2 파이프라인 위치

```
[독립 유틸리티]
    │
/docx-automation ──── 파이프라인 외부에서 호출 가능
    │
    └── Output: .agent/prompts/{slug}/docx/{filename}.docx
```

### 8.3 Handoff YAML 출력

```yaml
handoff:
  skill: "docx-automation"
  workload_slug: "{slug}"
  status: "completed"
  timestamp: "2026-01-28T14:35:00Z"
  next_action:
    skill: null
    arguments: null
    required: false
    reason: "Document generated successfully"
  output:
    path: ".agent/prompts/{slug}/docx/{filename}.docx"
    format: "docx"
```

---



### Version History

| Version | Change |
|---------|--------|
| 1.1.1 | DOCX generation with python-docx |
| 2.1.0 | V2.1.19 Spec 호환, allowed-tools 배열 형식 수정 |
| 2.2.0 | Standalone Execution + Handoff Contract |
| 3.0.0 | EFL Pattern Integration, disable-model-invocation: true, context: fork |

---



## EFL Pattern Implementation (V3.0.0)

### Utility Skill Design

As an Independent Utility Skill:
- Direct execution without agent delegation (P1 disabled)
- Sequential processing for document consistency (P2 disabled)
- Internal validation for generation safety (P6 adaptation)

### P6: Document Generation Validation

```javascript
// Pre-generation validation
const docxValidation = {
  maxRetries: 2,
  checks: [
    "sourceData !== null && sourceData !== undefined",
    "pythonDocxInstalled()",
    "outputDirWritable(outputPath)"
  ],
  onFailure: "Return error with installation instructions"
}
```

### Post-Compact Recovery

```javascript
if (isPostCompactSession()) {
  const slug = await getActiveWorkload()
  if (slug) {
    // Check for partial generation
    const exportDir = `.agent/prompts/${slug}/docx/`
    const partialFiles = await Glob(`${exportDir}/*.partial`)
    if (partialFiles.length > 0) {
      console.log("Resuming partial document generation...")
    }
  }
}
```
