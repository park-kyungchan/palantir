---
name: image-preprocess
description: |
  [D0·Foundation·Preprocess] CleanOCROutput for Pipeline B entry: OCR artifact detection, LaTeX cleanup, confidence scoring, backslash depth assessment. Multi-source (Doc Intelligence, Mathpix, manual). HITL when confidence < 0.7.

  WHEN: OCR output arrives for production QC, or image-derived LaTeX needs cleanup before validation. Pipeline B entry point.
  DOMAIN: foundation (D0 shared, skill 2 of 2). Peer: reference-build. Independent entry point for Pipeline B.
  INPUT_FROM: User (OCR output/image path via $ARGUMENTS), reference-build (OCR confusion patterns via IC-01 ocr_confusions).
  OUTPUT_TO: jsonl-validate IC-13 preprocessed_input (latex_content, confidence, flagged_artifacts, backslash_depth, quality_score, hitl_required).

  METHODOLOGY: (1) Detect source type + OCR tool from input, (2) Clean raw content (Unicode, whitespace, broken LaTeX), (3) Detect OCR artifacts via reference-build patterns, (4) Score quality across 4 dimensions + assess backslash depth, (5) Emit IC-13 preprocessed_input with full schema.
  OUTPUT_FORMAT: L1 YAML quality summary, L2 with IC-13 preprocessed_input section.
user-invocable: true
disable-model-invocation: false
argument-hint: "[image-path|ocr-output-path|latex-draft-path]"
---

# Foundation -- Image Preprocess

## Execution Model
- **Single-file**: One OCR output / image path / LaTeX draft at a time. Lead-direct invocation.
- **Batch**: Multiple files via `batch_id`. Lead iterates, calling `/image-preprocess` per file.
- **Multi-source**: Different OCR tools produce different artifact patterns. Source detection drives cleanup strategy:
  - **Doc Intelligence**: Unicode quirks, math region markers, specific line-break patterns
  - **Mathpix**: LaTeX with confidence annotations, inline math detection markers
  - **Manual**: No tool artifacts, but potential typos and inconsistent formatting
- All tiers: Lead-direct. No agent spawning needed (deterministic cleanup pipeline).

## Decision Points

### Source Type Detection
Determine input type from file extension, content patterns, or explicit `$ARGUMENTS`:

```
IF $ARGUMENTS specifies source type explicitly:
  -> Use specified type (ocr_output | latex_draft | image | manual_input)

ELIF file extension is .png/.jpg/.jpeg/.tiff/.pdf:
  -> type = "image"
  -> ABORT: Cannot perform OCR. Inform user to run external OCR tool first.
  -> Suggest: Doc Intelligence or Mathpix, then re-invoke with OCR output.

ELIF content contains \begin, \frac, \int, or other LaTeX commands:
  IF content also has OCR artifact markers (garbled Unicode, broken symbols):
    -> type = "ocr_output" (OCR-derived LaTeX)
  ELSE:
    -> type = "latex_draft" (human-written or tool-generated LaTeX)

ELIF content is plain text with math fragments (numbers, operators, no LaTeX markup):
  -> type = "ocr_output" (raw OCR text, no LaTeX conversion yet)

ELSE:
  -> type = "manual_input" (fallback)
  -> WARN: Source type unrecognized, defaulting to manual_input.
```

### OCR Tool Detection
Identify which OCR tool produced the output to apply tool-specific cleanup:

```
IF content contains Azure Doc Intelligence markers:
  (e.g., :selected:, :unselected:, specific Unicode patterns, page/line metadata)
  -> tool = "doc_intelligence"
  -> Apply: Unicode normalization, math region extraction, line-merge heuristics

ELIF content contains Mathpix-style annotations:
  (e.g., confidence brackets [0.95], \text{} wrapping patterns, inline $...$ detection)
  -> tool = "mathpix"
  -> Apply: Strip confidence annotations, normalize \text{} usage, verify delimiters

ELIF type == "manual_input" OR no tool markers detected:
  -> tool = "manual" (or "other")
  -> Apply: Basic whitespace normalization, LaTeX syntax check only
```

### Artifact Classification Strategy
Map detected issues to the 6 artifact types defined in IC-13 `flagged_artifacts`:

