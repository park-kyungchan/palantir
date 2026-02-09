# Mathpix API v3 — Comprehensive Reference

> Last updated: 2026-02-09
> Source: Official docs (docs.mathpix.com, mathpix.com/docs/convert/*, mathpix.github.io/docs),
> blog posts (supernet, figure-labels, streaming-api-for-pdfs, mathpix-text-endpoint),
> Python SDK (mpxpy), and API changelog.

---

## Table of Contents

1. [Authentication](#1-authentication)
2. [POST /v3/text — Image OCR](#2-post-v3text--image-ocr)
3. [POST /v3/pdf — Document OCR](#3-post-v3pdf--document-ocr)
4. [POST /v3/converter — Format Conversion](#4-post-v3converter--format-conversion)
5. [Line Data Reference](#5-line-data-reference)
6. [Word Data Reference](#6-word-data-reference)
7. [Geometry Data Reference](#7-geometry-data-reference)
8. [Error Codes](#8-error-codes)
9. [Rate Limits and Constraints](#9-rate-limits-and-constraints)
10. [Regional Endpoints](#10-regional-endpoints)
11. [Gotchas and Pipeline Notes](#11-gotchas-and-pipeline-notes)

---

## 1. Authentication

### Server-Side (API Keys)

All requests require two headers:

| Header    | Type   | Description                |
|-----------|--------|----------------------------|
| `app_id`  | string | Application identifier     |
| `app_key` | string | Application secret key     |

### Client-Side (App Tokens)

For browser/mobile apps that should not embed API keys:

```
POST /v3/app-tokens
Header: app_key: YOUR_APP_KEY
Response: { "app_token": "...", "app_token_expires_at": "..." }
```

- Token expires in 5 minutes (configurable).
- App tokens grant free requests but cannot access PDF, batch, or historical data endpoints.
- Use `app_token` header instead of `app_key` in subsequent requests.

---

## 2. POST /v3/text — Image OCR

**Base URL:** `https://api.mathpix.com/v3/text`
**Content-Type:** `application/json`

Processes a single image to extract text, math, tables, diagrams, and chemistry.

### 2.1 Request Parameters

#### Core Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `src` | string | Yes | — | Base64-encoded image (`data:image/jpeg;base64,...`) or public URL |
| `formats` | string[] | No | `["text"]` | Output formats to include in response |
| `data_options` | object | No | `{}` | Controls sub-formats within `"data"` output |

#### Format Values (for `formats` array)

| Value | Description |
|-------|-------------|
| `"text"` | Mathpix Markdown (MMD) with LaTeX math delimiters. Always set if readable content exists. |
| `"data"` | Structured data array — requires `data_options` to specify sub-formats |
| `"html"` | HTML markup with rendered math |
| `"latex_styled"` | Enhanced visual LaTeX. Omitted for text-heavy images where ambiguity exists. |

> **Note:** The legacy `/v3/latex` endpoint supports additional formats: `latex_normal`,
> `latex_simplified`, `latex_list`, `mathml`, `wolfram`. These are **not** available
> on `/v3/text`.

#### data_options Object

Only relevant when `"data"` is included in `formats`.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `include_asciimath` | bool | false | Include AsciiMath representation in data array |
| `include_latex` | bool | false | Include LaTeX representation in data array |
| `include_mathml` | bool | false | Include MathML representation in data array |
| `include_tsv` | bool | false | Include TSV for tables in data array |
| `include_table_html` | bool | false | Include HTML table markup in data array |

#### Segmentation Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `include_line_data` | bool | false | Return `line_data` array with per-line segmentation |
| `include_word_data` | bool | false | Return `word_data` array with per-word segmentation |
| `include_geometry_data` | bool | false | Return `geometry_data` for triangle shapes (**DEPRECATED** — diagram labels remain) |
| `include_diagram_text` | bool | false | Extract text fragments inside diagrams/charts. **Requires `include_line_data: true`** for v3/text. |
| `include_page_info` | bool | true | Include page info elements (headers, rotated text) in output |

> **IMPORTANT — `include_line_data` + `include_word_data` are MUTUALLY EXCLUSIVE.**
> Setting both to `true` returns `opts_conflict` error:
> `"Requesting both line data and word data is not supported."`
> Verified via live API test (2026-02-09). Official docs may suggest otherwise,
> but actual API behavior is the ground truth. COW pipeline uses `include_line_data` only.

#### Content Extraction Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `include_smiles` | bool | true | Extract SMILES notation from chemistry diagrams (since Aug 2024) |
| `include_inchi` | bool | false | Include InChI data as XML attributes inside `<smiles>` elements |
| `include_chemistry_as_image` | bool | false | Return chemistry as image crops with SMILES in alt-text (since Sep 2024) |
| `include_equation_tags` | bool | false | Enable equation number recognition via `\tag{}` (since Feb 2024) |
| `include_detected_alphabets` | bool | false | Return `detected_alphabets` object in response |

#### Math & Text Formatting

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `math_inline_delimiters` | string[] | `["\\(", "\\)"]` | Custom inline math delimiters (array of 2 strings) |
| `rm_spaces` | bool | false | Remove excess whitespace from equations |
| `rm_fonts` | bool | false | Strip font commands from LaTeX |
| `idiomatic_eqn_arrays` | bool | false | Use `aligned`/`gathered` environments instead of `array` |
| `numbers_default_to_math` | bool | false | Treat standalone numbers as math mode |
| `fullwidth_punctuation` | bool | — | Control fullwidth/halfwidth Unicode punctuation (since Jan 2025) |

#### Language Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `alphabets_allowed` | object | all true | Map of alphabet code -> bool. Set false to suppress unwanted scripts. |

Known alphabet codes: `en`, `zh`, `ja`, `ko`, `ru`, `hi`, `th`, `ta`, `te`, `gu`, `bn`, `vi`, `ar`, `he`

#### Confidence & Quality

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `confidence_threshold` | number | — | Overall confidence minimum [0, 1]. Returns error if below. |
| `confidence_rate_threshold` | number | 0.75 | Per-character confidence minimum [0, 1] |

#### Async & Callback

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `is_async` | bool | false | Non-blocking request. Use with `tags` for later retrieval. |
| `tags` | string[] | — | Identifiers for retrieving results via `GET /v3/ocr-results` |
| `callback` | object | — | Webhook configuration (see below) |

**Callback Object:**

| Key | Type | Description |
|-----|------|-------------|
| `callback.post` | string | URL to POST results to |
| `callback.reply` | string | Override session_id in response |
| `callback.body` | object | Additional data to include in callback POST |
| `callback.headers` | object | Custom headers for callback POST |

#### Miscellaneous

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `region` | object | — | Crop area: `{ top_left_x, top_left_y, width, height }` |
| `skip_recrop` | bool | false | Skip auto-cropping of detected content area |
| `improve_mathpix` | bool | true | Allow Mathpix to retain data for service improvement. Set false to opt out. |

### 2.2 Response Schema

```json
{
  "request_id": "string",
  "text": "string — Mathpix Markdown output",
  "html": "string — HTML output (if requested)",
  "data": [
    {
      "type": "asciimath|latex|mathml|tsv|table_html",
      "value": "string"
    }
  ],
  "latex_styled": "string — styled LaTeX (if requested)",
  "confidence": 0.99,
  "confidence_rate": 0.98,
  "is_printed": true,
  "is_handwritten": false,
  "auto_rotate_degrees": 0,
  "auto_rotate_confidence": 0.01,
  "detected_alphabets": {
    "en": true,
    "ko": false,
    "zh": false
  },
  "line_data": [ "...see §5..." ],
  "word_data": [ "...see §6..." ],
  "geometry_data": [ "...see §7..." ],
  "error": "string — human-readable error message",
  "error_info": {
    "id": "string — machine-readable error ID",
    "message": "string — detailed description",
    "detail": {}
  }
}
```

**Field Presence Rules:**
- `text`: Always present when readable content exists.
- `latex_styled`: Omitted for text-heavy images where math/text ambiguity exists.
- `html`, `data`: Only present when requested via `formats`.
- `line_data`, `word_data`, `geometry_data`: Only present when respective `include_*` is true.
- `detected_alphabets`: Only present when `include_detected_alphabets` is true.
- `error`, `error_info`: Only present on error.
- `auto_rotate_degrees`: In set {0, 90, -90, 180}. Value 0 = correct orientation.
- `auto_rotate_confidence`: ~0 if correct orientation, ~1 if rotation needed.

### 2.3 Example Request

```json
{
  "src": "data:image/png;base64,iVBOR...",
  "formats": ["text", "data", "html"],
  "data_options": {
    "include_latex": true,
    "include_table_html": true
  },
  "include_line_data": true,
  "include_smiles": true,
  "include_diagram_text": true,
  "include_equation_tags": true,
  "include_detected_alphabets": true,
  "math_inline_delimiters": ["$", "$"],
  "rm_spaces": true,
  "idiomatic_eqn_arrays": true
}
```

---

## 3. POST /v3/pdf — Document OCR

**Base URL:** `https://api.mathpix.com/v3/pdf`
**Content-Type:** `multipart/form-data`

Asynchronous endpoint for processing PDFs and other document formats.

### 3.1 Supported Input Formats

PDF, EPUB, DOCX, PPTX, AZW, AZW3, KFX, MOBI, DJVU, DOC, WPD, ODT

### 3.2 Upload Request

Two upload methods:

**Method A — File upload (multipart/form-data):**

| Field | Type | Description |
|-------|------|-------------|
| `file` | binary | The document file |
| `options_json` | string | JSON-encoded options (see below) |

```bash
curl -X POST 'https://api.mathpix.com/v3/pdf' \
  -H 'app_id: APP_ID' \
  -H 'app_key: APP_KEY' \
  -F 'file=@"document.pdf"' \
  -F 'options_json="{\"conversion_formats\":{\"docx\":true},\"math_inline_delimiters\":[\"$\",\"$\"]}"'
```

**Method B — URL reference (JSON body):**

```json
{
  "url": "https://example.com/document.pdf",
  "conversion_formats": { "docx": true },
  "math_inline_delimiters": ["$", "$"]
}
```

### 3.3 options_json Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `conversion_formats` | object | — | Output formats to generate (see below) |
| `page_ranges` | string | all | Specific pages: `"2,4-6,10"` |
| `streaming` | bool | false | Enable SSE streaming of page results |
| `math_inline_delimiters` | string[] | `["\\(", "\\)"]` | Custom inline math delimiters |
| `include_smiles` | bool | true | Extract SMILES from chemistry |
| `include_diagram_text` | bool | false | Extract text from diagrams |
| `include_page_info` | bool | false | Include page info elements |
| `include_equation_tags` | bool | false | Equation number recognition |
| `idiomatic_eqn_arrays` | bool | false | Use aligned/gathered |
| `fullwidth_punctuation` | bool | — | Control Unicode punctuation |
| `max_character_per_line` | int | — | Limit line length in Markdown output (min 10, since Apr 2025) |
| `footnote_compact_refs` | bool | false | Hide repeat indices for footnotes (since Feb 2025) |
| `include_chemistry_as_image` | bool | false | Chemistry as image crops |

#### conversion_formats Object

| Key | Type | Description |
|-----|------|-------------|
| `docx` | bool | Microsoft Word (.docx) |
| `tex.zip` | bool | LaTeX sources + images (.tex.zip) |
| `html` | bool | Self-contained HTML |
| `pptx` | bool | PowerPoint |
| `mmd` | bool | Mathpix Markdown (default output) |
| `md` | bool | Plain UTF-8 Markdown |

### 3.4 Upload Response

```json
{
  "pdf_id": "abc123def456"
}
```

### 3.5 Polling — GET /v3/pdf/{pdf_id}

Poll this endpoint to check processing status.

```json
{
  "status": "completed",
  "num_pages": 12,
  "num_pages_completed": 12,
  "percent_done": 100,
  "conversion_status": {
    "docx": { "status": "completed" },
    "tex.zip": { "status": "processing" }
  }
}
```

**Status values:** `"processing"`, `"completed"`, `"error"`

### 3.6 Output Retrieval

Once `status` is `"completed"`, retrieve outputs by appending the format extension:

| URL Pattern | Format | Description |
|-------------|--------|-------------|
| `GET /v3/pdf/{pdf_id}.mmd` | Mathpix Markdown | Always available |
| `GET /v3/pdf/{pdf_id}.docx` | Word | Requires `docx: true` |
| `GET /v3/pdf/{pdf_id}.tex.zip` | LaTeX bundle | Requires `tex.zip: true` |
| `GET /v3/pdf/{pdf_id}.html` | HTML | Requires `html: true` |
| `GET /v3/pdf/{pdf_id}.lines.json` | Line data (JSON) | Always available |
| `GET /v3/pdf/{pdf_id}.lines.mmd.json` | Line data (MMD content) | Always available |
| `GET /v3/pdf/{pdf_id}.md` | Plain Markdown | Requires `md: true` |

> **conversion_status** is a nested object — the top-level `status` reflects OCR completion,
> while each format has its own `status` that may still be `"processing"` after OCR completes.

### 3.7 Streaming — GET /v3/pdf/{pdf_id}/stream

When `streaming: true` is set in the upload request, page results stream via Server-Sent Events (SSE).

Each SSE event contains a JSON message with:

```json
{
  "text": "string — Mathpix Markdown for this page",
  "page_idx": 0,
  "pdf_selected_len": 1234
}
```

- Results arrive sequentially by page.
- First results appear in 2-3 seconds, even for PDFs that take 20+ seconds total.
- Streaming may slightly increase total processing time but dramatically lowers time-to-first-data.
- Eliminates need for polling.

### 3.8 .lines.json Structure

The `.lines.json` response is a JSON array where each element is a line data object.
Fields are identical to `line_data` in `/v3/text` (see [Section 5](#5-line-data-reference)),
with the addition of:

- `confidence` and `confidence_rate` fields on each line (added Feb 2025)
- Page-level grouping (lines are ordered by page)

---

## 4. POST /v3/converter — Format Conversion

**Base URL:** `https://api.mathpix.com/v3/converter`
**Content-Type:** `application/json`
**Max body size:** 10 MB

Converts existing Mathpix Markdown (MMD) to other document formats. No OCR involved.

### 4.1 Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `mmd` | string | Yes | Full Mathpix Markdown text to convert |
| `formats` | object | Yes | Target formats (see below) |
| `conversion_options` | object | No | Format-specific settings |

#### formats Object

| Key | Type | Description |
|-----|------|-------------|
| `docx` | bool | Microsoft Word |
| `tex.zip` | bool | LaTeX + images bundle |
| `html` | bool | Self-contained HTML |
| `pdf` | bool | PDF (rendered from MMD) |
| `latex.pdf` | bool | PDF (rendered from LaTeX) |
| `pptx` | bool | PowerPoint |
| `md` | bool | Plain Markdown |
| `mmd.zip` | bool | MMD + images bundle |
| `md.zip` | bool | Markdown + images bundle |
| `html.zip` | bool | HTML + images bundle |

#### conversion_options Object

| Key | Type | Description |
|-----|------|-------------|
| `resource_load_timeout_sec` | int | Timeout for loading external resources during HTML-to-PDF (since Aug 2025) |

### 4.2 Response

```json
{
  "conversion_id": "abc123def456"
}
```

### 4.3 Polling — GET /v3/converter/{conversion_id}

Same pattern as PDF polling:

```json
{
  "status": "completed",
  "conversion_status": {
    "docx": { "status": "completed" },
    "pdf": { "status": "completed" }
  }
}
```

### 4.4 Output Retrieval

| URL Pattern | Format |
|-------------|--------|
| `GET /v3/converter/{conversion_id}.docx` | Word |
| `GET /v3/converter/{conversion_id}.tex.zip` | LaTeX bundle |
| `GET /v3/converter/{conversion_id}.html` | HTML |
| `GET /v3/converter/{conversion_id}.pdf` | PDF |
| `GET /v3/converter/{conversion_id}.latex.pdf` | LaTeX-rendered PDF |

### 4.5 Example

```python
import requests, json, time

url = "https://api.mathpix.com/v3/converter"
headers = {
    "app_id": "APP_ID",
    "app_key": "APP_KEY",
    "Content-Type": "application/json"
}

# Step 1: Submit conversion
payload = {
    "mmd": "# Title\n\nThe equation $E = mc^2$ is famous.\n",
    "formats": { "pdf": True, "docx": True }
}
resp = requests.post(url, headers=headers, json=payload)
conversion_id = resp.json()["conversion_id"]

# Step 2: Poll until complete
while True:
    status = requests.get(f"{url}/{conversion_id}", headers=headers).json()
    if status["status"] == "completed":
        break
    time.sleep(2)

# Step 3: Download output
pdf_bytes = requests.get(f"{url}/{conversion_id}.pdf", headers=headers).content
```

---

## 5. Line Data Reference

Returned in `line_data` array when `include_line_data: true` (v3/text) or in `.lines.json` (v3/pdf).

### 5.1 LineData Object Schema

| Field | Type | Always Present | Description |
|-------|------|----------------|-------------|
| `id` | string | Yes (since Apr 2025) | Unique identifier for this line |
| `type` | string | Yes | Primary element classification (see §5.2) |
| `subtype` | string | No | Sub-classification (see §5.2) |
| `text` | string | Yes | Content in Mathpix Markdown |
| `text_display` | string | No | Formatted/styled version (since Apr 2025) |
| `html` | string | No | HTML rendering of this line |
| `cnt` | number[][] | Yes | Polygon coordinates as `[[x1,y1], [x2,y2], ...]` in pixel coords |
| `confidence` | number | Yes | Recognition confidence [0, 1] |
| `confidence_rate` | number | No | Per-character confidence [0, 1] |
| `is_printed` | bool | No | Content is printed (since Dec 2023) |
| `is_handwritten` | bool | No | Content is handwritten (since Dec 2023) |
| `included` | bool | No | Whether this line contributed to top-level `text` field |
| `parent_id` | string | No | ID of parent container (since Apr 2025) |
| `children_ids` | string[] | No | IDs of child elements (since Apr 2025) |
| `conversion_output` | bool | No | `true` if included in converted output (MMD/DOCX/HTML/LaTeX); `false` for metadata like extracted diagram text (since Apr 2025) |
| `selected_labels` | string[] | No | List of associated `figure_label` line IDs (since Aug 2025) |

### 5.2 Type and Subtype Values

#### Content Types

| Type | Subtypes | Description |
|------|----------|-------------|
| `text` | `vertical`, `big_capital_letter` | Standard text content |
| `math` | — | Mathematical expression (inline or display) |
| `table` | — | Table content |
| `diagram` | `algorithm`, `pseudocode`, `chemistry`, `chemistry_reaction`, `triangle` | Visual diagram |
| `chart` | `column`, `bar`, `line`, `analytical`, `pie`, `scatter`, `area` | Data visualization |
| `code` | — | Code block |
| `form_field` | `parentheses`, `dotted`, `dashed`, `box`, `checkbox`, `circle` | Form input field (since Apr 2024) |

#### Metadata Types

| Type | Subtypes | Description |
|------|----------|-------------|
| `figure_label` | — | Caption text for diagrams/tables/charts (since Aug 2025) |
| `equation_number` | — | Equation numbering label |
| `chart_info` | — | Extracted chart labels and information |
| `diagram_info` | — | Extracted diagram metadata |
| `page_info` | — | Page-level elements (headers, footers, rotated text) |
| `column` | — | Column layout indicator |
| `pseudocode` | — | Pseudocode block |
| `qed_symbol` | — | End-of-proof marker |
| `x_axis_tick_label` | — | Chart X-axis tick label |
| `y_axis_tick_label` | — | Chart Y-axis tick label |
| `x_axis_label` | — | Chart X-axis title |
| `y_axis_label` | — | Chart Y-axis title |
| `legend_label` | — | Chart legend label |
| `model_label` | — | Chart model label |

#### Math Classification Notes

- Math is always `type: "math"` — there is no inline/display distinction at the type level.
- Inline vs display is determined by the delimiters in the `text` field:
  - Inline: `\( ... \)` (or custom `math_inline_delimiters`)
  - Display: `\[ ... \]`
- Equation numbers are separate `type: "equation_number"` lines.

#### Diagram Hierarchies

- A `diagram` line can have `children_ids` pointing to nested text/math lines extracted from within it.
- `include_diagram_text: true` populates these child lines.
- Child lines have `conversion_output: false` (they are metadata, not in final output).
- `selected_labels` on a diagram/table links to `figure_label` caption lines.

### 5.3 The `cnt` Coordinate System

- Coordinates are in **pixel space** of the original image (or PDF page).
- Format: array of [x, y] pairs forming a polygon (typically 4 corners for a rectangle).
- Corner order: typically counter-clockwise from bottom-left, but NOT guaranteed.
- Example: `[[111, 104], [3, 104], [3, 74], [111, 74]]`

**Converting `cnt` to bounding box:**
```python
xs = [p[0] for p in cnt]
ys = [p[1] for p in cnt]
bbox = {
    "x": min(xs),
    "y": min(ys),
    "width": max(xs) - min(xs),
    "height": max(ys) - min(ys)
}
```

---

## 6. Word Data Reference

Returned in `word_data` array when `include_word_data: true` (v3/text only).

### 6.1 WordData Object Schema

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Content type: `"text"`, `"math"`, `"table"`, `"diagram"` |
| `text` | string | Actual text content (e.g., `"Perform"`) |
| `latex` | string | LaTeX representation (e.g., `"\\text { Perform }"`) |
| `cnt` | number[][] | Bounding box as polygon coordinates `[[x,y], ...]` |
| `confidence` | number | Recognition confidence [0, 1] |
| `confidence_rate` | number | Per-character confidence [0, 1] |

### 6.2 Line Data vs Word Data

| Aspect | `line_data` | `word_data` |
|--------|-------------|-------------|
| Granularity | Line-level (sentences, equations) | Word-level (individual words) |
| Hierarchy | Has `parent_id`/`children_ids` | Flat list |
| Type variety | 15+ types (text, math, diagram, chart...) | 4 types (text, math, table, diagram) |
| Extra fields | `html`, `text_display`, `selected_labels` | `latex` |
| PDF support | Yes (`.lines.json`) | v3/text only |

**MUTUALLY EXCLUSIVE with `include_line_data`.** Despite official docs suggesting independence,
live API returns `opts_conflict` when both are true (verified 2026-02-09).
COW pipeline uses `include_line_data` only (richer type system, hierarchy support).

---

## 7. Geometry Data Reference

**STATUS: DEPRECATED** — Triangle shape extraction is being phased out.
Diagram label outputs remain unchanged.

Returned in `geometry_data` when `include_geometry_data: true`.

### 7.1 Structure

```json
{
  "geometry_data": [
    {
      "position": {
        "top_left_x": 50,
        "top_left_y": 100,
        "height": 200,
        "width": 300
      },
      "shape_list": [
        {
          "type": "triangle",
          "vertex_list": [
            {
              "x": 100, "y": 150,
              "edge_list": [
                { "start_x": 100, "start_y": 150, "end_x": 250, "end_y": 300 }
              ]
            }
          ]
        }
      ],
      "label_list": [
        {
          "position": { "top_left_x": 80, "top_left_y": 130, "height": 20, "width": 30 },
          "text": "A",
          "latex": "A",
          "confidence": 0.95
        }
      ]
    }
  ]
}
```

> **Recommendation:** Use `include_diagram_text: true` with `include_line_data: true` instead
> for general diagram content extraction. Geometry data only ever supported triangles.

---

## 8. Error Codes

### 8.1 HTTP-Level Errors

| Error ID | HTTP Status | Description |
|----------|-------------|-------------|
| `http_unauthorized` | 401 | Invalid `app_id` or `app_key` |
| `http_max_requests` | 429 | Rate limit exceeded (50 req/min default) |

### 8.2 Request-Level Errors (HTTP 200 with error body)

| Error ID | Description |
|----------|-------------|
| `json_syntax` | Malformed JSON in request body |
| `image_missing` | No `src` URL or base64 data in request |
| `image_download_error` | Could not download image from URL |
| `image_decode_error` | Could not decode image data |
| `image_no_content` | Image is empty or has no recognizable content |
| `image_not_supported` | OCR engine does not accept this line type |
| `image_max_size` | Image exceeds maximum size limit |
| `math_confidence` | Recognition confidence below `confidence_threshold` |
| `math_syntax` | Generated LaTeX has syntax errors |
| `batch_unknown_id` | Batch ID not found |

### 8.3 Options Errors (HTTP 200)

Error IDs beginning with `opts_` indicate request body option problems:

| Error Pattern | Description |
|---------------|-------------|
| `opts_unknown_format` | Unrecognized value in `formats` array |
| `opts_conflict` | Conflicting parameters in request body |
| `opts_bad_callback` | Invalid `callback.post` URL or structure |
| `opts_bad_batch_id` | Invalid batch_id reference |

### 8.4 Python SDK Error Types

| Exception Class | Trigger |
|----------------|---------|
| `AuthenticationError` | Missing or invalid credentials |
| `ValidationError` | Missing, conflicting, or malformed parameters |
| `FilesystemError` | File path access issues |
| `ConversionIncompleteError` | Attempting to retrieve output before conversion is finished |
| `MathpixClientError` | General unexpected errors |

### 8.5 Error Response Format

```json
{
  "error": "Human-readable error message",
  "error_info": {
    "id": "machine_readable_error_id",
    "message": "Detailed description",
    "detail": {}
  }
}
```

---

## 9. Rate Limits and Constraints

### 9.1 Rate Limits

| Endpoint | Default Limit | Notes |
|----------|---------------|-------|
| `v3/text` | 50 requests/minute | Can be increased on request |
| `v3/latex` | 50 requests/minute | Shared with v3/text limit |
| `v3/batch` | 50 requests/minute | Shared limit |
| `v3/pdf` | 5,000 pages/month | Can be increased on request |

Contact support@mathpix.com for custom limits.

### 9.2 Size Limits

| Resource | Limit | Notes |
|----------|-------|-------|
| Image | ~100 KB recommended | Larger images work but add latency proportional to size |
| Image (max) | Not published | Returns `image_max_size` error when exceeded |
| JSON body (converter) | 10 MB | Hard limit for `/v3/converter` requests |
| PDF file (upload) | 1 GB | Maximum file size for `/v3/pdf` |

### 9.3 Supported Image Formats

JPEG, PNG, BMP, JPEG 2000, WebP, TIFF (and formats compatible with OpenCV/GDAL)

### 9.4 Data Retention

- Batch results: Retained approximately 2 days (subject to change).
- PDF results: Check Mathpix Console for retention policy.
- Set `improve_mathpix: false` to prevent data retention for model improvement.

### 9.5 Pricing (as of 2026)

| Endpoint | First 1M | Next 500K |
|----------|----------|-----------|
| `v3/text` | $0.002/request | $0.0015/request |
| `v3/pdf` | $0.005/page | $0.0035/page |

---

## 10. Regional Endpoints

| Region | Base URL | Use Case |
|--------|----------|----------|
| US East (Virginia) | `https://api.mathpix.com/` | Default |
| EU Central (Frankfurt) | `https://eu-central-1.api.mathpix.com/` | EU data compliance (GDPR) |
| SE Asia (Singapore) | Available | Low-latency Asia Pacific |

Implement latency-based routing for global deployments.

---

## 11. Gotchas and Pipeline Notes

### 11.1 Common Pitfalls

1. **`include_diagram_text` requires `include_line_data`** — On v3/text, setting
   `include_diagram_text: true` without `include_line_data: true` will silently produce
   no diagram text in the response.

2. **`include_geometry_data` is deprecated** — Triangle extraction is being phased out.
   Use `include_diagram_text` for general diagram content instead.

3. **Conversion format status is nested** — After `status: "completed"` at the top level,
   individual formats may still be `"processing"`. Always check `conversion_status.{format}.status`.

4. **`latex_styled` is NOT always returned** — For text-heavy images, this field is omitted
   to avoid ambiguity. Do not assume its presence.

5. **v3/text vs v3/latex** — The newer `v3/text` strips cosmetic newlines, uses `\( \)` delimiters,
   and provides `text`/`latex_styled` only (not `mathml`/`wolfram`). Always prefer `v3/text`.

6. **Parameter rename** — `expand_chemistry` was renamed to `include_chemistry` (Jan 2024).
   The old name may cause `opts_conflict`.

7. **Section numbering mutual exclusion** — Only ONE of `auto_number_sections`,
   `remove_section_numbering`, or `preserve_section_numbering` can be true.

### 11.2 COW Pipeline Mapping

The COW pipeline's `BBox` model uses `(x, y, width, height)` format, but Mathpix
returns `cnt` as polygon coordinates `[[x,y], ...]`. Required transformation:

```python
def cnt_to_bbox(cnt: list[list[int]]) -> BBox:
    """Convert Mathpix cnt polygon to COW BBox."""
    xs = [p[0] for p in cnt]
    ys = [p[1] for p in cnt]
    return BBox(
        x=min(xs),
        y=min(ys),
        width=max(xs) - min(xs),
        height=max(ys) - min(ys)
    )
```

The COW `OcrRegion.type` Literal covers: `"text"`, `"math"`, `"table"`, `"diagram"`,
`"chart"`, `"figure"`, `"equation_number"`. Mathpix returns additional types
(`code`, `form_field`, `page_info`, `chart_info`, etc.) that need mapping or filtering.

### 11.3 Changelog Highlights (2024-2025)

| Date | Change | Impact |
|------|--------|--------|
| 2025-08-11 | `include_page_info` added | v3/text default true, v3/pdf default false |
| 2025-08-04 | `figure_label` type + `selected_labels` field | New diagram-caption linking |
| 2025-08-04 | Figures wrapped in `\begin{figure}...\end{figure}` | MMD output format change |
| 2025-07-15 | `enable_spelling_correction` deprecated | Remove from requests |
| 2025-04-16 | `id`, `parent_id`, `children_ids`, `text_display`, `conversion_output` added | Document tree structure in line data |
| 2025-04-16 | `include_diagram_text` option | Diagram text extraction |
| 2025-02-05 | `confidence`/`confidence_rate` added to PDF lines | Lines.json quality metrics |
| 2024-10-31 | Chart detection with subtypes | New chart type in line_data |
| 2024-09-30 | `include_chemistry_as_image` | Chemistry image crops |
| 2024-08-14 | `include_smiles` default true | Chemistry SMILES always on |
| 2024-05-20 | `analytical` chart subtype | New chart variant |
| 2024-04-04 | `form_field` type | Form recognition |
| 2024-02-06 | `include_equation_tags` | Equation numbering |
| 2024-01-16 | `expand_chemistry` renamed to `include_chemistry` | Breaking change |
| 2023-12-28 | `is_printed`/`is_handwritten` in line data | Content type detection |

---

## Appendix A: Quick Reference Card

### Minimum Viable Request (Image OCR)

```json
POST /v3/text
Headers: app_id, app_key, Content-Type: application/json

{ "src": "data:image/png;base64,..." }
```

### Full-Featured Request (Image OCR)

```json
{
  "src": "data:image/png;base64,...",
  "formats": ["text", "data", "html", "latex_styled"],
  "data_options": {
    "include_asciimath": true,
    "include_latex": true,
    "include_mathml": true,
    "include_tsv": true,
    "include_table_html": true
  },
  "include_line_data": true,
  "include_smiles": true,
  "include_inchi": true,
  "include_diagram_text": true,
  "include_detected_alphabets": true,
  "include_equation_tags": true,
  "include_page_info": true,
  "math_inline_delimiters": ["$", "$"],
  "rm_spaces": true,
  "idiomatic_eqn_arrays": true,
  "confidence_threshold": 0.3,
  "improve_mathpix": false
}
```

### PDF Upload + Polling Pattern

```python
import requests, time

BASE = "https://api.mathpix.com"
HEADERS = {"app_id": "...", "app_key": "..."}

# Upload
resp = requests.post(f"{BASE}/v3/pdf",
    headers=HEADERS,
    files={"file": open("doc.pdf", "rb")},
    data={"options_json": '{"conversion_formats":{"docx":true},"math_inline_delimiters":["$","$"]}'}
)
pdf_id = resp.json()["pdf_id"]

# Poll
while True:
    status = requests.get(f"{BASE}/v3/pdf/{pdf_id}", headers=HEADERS).json()
    if status["status"] == "completed":
        # Check individual format status too
        if all(v["status"] == "completed" for v in status.get("conversion_status", {}).values()):
            break
    time.sleep(3)

# Retrieve
mmd = requests.get(f"{BASE}/v3/pdf/{pdf_id}.mmd", headers=HEADERS).text
lines = requests.get(f"{BASE}/v3/pdf/{pdf_id}.lines.json", headers=HEADERS).json()
docx = requests.get(f"{BASE}/v3/pdf/{pdf_id}.docx", headers=HEADERS).content
```

### Converter Pattern

```python
resp = requests.post(f"{BASE}/v3/converter",
    headers={**HEADERS, "Content-Type": "application/json"},
    json={"mmd": mmd_content, "formats": {"pdf": True, "docx": True}}
)
cid = resp.json()["conversion_id"]

# Poll & retrieve same as PDF pattern but with /v3/converter/{cid}
```
