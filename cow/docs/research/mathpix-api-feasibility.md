# Mathpix API Feasibility Study: Korean Math/Science Document OCR

> Research date: 2026-02-09
> Target use case: Korean math/science document digitization with layout preservation

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [API Endpoints and Features](#2-api-endpoints-and-features)
3. [Korean Language Support](#3-korean-language-support)
4. [Layout Preservation](#4-layout-preservation)
5. [Output Formats](#5-output-formats)
6. [Diagram and Chart Detection](#6-diagram-and-chart-detection)
7. [Best Practices for Korean Math/Science Documents](#7-best-practices-for-korean-mathscience-documents)
8. [Pricing](#8-pricing)
9. [Limitations and Known Issues](#9-limitations-and-known-issues)
10. [Changelog Highlights (2024-2026)](#10-changelog-highlights-2024-2026)
11. [Verdict and Recommendations](#11-verdict-and-recommendations)
12. [Sources](#12-sources)

---

## 1. Executive Summary

Mathpix provides the most mature OCR API specifically designed for STEM content (math equations, scientific notation, chemical structures, tables). It supports Korean (Hangeul) as a **printed text** language, with strong math/equation recognition across all languages. For Korean math/science documents, Mathpix is a strong candidate with important caveats:

**Strengths:**
- Industry-leading math equation OCR (up to 99% accuracy for printed equations)
- Korean printed text supported alongside math
- Rich structured output: bounding boxes, document tree hierarchy, element typing
- Multiple output formats (MMD, LaTeX, DOCX, HTML, JSON with line-level data)
- Active development: SuperNet model updates every 1-2 months
- Diagram/chart detection with text extraction and figure label linking

**Weaknesses:**
- No handwritten Korean support (only Latin scripts + Hindi for handwriting)
- Korean is "adequately supported" but not a primary optimization target
- No Korean-specific spell check (English only as of Feb 2026)
- Limited public documentation on Korean-specific accuracy metrics

**Bottom line:** Feasible for printed Korean math/science documents. For handwritten Korean content, a supplementary OCR solution would be needed.

---

## 2. API Endpoints and Features

### Core Processing Endpoints

| Endpoint | Method | Purpose | Async? |
|----------|--------|---------|--------|
| `v3/text` | POST | Single image OCR (equations, text, tables, diagrams) | No (sync) |
| `v3/pdf` | POST | PDF/EPUB/DOCX document conversion | Yes |
| `v3/batch` | POST | Multiple images in one request | Yes |
| `v3/strokes` | POST | Digital ink/handwriting recognition | No |
| `v3/latex` | POST | Legacy equation-only OCR | No |

### Query/Utility Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `v3/ocr-results` | GET | Search results from v3/text, v3/strokes, v3/latex |
| `v3/pdf-results` | GET | Search results from v3/pdf |
| `v3/pdf/{pdf_id}` | GET | Check PDF processing status |
| `v3/pdf/{pdf_id}/stream` | GET | Streaming PDF results (SSE) |
| `v3/app-tokens` | POST | Generate temporary client-side tokens |

### Recommended Endpoint

**Use `v3/text` for images** (recommended over legacy v3/latex — more features, more robust).
**Use `v3/pdf` for multi-page documents** (asynchronous, supports page ranges).

### v3/text Request Parameters

```json
{
  "src": "data:image/jpeg;base64,..." ,
  "formats": ["text", "data", "html", "latex_styled"],
  "data_options": {
    "include_svg": true,
    "include_tsv": true,
    "include_latex": true,
    "include_asciimath": true,
    "include_mathml": true
  },
  "include_line_data": true,
  "include_word_data": true,
  "include_diagram_text": true,
  "include_equation_tags": true,
  "math_inline_delimiters": ["\\(", "\\)"],
  "math_display_delimiters": ["\\[", "\\]"],
  "rm_spaces": true,
  "rm_fonts": false,
  "numbers_default_to_math": false,
  "idiomatic_eqn_arrays": false,
  "alphabets_allowed": {
    "ko": true
  },
  "region": {
    "top_left_x": 0,
    "top_left_y": 0,
    "width": 1000,
    "height": 800
  }
}
```

### v3/text Response Structure

```json
{
  "text": "Mathpix Markdown output...",
  "latex_styled": "\\frac{a}{b}",
  "confidence": 0.98,
  "confidence_rate": 0.95,
  "is_printed": true,
  "is_handwritten": false,
  "auto_rotate_degrees": 0,
  "line_data": [ /* LineData objects */ ],
  "word_data": [ /* WordData objects */ ],
  "data": [ /* Data objects */ ],
  "error": null,
  "error_info": null
}
```

### v3/pdf Request Parameters

```json
{
  "url": "https://example.com/document.pdf",
  "streaming": true,
  "page_ranges": "1-5,8,10-12",
  "conversion_formats": {
    "docx": true,
    "tex.zip": true,
    "html": true,
    "md": true,
    "mmd": true,
    "pdf": true,
    "pptx": true,
    "xlsx": true
  },
  "include_smiles": true,
  "include_equation_tags": true,
  "include_diagram_text": true,
  "alphabets_allowed": { "ko": true }
}
```

---

## 3. Korean Language Support

### Support Level

| Aspect | Status | Notes |
|--------|--------|-------|
| Printed Korean text | Supported | Listed as "Korean (Hangeul)" in Asian languages |
| Handwritten Korean | NOT supported | Handwriting limited to English, Latin-script langs, Hindi |
| Korean + Math mixed | Supported | "Recognized with relative accuracy" |
| Korean spell check | NOT available | `enable_spell_check` is English-only as of Feb 2026 |
| Korean in tables | Supported | Via general table OCR |
| Korean in diagrams | Supported | Via `include_diagram_text: true` |

### Alphabet Configuration

Korean recognition is enabled by default. To explicitly control it:

```json
{
  "alphabets_allowed": {
    "ko": true
  }
}
```

The `alphabets_allowed` parameter accepts language codes: `ko` (Korean), `ja` (Japanese), `zh` (Chinese), `hi` (Hindi), `ru` (Russian), `th` (Thai), `vi` (Vietnamese), etc. Setting a language to `false` prevents those characters from appearing in output (useful for reducing false positives when Korean is not expected).

### XeLaTeX Auto-Selection

When non-Latin scripts (including Korean) are detected, Mathpix automatically selects XeLaTeX for LaTeX output, ensuring proper font rendering for Korean characters in the generated `.tex` files.

### Practical Assessment

Korean text mixed with math equations is the typical use case for Korean math/science documents. Mathpix's primary strength is the math recognition, which is language-agnostic. The Korean text portions are recognized "with relative accuracy" — meaning:
- Common Korean vocabulary in math/science contexts works well
- Complex or unusual Korean phrasing may have lower accuracy than English
- No dedicated Korean language model tuning is publicly documented

---

## 4. Layout Preservation

### 4.1 Bounding Boxes

Mathpix provides two coordinate formats for element positioning:

#### Contour (`cnt`) — Polygon Coordinates
Available in both `line_data` and `word_data`. Represents the exact boundary as polygon vertices:

```json
{
  "cnt": [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
}
```

Coordinates are in **pixel space** of the input image.

#### Region — Rectangle Coordinates
Available for elements with rectangular bounds:

```json
{
  "region": {
    "top_left_x": 120,
    "top_left_y": 45,
    "width": 350,
    "height": 28
  }
}
```

Also in pixel coordinates.

### 4.2 Document Tree Hierarchy (April 2025+)

The SuperNet model introduced hierarchical element tracking:

```json
{
  "id": "b36ee632ed9f40a98be59f58876fc2c1",
  "parent_id": "a1b2c3d4e5f6...",
  "children_ids": ["child1_id", "child2_id"],
  "type": "text",
  "subtype": null,
  "text": "Content here...",
  "cnt": [[x1, y1], ...],
  "region": { ... },
  "conversion_output": true,
  "confidence": 0.97,
  "confidence_rate": 0.95,
  "is_printed": true,
  "is_handwritten": false
}
```

**Key relationships:**
- A diagram's `children_ids` contain IDs of text lines within it
- A text line's `parent_id` references its containing diagram
- Tables have children representing cells
- `conversion_output: true` means the element appears in the final Markdown/DOCX/HTML output

### 4.3 Multi-Column Layout

The SuperNet layout model improved multi-column text handling and page layout parsing. Key capabilities:
- Automatic column detection and reading order determination
- Improved paragraph separation algorithms
- Rotated page content recognition (0, 90, -90, 180 degrees)
- Table of contents detection

**Note:** Multi-column support has been steadily improving through SuperNet updates, but Mathpix does not expose explicit column boundary coordinates. The reading order is reflected in the sequence of `line_data` elements.

### 4.4 Table Structures

Tables are well-supported with:
- Cell-level detection and extraction
- Multi-column and multi-row spanning
- Rotated cell support
- Diagonally split cell support
- LaTeX `tabular` output with full formatting
- TSV/XLSX export for data extraction
- Table hierarchy in document tree (parent table -> child cells)

### 4.5 Line Data Object (Complete Structure)

```json
{
  "id": "unique_identifier",
  "parent_id": "parent_container_id",
  "children_ids": ["child1", "child2"],
  "type": "text|math|table|diagram|code|figure_label|chart",
  "subtype": "vertical|chemistry|triangle|column|bar|line|pie|scatter|area|algorithm|pseudocode",
  "cnt": [[x1, y1], [x2, y2], ...],
  "region": { "top_left_x": 0, "top_left_y": 0, "width": 100, "height": 50 },
  "text": "Mathpix Markdown content",
  "conversion_output": true,
  "confidence": 0.98,
  "confidence_rate": 0.96,
  "is_printed": true,
  "is_handwritten": false,
  "selected_labels": ["figure_label_id"],
  "error_id": null
}
```

### 4.6 Word Data Object

```json
{
  "type": "text|math|table|diagram|equation_number",
  "cnt": [[x1, y1], [x2, y2], ...],
  "text": "word content",
  "latex": "\\LaTeX",
  "confidence": 0.99,
  "confidence_rate": 0.97
}
```

---

## 5. Output Formats

### 5.1 Available Formats

| Format | v3/text | v3/pdf | Description |
|--------|---------|--------|-------------|
| MMD (Mathpix Markdown) | `text` field | `convert_to_mmd` | Superset of Markdown with LaTeX math |
| LaTeX | `latex_styled` | `convert_to_tex_zip` | Full LaTeX with images in ZIP |
| HTML | `html` format | `convert_to_html` | Rendered HTML with MathJax |
| DOCX | -- | `convert_to_docx` | Word document |
| PDF | -- | `convert_to_pdf` | Re-rendered PDF |
| PPTX | -- | `convert_to_pptx` | PowerPoint |
| XLSX | -- | `convert_to_xlsx` | Excel (tables only) |
| JSON (line_data) | `include_line_data` | `lines_json` | Per-line structured data with bbox |
| JSON (word_data) | `include_word_data` | -- | Per-word structured data with bbox |
| AsciiMath | via `data_options` | -- | ASCII math notation |
| MathML | via `data_options` | -- | MathML XML |
| SVG | via `data_options` | -- | SVG rendering of math |
| TSV | via `data_options` | -- | Tab-separated values (tables) |
| SMILES | `include_smiles` | `include_smiles` | Chemical structure notation |

### 5.2 Mathpix Markdown (MMD) Format

MMD is the primary output format and a strict superset of standard Markdown:

**Math delimiters:**
- Inline: `$...$` or `\(...\)`
- Block (unnumbered): `$$...$$`, `\[...\]`, `\begin{equation*}...\end{equation*}`
- Block (numbered): `\begin{equation}...\end{equation}`
- Multi-line: `\begin{align}...\end{align}`, `\begin{gather}...\end{gather}`

**Tables:** Both Markdown pipe syntax and LaTeX `tabular` environment.

**Figures:** `\begin{figure}[h]\includegraphics[width=0.5\textwidth]{url}\end{figure}`

**Chemistry:** `<smiles>CCO</smiles>` for inline chemical structures.

**Cross-references:** `\label{}`, `\ref{}`, `\eqref{}`, `\tag{}`

### 5.3 JSON with Per-Element Bounding Boxes

The most structured output for layout reconstruction. Request with:

```json
{
  "include_line_data": true,
  "include_word_data": true,
  "include_diagram_text": true
}
```

Returns hierarchical element tree with polygon (`cnt`) and rectangle (`region`) coordinates for every detected element.

### 5.4 LaTeX Output Quality for Korean Math

- Math equations: Excellent quality, language-agnostic
- Korean text: Rendered via XeLaTeX auto-selection
- Equation numbering: Via `include_equation_tags: true`
- Code blocks: `lstlisting` environment with Unicode support
- Image alt-text preserved via `\includegraphics[alt={...}]`

---

## 6. Diagram and Chart Detection

### 6.1 Element Type System

When `include_line_data: true`, each element is classified:

| Type | Subtypes | Description |
|------|----------|-------------|
| `text` | -- | Regular text content |
| `math` | -- | Mathematical equations |
| `table` | -- | Tabular data |
| `diagram` | `algorithm`, `pseudocode`, `chemistry`, `chemistry_reaction`, `triangle` | Non-chart visual elements |
| `chart` | `column`, `bar`, `line`, `analytical`, `pie`, `scatter`, `area` | Data visualization charts |
| `code` | -- | Code/pseudocode blocks |
| `figure_label` | -- | Captions/labels for figures |

### 6.2 Figure Label Linking (SuperNet-105, Aug 2025)

Figures, charts, and tables are linked to their captions via `selected_labels`:

```json
{
  "id": "diagram_abc123",
  "type": "diagram",
  "selected_labels": ["label_xyz789"],
  "cnt": [[50, 100], [400, 100], [400, 350], [50, 350]],
  "children_ids": ["text_in_diagram_1", "text_in_diagram_2"]
}
```

Corresponding label:
```json
{
  "id": "label_xyz789",
  "type": "figure_label",
  "text": "Figure 3. Force diagram of the pendulum system"
}
```

### 6.3 Diagram Text Extraction

Enable with `"include_diagram_text": true`. Text fragments inside diagrams become child elements in the document tree, accessible via `parent_id`/`children_ids` relationships.

### 6.4 Detection Capabilities

**What Mathpix CAN detect:**
- Chart type classification (7 chart subtypes)
- Diagram boundary boxes
- Text within diagrams
- Figure-caption associations
- Table cell structures (including rotated/diagonal splits)

**What Mathpix CANNOT do:**
- Extract numerical data from chart axes/series (no chart data extraction)
- Recognize geometric shapes as semantic objects (e.g., "this is a triangle with angles X, Y, Z")
- OCR of very small text within complex diagrams may have reduced accuracy

---

## 7. Best Practices for Korean Math/Science Documents

### 7.1 Image Preparation

- **Resolution:** Aim for 300 DPI minimum for printed documents
- **File size:** Keep under 100KB for maximum speed (JPEG compression recommended)
- **Format:** JPEG preferred for speed; PNG for diagrams with fine lines
- **Cropping:** Crop to content area to minimize unnecessary data

### 7.2 Recommended API Configuration

```json
{
  "src": "data:image/jpeg;base64,...",
  "formats": ["text", "data"],
  "data_options": {
    "include_latex": true,
    "include_mathml": true
  },
  "include_line_data": true,
  "include_word_data": true,
  "include_diagram_text": true,
  "include_equation_tags": true,
  "alphabets_allowed": {
    "ko": true
  },
  "math_inline_delimiters": ["\\(", "\\)"],
  "math_display_delimiters": ["\\[", "\\]"],
  "rm_spaces": true,
  "idiomatic_eqn_arrays": true
}
```

### 7.3 PDF Processing Configuration

```json
{
  "url": "https://...",
  "conversion_formats": {
    "md": true,
    "tex.zip": true
  },
  "include_diagram_text": true,
  "include_equation_tags": true,
  "alphabets_allowed": { "ko": true },
  "streaming": true
}
```

### 7.4 Performance Tips

1. **Use the SE Asia server** for lower latency from Korea: standard API endpoint auto-routes, but can test `https://ap-southeast-1.api.mathpix.com/` if available
2. **Use form uploads** (multipart/form-data) over base64 JSON for better upload speed
3. **Batch processing:** Use `v3/text` with `async` flag + `tags` for bulk operations, then query via `v3/ocr-results`
4. **Streaming PDF API:** Use `GET /v3/pdf/{pdf_id}/stream` for real-time page-by-page results on long documents
5. **Page ranges:** Use `page_ranges` parameter to process only needed pages

### 7.5 Post-Processing Recommendations

- Validate Korean text accuracy with a secondary check (e.g., comparison with a general-purpose Korean OCR)
- Use the `confidence` and `confidence_rate` fields to flag low-confidence Korean text segments for manual review
- For LaTeX output, verify XeLaTeX compilation with Korean fonts (NanumGothic, Malgun Gothic, etc.)

---

## 8. Pricing

### 8.1 Current Pricing (as of Feb 2026)

| Tier | Image API (v3/text) | PDF API (v3/pdf) |
|------|---------------------|-------------------|
| 0 - 1M units | $0.002 / image | $0.005 / page |
| 1M+ units | $0.0015 / image | $0.0035 / page |

**Setup fee:** $19.99 one-time (includes $29 credit for testing).

**Important:** Images with more than 12 rows of text are billed at PDF page rates ($0.005/page).

### 8.2 Stroke API Pricing

| Tier | Price |
|------|-------|
| 0 - 1K sessions | Free |
| 1K - 100K sessions | $0.01 / session |
| 100K - 1M sessions | $0.008 / session |
| 1M+ sessions | $0.005 / session |

### 8.3 Cost Estimation for Korean Math Documents

**Scenario: Processing a 200-page Korean math textbook**
- Via PDF API: 200 pages x $0.005 = **$1.00**
- If processing individual page images: 200 images x $0.002 = **$0.40** (if each image <= 12 text rows)

**Scenario: Processing 10,000 math problem images**
- 10,000 x $0.002 = **$20.00**

**Scenario: Monthly processing of 50,000 PDF pages**
- 50,000 x $0.005 = **$250.00/month**

### 8.4 Enterprise

Custom pricing available for long-term contracts with 24/7 priority support and customizable recognition features.

---

## 9. Limitations and Known Issues

### 9.1 Korean-Specific Limitations

| Issue | Severity | Detail |
|-------|----------|--------|
| No handwritten Korean | HIGH | Only printed Korean recognized; handwritten Korean not supported |
| No Korean spell check | MEDIUM | `enable_spell_check` is English-only |
| Korean accuracy gap | MEDIUM | Korean text "relatively accurate" but not primary optimization target |
| No Korean-specific metrics | LOW | No public accuracy benchmarks for Korean |
| Korean training data bias | UNKNOWN | Unclear how much Korean STEM content is in training data |

### 9.2 General Limitations

| Issue | Severity | Detail |
|-------|----------|--------|
| No chart data extraction | MEDIUM | Can detect chart type but cannot extract data series/values |
| Diagram semantic understanding | MEDIUM | Detects diagrams but does not understand geometric relationships |
| Multi-column ordering | LOW | Generally works but complex layouts may produce incorrect reading order |
| Low-resolution images | MEDIUM | Accuracy drops significantly below 150 DPI |
| Large images billed as PDF | LOW | >12 text rows = PDF pricing ($0.005 vs $0.002) |
| Async-only PDF processing | LOW | v3/pdf is asynchronous (requires polling or streaming) |

### 9.3 Handwriting Support Matrix

| Language | Printed | Handwritten |
|----------|---------|-------------|
| English | Yes | Yes |
| Korean | Yes | **No** |
| Chinese | Yes | Yes (improved 2025) |
| Japanese | Yes | Yes (improved 2025) |
| Hindi | Yes | Yes |
| Latin-script | Yes | Yes |
| Cyrillic | Yes | No |
| Arabic | Yes | No |

---

## 10. Changelog Highlights (2024-2026)

### 2026 (Jan-Feb)
- Hierarchical element tracking: `id`, `parent_id`, `children_ids` fields (April 2025 SuperNet, confirmed in 2026 builds)
- Ongoing SuperNet model improvements

### 2025
| Month | Update | Relevance |
|-------|--------|-----------|
| Nov | SuperNet-108: Greek/Georgian support, improved scanned docs | Scanned doc quality |
| Sep | HTML, MMD, MD ZIP export; form field recognition | New export options |
| Aug | **SuperNet-105: Figure labels linked to diagrams/charts/tables** | Layout preservation |
| Aug | Improved handwritten Chinese and Japanese | CJK improvements |
| Apr | **SuperNet: New layout model, document tree, diagram text parsing** | Core layout upgrade |
| Mar | Image API price reduction | Cost savings |

### 2024
| Month | Update | Relevance |
|-------|--------|-----------|
| Dec | Streaming PDF API (`/v3/pdf/{id}/stream`) | Real-time processing |
| Sep | Chart type detection (7 subtypes) | Chart classification |
| Feb | Equation tags support (`include_equation_tags`) | Numbered equations |

---

## 11. Verdict and Recommendations

### 11.1 Feasibility Assessment

| Criterion | Rating | Notes |
|-----------|--------|-------|
| Math equation OCR | EXCELLENT | Industry-leading, language-agnostic |
| Korean printed text | GOOD | Supported, adequate accuracy |
| Korean handwritten text | NOT FEASIBLE | Not supported |
| Layout preservation | VERY GOOD | Bbox + document tree + element hierarchy |
| Diagram detection | GOOD | Type/subtype classification, text extraction |
| Table extraction | EXCELLENT | Cell-level, multi-span, export to XLSX |
| Output format richness | EXCELLENT | MMD, LaTeX, DOCX, HTML, JSON, XLSX, etc. |
| Pricing | GOOD | Competitive for STEM OCR ($0.002-$0.005/unit) |
| API maturity | EXCELLENT | Well-documented, active development, Python SDK |

### 11.2 Recommendations

1. **Use Mathpix as the primary OCR engine** for printed Korean math/science documents. The math recognition quality is unmatched, and Korean text support is adequate.

2. **Supplement with a Korean-specialized OCR** (e.g., Naver Clova OCR, Google Cloud Vision) for:
   - Handwritten Korean content
   - Documents that are mostly Korean text with minimal math
   - Accuracy validation of Mathpix's Korean text output

3. **Use `include_line_data` + `include_word_data`** to get full bounding box information for layout reconstruction.

4. **Use `include_diagram_text: true`** to extract text from diagrams and charts.

5. **For the pipeline architecture**, consider:
   - Mathpix for math-heavy content (equations, tables, chemical structures)
   - A general Korean OCR for text-heavy regions
   - Merge results using bounding box coordinates for alignment

6. **Monitor SuperNet updates** — Korean support may improve in future model versions, given the CJK improvements already made for Chinese and Japanese handwriting.

### 11.3 Python SDK Quick Start

```python
from mpxpy.mathpix_client import MathpixClient

client = MathpixClient(
    app_id="YOUR_APP_ID",
    app_key="YOUR_APP_KEY"
)

# Single image processing
image = client.image_new(
    file_path="/path/to/korean_math_problem.jpg"
)
print(image.mmd())           # Mathpix Markdown
print(image.lines_json())    # Structured line data with bboxes

# PDF processing
pdf = client.pdf_new(
    file_path="/path/to/korean_textbook.pdf",
    convert_to_md=True,
    convert_to_docx=True,
    convert_to_tex_zip=True
)
pdf.wait_until_complete(timeout=120)
lines = pdf.to_lines_json()  # Per-line OCR with bounding boxes
pdf.to_md_file("/output/textbook.md")
pdf.to_docx_file("/output/textbook.docx")
```

---

## 12. Sources

- [Mathpix Convert API Overview](https://mathpix.com/convert)
- [Mathpix API v3 Reference](https://docs.mathpix.com/)
- [Convert API Endpoints Guide](https://mathpix.com/docs/convert/endpoints)
- [Supported Languages](https://mathpix.com/docs/convert/supported_languages)
- [All Supported Languages](https://mathpix.com/language-support)
- [Convert API Changelog](https://mathpix.com/docs/convert/changelog)
- [API Best Practices](https://mathpix.com/docs/convert/best-practices)
- [Convert API Pricing](https://mathpix.com/pricing/api)
- [SuperNet Blog Post: Layout Model and Document Tree](https://mathpix.com/blog/supernet)
- [SuperNet-105: Figure Labels Linked to Figures](https://mathpix.com/blog/figure-labels)
- [Mathpix Markdown Syntax Reference](https://mathpix.com/docs/mathpix-markdown/syntax-reference)
- [Python SDK: Image Processing](https://mathpix.com/docs/mpxpy/images)
- [Python SDK: PDF Processing](https://mathpix.com/docs/mpxpy/pdf)
- [Mathpix Markdown GitHub (mathpix-markdown-it)](https://github.com/Mathpix/mathpix-markdown-it)
- [Image API Price Reduction Blog](https://mathpix.com/blog/image-api-price-reduction)
- [Mathpix Korean Analysis (Skywork AI)](https://skywork.ai/skypage/ko/mathpix-snip-ai-analysis/1982726737674502144)
- [Mathpix Reviews 2026 (G2)](https://www.g2.com/products/mathpix/reviews)