| Type | Description | Typical Source | Default Severity |
|------|-------------|----------------|------------------|
| `ocr_misrecognition` | Character confused by OCR | All OCR tools | FAIL |
| `encoding_error` | Unicode/encoding corruption | Doc Intelligence | FAIL |
| `structural_damage` | LaTeX structure broken (unclosed env, missing braces) | OCR line breaks | FATAL |
| `missing_content` | Content present in source but absent in output | OCR region skip | FATAL |
| `extra_content` | Noise, headers, page numbers leaked into content | OCR boundary error | WARN |
| `formatting_loss` | Spacing, alignment, style degraded but content intact | All sources | INFO |

Severity escalation rules:
- Any artifact where content meaning changes: minimum FAIL
- Any artifact where content is unrecoverable without source: FATAL
- `ocr_misrecognition` with `confidence < 0.5`: escalate to FATAL (unreliable correction)

### Quality Score Calculation
Four dimensions, weighted to reflect production QC priorities:

| Dimension | Weight | Description | Scoring |
|-----------|--------|-------------|---------|
| `completeness` | 30% | All source content present in output | 1.0 - (missing_chars / total_chars) |
| `accuracy` | 30% | Content correctly transcribed | 1.0 - (artifact_count * severity_weight / total_elements) |
| `structure` | 25% | LaTeX structure valid and complete | Env matching + brace balance + command validity |
| `cleanliness` | 15% | No noise, extra content, or formatting debris | 1.0 - (extra_artifacts / total_elements) |

Severity weights for accuracy: FATAL=1.0, FAIL=0.5, WARN=0.2, INFO=0.05.
Overall = weighted average across 4 dimensions.

### Backslash Depth Assessment
Determine current escape depth from content analysis:

```
Depth 0 (Raw LaTeX):    \frac{a}{b}         -> source image/document
Depth 1 (String):       \\frac{a}{b}        -> LaTeX in a string context
Depth 2 (JSONL):        \\\\frac{a}{b}      -> LaTeX in JSONL file

DETECTION:
  Count consecutive backslashes before known LaTeX commands (\frac, \int, \sum, etc.)
  IF mostly single-backslash: current_depth = 0
  IF mostly double-backslash: current_depth = 1
  IF mostly quadruple-backslash: current_depth = 2

  target_depth = 2 (always, for JSONL downstream consumer)
  needs_escaping = (current_depth < target_depth)

  depth_map: per-command analysis showing current vs target escaping
```

### HITL Trigger Decision
```
Set hitl_required = true when ANY of:
  - Overall confidence < 0.7 (REQ-IP-05 threshold)
  - Any flagged_artifact has severity == FATAL
  - quality_score.overall < 0.6
  - Source type detection fell back to "manual_input" unexpectedly

Set hitl_reason to explain the specific trigger(s).
Set hitl_artifacts to list artifact_ids needing human review.
```

## Methodology

### 1. Detect Source Type and OCR Tool
Analyze input from `$ARGUMENTS` or content inspection:
- Parse file path or inline content from user invocation
- Apply Source Type Detection logic (see Decision Points)
- Apply OCR Tool Detection logic (see Decision Points)
- If `type == "image"`: ABORT early with guidance (no OCR capability)
- Record `source.type`, `source.tool`, `source.original_filename`, `source.page_number`, `source.region` for IC-13 output
- Set `mode` based on invocation context: `production` (default for Pipeline B) or `drill` (if explicitly requested)

### 2. Clean Raw Content
Apply tool-specific and universal cleanup transformations. Preserve `raw_content` (original) and build `latex_content` (cleaned):

**Universal cleanup (all sources):**
- Normalize Unicode: replace look-alike characters with LaTeX equivalents (e.g., × -> \times, ÷ -> \div, − -> -)
- Normalize whitespace: collapse multiple spaces, normalize line endings, trim trailing whitespace
- Fix common LaTeX structural issues: balance braces, close unclosed environments (mark as WARN artifact)

**Doc Intelligence specific:**
- Remove `:selected:` / `:unselected:` checkbox markers
- Extract math regions from mixed text/math output
- Merge lines broken by page layout (detect continuation patterns)
- Handle Unicode math symbols that Doc Intelligence outputs instead of LaTeX commands

**Mathpix specific:**
- Strip confidence annotations (e.g., `[0.95]` after expressions)
- Normalize `\text{}` wrapping (Mathpix sometimes over-wraps)
- Verify math delimiter consistency (`$...$` vs `\(...\)`)

**Manual/other:**
- Basic whitespace normalization only
- No tool-specific cleanup (risk of removing intentional content)

### 3. Detect OCR Artifacts
Scan cleaned content against known OCR confusion patterns and structural integrity checks:

**Reference-build pattern matching (IC-01 ocr_confusions):**
- Load OCR confusion patterns from `crowd_works/data/reference-cache/{domain}.yaml` if available
- For each known confusion (e.g., theta->9, Delta->A, mu->u, Sigma->E, integral->broken):
  - Scan `latex_content` for instances matching the source (OCR-garbled) form
  - If found: create `flagged_artifact` entry with type `ocr_misrecognition`
  - Set `ocr_pattern_ref` linking back to the IC-01 pattern ID
  - Apply the correction to `latex_content` (replace garbled with correct LaTeX)
  - Set artifact `confidence` based on pattern match certainty

**Built-in minimal OCR confusion list (fallback when reference-build unavailable):**

| OCR Output | Correct | LaTeX | Context |
|------------|---------|-------|---------|
| `9` (digit) | theta | `\theta` | Greek letter context |
| `A` (capital) | Delta | `\Delta` | Change notation |
| `u` (lowercase) | mu | `\mu` | Stats/physics constant |
| `E` (capital) | Sigma | `\Sigma` | Summation context |
| `l` (lowercase L) | 1 (one) | `1` | Numeric expression |
| `0` (zero) | O (letter) | `O` | Variable name context |
| `rn` | m | `m` | Variable name |

**Structural integrity checks:**
- Unclosed environments (`\begin` without `\end`): type `structural_damage`, severity FATAL
- Unbalanced braces: type `structural_damage`, severity FATAL
- Broken LaTeX commands (e.g., `\fra` instead of `\frac`): type `ocr_misrecognition`, severity FAIL
- Orphaned delimiters (`\left` without `\right`): type `structural_damage`, severity FAIL

**For each artifact, record:**
- `artifact_id`: sequential (ART-001, ART-002, ...)
- `type`: one of 6 enum values
- `severity`: FATAL / FAIL / WARN / INFO
- `location`: `{char_start, char_end, line}` in raw_content
- `original_text`: text before correction
- `cleaned_text`: text after correction (or empty if uncorrectable)
- `confidence`: 0.0-1.0 for the correction
- `ocr_pattern_ref`: reference to IC-01 pattern if applicable
- `manual_review`: true if confidence < 0.7 for this artifact

### 4. Calculate Quality Score and Assess Backslash Depth
**Quality score:**
- Compute each dimension per the Quality Score Calculation decision point
- `completeness`: Compare raw_content length and structure against latex_content
- `accuracy`: Weight artifact count by severity (FATAL=1.0, FAIL=0.5, WARN=0.2, INFO=0.05)
- `structure`: Check environment matching, brace balance, command validity
- `cleanliness`: Count extra_content and formatting_loss artifacts
- Overall = 0.30 * completeness + 0.30 * accuracy + 0.25 * structure + 0.15 * cleanliness
- Set `confidence` = overall quality_score (they track together)

**Backslash depth:**
- Apply detection logic from Backslash Depth Assessment decision point
- Build `depth_map`: for each LaTeX command found, record `{command, current_escaping, target_escaping}`
- Set `needs_escaping` flag if any command requires depth adjustment
- Note: image-preprocess does NOT perform the escaping. It reports the depth state for jsonl-validate to handle.

### 5. Generate IC-13 preprocessed_input Output
Assemble the full IC-13 schema output:

```yaml
preprocessed_input:
  file_id: "{generated or from $ARGUMENTS}"
  mode: "production"  # or "drill" if explicitly requested
  preprocessed_at: "{ISO 8601 timestamp}"
  batch_id: null  # or from $ARGUMENTS if batch processing
  source:
    type: "{detected source type}"
    tool: "{detected OCR tool}"
    original_filename: "{from $ARGUMENTS}"
    page_number: null  # if applicable
    region: null  # if applicable
  latex_content: "{cleaned LaTeX}"
  raw_content: "{original input before cleanup}"
  confidence: 0.0-1.0
  confidence_breakdown:
    ocr_accuracy: 0.0-1.0
    artifact_removal: 0.0-1.0
    structural_integrity: 0.0-1.0
  flagged_artifacts:
    - artifact_id: "ART-001"
      type: "{enum}"
      severity: "{enum}"
      location: {char_start: N, char_end: N, line: N}
      original_text: "..."
      cleaned_text: "..."
      confidence: 0.0-1.0
      ocr_pattern_ref: "{IC-01 ref or null}"
      manual_review: true|false
  quality_score:
    overall: 0.0-1.0
    dimensions:
      completeness: 0.0-1.0
      accuracy: 0.0-1.0
      structure: 0.0-1.0
      cleanliness: 0.0-1.0
  backslash_depth:
    current_depth: 0|1|2
    target_depth: 2
    needs_escaping: true|false
    depth_map:
      - command: "\\frac"
        current_escaping: "\\"
        target_escaping: "\\\\"
  hitl_required: true|false
  hitl_reason: "{explanation or null}"
  hitl_artifacts: ["ART-001", ...]  # artifact IDs needing review
```

**Validation before output:**
- `latex_content` and `raw_content` must be non-empty strings
- `confidence` must be 0.0-1.0
- `confidence < 0.7` must imply `hitl_required: true`
- Any FATAL artifact must imply `hitl_required: true`
- `backslash_depth.current_depth` must be 0, 1, or 2

## Failure Handling

### Empty Input
- **Cause**: User invokes with empty path or empty content
- **Action**: ABORT with clear error: "No input content provided. Provide OCR output text or a file path."
- **Route**: Return to Lead. Do not generate partial IC-13 output.

### Unrecognized Source Type
- **Cause**: Content does not match OCR output, LaTeX draft, or image patterns
- **Action**: Default to `source.type = "manual_input"`. Set `source.tool = "manual"`.
- **Route**: Continue with basic cleanup only. Add WARN: "Source type unrecognized, applied minimal cleanup."

### Image File Without OCR
- **Cause**: User provides .png/.jpg/.pdf path (binary image, not OCR output)
- **Action**: ABORT with guidance: "Image files require external OCR processing first. Use Doc Intelligence or Mathpix to extract text, then re-invoke with the OCR output."
- **Route**: Return to Lead. Suggest OCR tool options.

### All Artifacts FATAL
- **Cause**: Every detected artifact has FATAL severity (content unrecoverable)
- **Action**: Set `hitl_required: true`, `confidence` very low (< 0.3), generate IC-13 output with all artifacts documented.
- **Route**: jsonl-validate will receive the low-confidence output. HITL queue activated.

### Reference-Build Patterns Unavailable
- **Cause**: No `crowd_works/data/reference-cache/{domain}.yaml` exists for the target domain
- **Action**: Fall back to built-in minimal OCR confusion list (7 universal patterns). Add INFO artifact: "Reference-build patterns not available, using built-in fallback."
- **Route**: Continue normally. Suggest running `/reference-build [domain]` to improve detection.

### Content Too Large
- **Cause**: OCR output exceeds practical processing size (e.g., full document dump)
- **Action**: Process first N pages/sections. Set `hitl_required: true` with reason "partial processing due to content size."
- **Route**: jsonl-validate receives partial output. Lead may need to split into batch.

### Backslash Depth Ambiguous
- **Cause**: Mixed escaping depths within the same content (some commands at depth 0, others at depth 1)
- **Action**: Report `current_depth` as the majority depth. Add WARN artifacts for inconsistent commands. Flag in `depth_map`.
- **Route**: jsonl-validate will normalize based on reported depth_map.

## Anti-Patterns

### DO NOT: Attempt OCR
This skill has NO image processing capability. It only CLEANS OCR output that has already been produced by an external tool. If the user provides a raw image, ABORT with guidance.

### DO NOT: Modify Mathematical Meaning
Cleanup must preserve mathematical semantics. Fix encoding artifacts (`\u00D7` -> `\times`) and structural damage (unclosed environments), but NEVER change the mathematical content. `\frac{a}{b}` must not become `\frac{b}{a}`.

### DO NOT: Assume Backslash Depth
Always detect depth from content analysis. Do not assume depth 0 just because the content "looks like raw LaTeX." OCR tools may output at depth 1 if they produce JSON-wrapped output.

### DO NOT: Auto-Fix FATAL Artifacts
FATAL severity means content is unrecoverable without the original source. Flag for human review (`manual_review: true`). Do not guess at corrections -- guessing corrupts data.

### DO NOT: Discard Raw Content
Always preserve `raw_content` alongside `latex_content`. The raw form is the audit trail. jsonl-validate and downstream skills may need it for comparison.

### DO NOT: Skip Built-in Fallback Patterns
Even when reference-build patterns are available, also check the 7 universal OCR confusions. These are cross-domain patterns that individual domain references might not include.

### DO NOT: Output Without Schema Validation
Every IC-13 output must pass the validation rules before emission. Do not output a `preprocessed_input` with empty `latex_content`, missing `confidence`, or incorrect `hitl_required` logic.

## Transitions

### Receives From
| Source | Data Expected | Key Fields | Format |
|--------|--------------|------------|--------|
| User | OCR output or file path | Content text or file path | `$ARGUMENTS` (natural language or path) |
| reference-build | OCR confusion patterns | `ocr_confusions[]` (source_char, target_char, latex_correct, frequency) | YAML from `reference-cache/{domain}.yaml` (IC-01) |
| Lead | Mode override | `mode: drill\|production` | `$ARGUMENTS` context |

### Sends To
| Target Skill | Data Produced | Key Fields (IC ref) | Trigger |
|-------------|---------------|---------------------|---------|
| jsonl-validate | IC-13 preprocessed_input | `file_id`, `mode`, `latex_content`, `raw_content`, `confidence`, `flagged_artifacts`, `backslash_depth`, `quality_score`, `hitl_required` | Always (on successful processing) |
| latex-parse | Flagged artifacts for cross-reference | `flagged_artifacts[]` with OCR artifact tags | Production mode (indirect, via IC-13) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Empty input | Lead (abort) | Error message: no content provided |
| Image file (no OCR) | Lead (abort) | Guidance: run external OCR first |
| All FATAL artifacts | jsonl-validate (degraded) | IC-13 with very low confidence + hitl_required=true |
| Reference patterns missing | jsonl-validate (normal) | IC-13 with built-in fallback patterns used |

## Quality Gate
- IC-13 `preprocessed_input` conforms to full schema (all REQUIRED fields present)
- `latex_content` is non-empty string
- `raw_content` is non-empty string and preserves original input exactly
- `confidence` is within 0.0-1.0 range
- `confidence < 0.7` correctly implies `hitl_required: true`
- Any FATAL-severity artifact correctly implies `hitl_required: true`
- `backslash_depth.current_depth` is 0, 1, or 2
- `backslash_depth.target_depth` is always 2 (JSONL target)
- All `flagged_artifacts` have valid `type` and `severity` enum values
- `quality_score.overall` matches weighted average of 4 dimensions (within rounding)
- `quality_score` dimensions are all within 0.0-1.0
- Source type and tool detection are consistent (e.g., `tool: doc_intelligence` only with `type: ocr_output`)
- `hitl_artifacts` array contains only artifact_ids that exist in `flagged_artifacts`
- No artifact has `manual_review: true` without corresponding entry in `hitl_artifacts`

## Output

### L1
```yaml
domain: foundation
skill: image-preprocess
status: complete|partial|abort
file_id: string
mode: drill|production
source_type: ocr_output|latex_draft|image|manual_input
source_tool: doc_intelligence|mathpix|manual|other
confidence: 0.0-1.0
artifact_count: 0
artifact_severity:
  FATAL: 0
  FAIL: 0
  WARN: 0
  INFO: 0
quality_score: 0.0-1.0
quality_dimensions:
  completeness: 0.0-1.0
  accuracy: 0.0-1.0
  structure: 0.0-1.0
  cleanliness: 0.0-1.0
backslash_depth:
  current: 0|1|2
  target: 2
  needs_escaping: true|false
hitl_required: true|false
hitl_reason: string|null
contract_compliance:
  ic13_preprocessed_input: true|false
```

### L2
- Source detection analysis: type, tool, detection rationale
- Cleanup transformation log: each change applied with before/after
- Artifact detail table: all flagged_artifacts with type, severity, location, original/cleaned text, confidence
- OCR pattern matching results: which IC-01 patterns matched, which corrections applied
- Quality dimension breakdown: per-dimension score with calculation evidence
- Backslash depth analysis: depth_map table showing per-command current vs target escaping
- HITL decision rationale: confidence breakdown, trigger conditions met
- Full IC-13 `preprocessed_input` output block
