> **CRITICAL:** See [MATHPIX_API_CONSTRAINTS.md](MATHPIX_API_CONSTRAINTS.md) for important API limitations.

> - `include_word_data` and `include_line_data` are **MUTUALLY EXCLUSIVE**

> - These parameters are **TOP-LEVEL** (not inside data_options)

---

# Mathpix API Documentation Extraction for Claude Code CLI

## Comprehensive YAML Specification Files

Based on complete extraction from https://docs.mathpix.com/ - the official Mathpix API v3 Reference documentation.

---

## INDEX.yaml - Master Index of All APIs

```yaml
# Mathpix API Documentation Index
# Version: v3 (Current as of February 2026)
# Base URL: https://api.mathpix.com

api_version: v3
base_url: https://api.mathpix.com
eu_base_url: https://eu-central-1.api.mathpix.com

endpoints:
  - name: Process Image
    path: /v3/text
    method: POST
    spec_file: ocr/SPEC.yaml
    description: Primary OCR endpoint for images with math, text, tables, diagrams
    
  - name: Process Equation (Legacy)
    path: /v3/latex
    method: POST
    spec_file: ocr/SPEC.yaml
    description: Legacy endpoint for equation images - deprecated in favor of v3/text
    
  - name: Process Strokes
    path: /v3/strokes
    method: POST
    spec_file: strokes/SPEC.yaml
    description: Digital ink/handwriting recognition
    
  - name: Process PDF
    path: /v3/pdf
    method: POST
    spec_file: pdf/SPEC.yaml
    description: Async PDF to Markdown/LaTeX/DOCX conversion
    
  - name: Process Batch
    path: /v3/batch
    method: POST
    spec_file: batch/SPEC.yaml
    description: Multiple images in single request
    
  - name: Convert Documents
    path: /v3/converter
    method: POST
    spec_file: latex/SPEC.yaml
    description: Convert MMD to other formats
    
  - name: App Tokens
    path: /v3/app-tokens
    method: POST
    spec_file: common/SPEC.yaml
    description: Generate short-lived client-side tokens
    
  - name: Query OCR Results
    path: /v3/ocr-results
    method: GET
    spec_file: common/SPEC.yaml
    description: Search previous OCR results
    
  - name: Query PDF Results
    path: /v3/pdf-results
    method: GET
    spec_file: pdf/SPEC.yaml
    description: Search previous PDF results
    
  - name: Query OCR Usage
    path: /v3/ocr-usage
    method: GET
    spec_file: common/SPEC.yaml
    description: Track API usage statistics

supported_content_types:
  input:
    - math_equations
    - text_paragraphs
    - tables
    - chemistry_diagrams
    - handwriting
    - printed_content
  output_formats:
    - mathpix_markdown
    - latex
    - asciimath
    - mathml
    - html
    - docx
    - pdf
    - pptx
```

---

## ocr/SPEC.yaml - Image OCR API

```yaml
# Mathpix Image OCR API Specification
# Endpoint: POST /v3/text (Primary) and POST /v3/latex (Legacy)

endpoint:
  primary:
    path: /v3/text
    method: POST
    description: Process an image with MathpixOCR for math, text, tables, diagrams
  legacy:
    path: /v3/latex
    method: POST
    description: Legacy equation-only endpoint (deprecated - use v3/text)

request:
  content_types:
    - application/json
    - multipart/form-data
    
  headers:
    app_id:
      type: string
      required: true
      description: Application identifier
    app_key:
      type: string
      required: true
      description: API key for authorization
    app_token:
      type: string
      required: false
      description: Alternative to app_id/app_key for client-side auth
    Content-Type:
      type: string
      required: true
      enum: ["application/json", "multipart/form-data"]

  parameters:
    # Image Source
    src:
      type: string
      required: true (if not using file upload)
      description: Image URL or base64 data URI (data:image/jpeg;base64,...)
      formats:
        - url: Public HTTP(S) URL to image
        - data_uri: "data:image/{format};base64,{encoded_data}"
    
    file:
      type: binary
      required: true (if not using src)
      description: Image file for multipart/form-data upload
      
    options_json:
      type: string (JSON)
      required: false
      description: Stringified JSON options when using file upload
    
    # Output Formats
    formats:
      type: array[string]
      required: false
      description: List of desired output formats
      values:
        - text: Mathpix Markdown output
        - data: Computed data list from text (asciimath, latex, etc.)
        - html: HTML rendered from text
        - latex_styled: Math LaTeX when image is single equation
      default: ["text"]
    
    data_options:
      type: object
      required: false
      description: Options for data and html return fields
      properties:
        include_svg:
          type: boolean
          default: false
          description: Include math SVG in html and data formats
        include_table_html:
          type: boolean
          default: false
          description: Include HTML for tables
        include_latex:
          type: boolean
          default: false
          description: Include math mode latex
        include_tsv:
          type: boolean
          default: false
          description: Include tab-separated values for tables
        include_asciimath:
          type: boolean
          default: false
          description: Include AsciiMath output
        include_mathml:
          type: boolean
          default: false
          description: Include MathML output
    
    # Segmentation Options
    include_line_data:
      type: boolean
      required: false
      default: false
      description: Return line-by-line segmentation data
      
    include_word_data:
      type: boolean
      required: false
      default: false
      description: Return word-level segmentation data
      
    include_detected_alphabets:
      type: boolean
      required: false
      default: false
      description: Return detected alphabets object
    
    # Math Delimiter Configuration
    math_inline_delimiters:
      type: array[string, string]
      required: false
      default: ["\\(", "\\)"]
      description: Begin/end delimiters for inline math
      examples:
        - ["$", "$"]
        - ["\\(", "\\)"]
        
    math_display_delimiters:
      type: array[string, string]
      required: false
      default: ["\\[", "\\]"]
      description: Begin/end delimiters for display math
      examples:
        - ["$$", "$$"]
        - ["\\[", "\\]"]
    
    # Processing Options
    region:
      type: object
      required: false
      description: Specify image area to process (pixel coordinates)
      properties:
        top_left_x:
          type: integer
          description: X coordinate of top-left corner
        top_left_y:
          type: integer
          description: Y coordinate of top-left corner
        width:
          type: integer
          description: Width in pixels
        height:
          type: integer
          description: Height in pixels
    
    confidence_threshold:
      type: number
      required: false
      range: [0, 1]
      description: Minimum confidence for 100% correct result
      
    confidence_rate_threshold:
      type: number
      required: false
      default: 0.75
      range: [0, 1]
      description: Symbol-level confidence threshold
    
    auto_rotate_confidence_threshold:
      type: number
      required: false
      default: 0.99
      range: [0, 1]
      description: Threshold for auto-rotating images; set to 1 to disable
    
    rm_spaces:
      type: boolean
      required: false
      default: true
      description: Remove extra whitespace from equations
      
    rm_fonts:
      type: boolean
      required: false
      default: false
      description: Remove font commands (mathbf, mathrm, etc.)
    
    idiomatic_eqn_arrays:
      type: boolean
      required: false
      default: false
      description: Use aligned/gathered/cases instead of array environment
      
    idiomatic_braces:
      type: boolean
      required: false
      default: false
      description: Remove unnecessary braces (x^2 instead of x^{2})
    
    numbers_default_to_math:
      type: boolean
      required: false
      default: false
      description: Wrap all numbers in math mode
      
    math_fonts_default_to_math:
      type: boolean
      required: false
      default: false
      description: Wrap math fonts in math mode
    
    include_equation_tags:
      type: boolean
      required: false
      default: false
      description: Include \tag{eq_number} in equations
    
    include_smiles:
      type: boolean
      required: false
      default: false
      description: Enable chemistry diagram OCR returning SMILES notation
      
    include_inchi:
      type: boolean
      required: false
      default: false
      description: Include InChI data in SMILES elements
    
    include_geometry_data:
      type: boolean
      required: false
      default: false
      description: Enable geometry diagram data extraction (triangles)
      
    include_diagram_text:
      type: boolean
      required: false
      default: false
      description: Extract text from diagrams in line_data
      
    include_page_info:
      type: boolean
      required: false
      default: true
      description: Include page info elements (headers, footers, etc.)
    
    enable_blue_hsv_filter:
      type: boolean
      required: false
      default: false
      description: OCR blue hue text exclusively
      
    enable_tables_fallback:
      type: boolean
      required: false
      default: false
      description: Enable advanced table processing for complex tables
    
    fullwidth_punctuation:
      type: boolean
      required: false
      default: null
      description: Use fullwidth Unicode punctuation (null = auto-detect)
    
    # Alphabet Control
    alphabets_allowed:
      type: object
      required: false
      description: Control which alphabets appear in output
      properties:
        en:
          type: boolean
          default: true
          description: English
        hi:
          type: boolean
          default: true
          description: Hindi Devanagari
        zh:
          type: boolean
          default: true
          description: Chinese
        ja:
          type: boolean
          default: true
          description: Japanese Kana
        ko:
          type: boolean
          default: true
          description: Korean Hangul
        ru:
          type: boolean
          default: true
          description: Russian
        th:
          type: boolean
          default: true
          description: Thai
        ta:
          type: boolean
          default: true
          description: Tamil
        te:
          type: boolean
          default: true
          description: Telugu
        gu:
          type: boolean
          default: true
          description: Gujarati
        bn:
          type: boolean
          default: true
          description: Bengali
        vi:
          type: boolean
          default: true
          description: Vietnamese
    
    # Async and Callbacks
    async:
      type: boolean
      required: false
      default: false
      description: Enable non-interactive async processing
      
    callback:
      type: object
      required: false
      description: Callback configuration for async results
      properties:
        post:
          type: string
          description: URL to POST results to
        reply:
          type: object
          description: Additional fields to include in response
        body:
          type: object
          description: Additional data to pass to callback
        headers:
          type: object
          description: Headers to send with callback POST
    
    # Metadata
    metadata:
      type: object
      required: false
      description: Key-value metadata for tracking
      properties:
        improve_mathpix:
          type: boolean
          default: true
          description: Allow Mathpix to retain output for improvement
    
    tags:
      type: array[string]
      required: false
      description: Tags for identifying results in v3/ocr-results queries

response:
  fields:
    request_id:
      type: string
      description: Unique request identifier for debugging
      example: "2025_04_16_d884f78c7c80ba983343g"
    
    version:
      type: string
      description: OCR engine version
      example: "SuperNet-100"
    
    text:
      type: string
      description: Mathpix Markdown output with math in delimiters
      example: "\\( f(x) = x^2 \\)"
    
    latex_styled:
      type: string
      description: Math LaTeX for single-equation images
      example: "f(x) = x^{2}"
    
    confidence:
      type: number
      range: [0, 1]
      description: Estimated probability of 100% correctness
    
    confidence_rate:
      type: number
      range: [0, 1]
      description: Per-symbol confidence geometric mean
    
    is_printed:
      type: boolean
      description: Whether printed content was detected
    
    is_handwritten:
      type: boolean
      description: Whether handwritten content was detected
    
    image_width:
      type: integer
      description: Input image width in pixels
    
    image_height:
      type: integer
      description: Input image height in pixels
    
    auto_rotate_confidence:
      type: number
      range: [0, 1]
      description: Confidence that image needs rotation
    
    auto_rotate_degrees:
      type: integer
      enum: [0, 90, -90, 180]
      description: Rotation applied to correct orientation
    
    # Optional fields based on request options
    data:
      type: array[DataObject]
      description: List of extracted data elements
      
    html:
      type: string
      description: Annotated HTML output
      
    line_data:
      type: array[LineDataObject]
      description: Line-by-line segmentation (when include_line_data=true)
      
    word_data:
      type: array[WordDataObject]
      description: Word-level segmentation (when include_word_data=true)
    
    detected_alphabets:
      type: DetectedAlphabetObject
      description: Which alphabets were detected
    
    geometry_data:
      type: array[GeometryDataObject]
      description: Geometry diagram data
    
    error:
      type: string
      description: Error message (US locale)
      
    error_info:
      type: ErrorInfoObject
      description: Detailed error information

schemas:
  DataObject:
    type: object
    properties:
      type:
        type: string
        enum: [asciimath, mathml, latex, svg, tsv, table_html]
        description: Type of extracted data
      value:
        type: string
        description: The extracted value
  
  LineDataObject:
    type: object
    properties:
      id:
        type: string
        description: Unique line identifier
      parent_id:
        type: string
        required: false
        description: Parent line identifier
      children_ids:
        type: array[string]
        required: false
        description: Child line identifiers
      type:
        type: string
        enum: [text, math, table, diagram, equation_number, code, title, section_header, authors, abstract, multiple_choice_block, footnote, quote, chart, chart_info, form_field, pseudocode, figure_label, qed_symbol, rotated_container, table_cell, column]
        description: Line content type
      subtype:
        type: string
        required: false
        enum: [vertical, big_capital_letter, algorithm, pseudocode, chemistry, chemistry_reaction, triangle, column, bar, line, analytical, pie, scatter, area, parentheses, dotted, dashed, box, checkbox, circle, split, spanning]
        description: Line subtype
      cnt:
        type: array[array[integer, integer]]
        description: Contour as list of [x,y] pixel coordinates
      text:
        type: string
        description: Mathpix Markdown for this line
      confidence:
        type: number
        range: [0, 1]
      confidence_rate:
        type: number
        range: [0, 1]
      included:
        type: boolean
        deprecated: true
        description: Use conversion_output instead
      conversion_output:
        type: boolean
        description: Whether line is in final output
      is_printed:
        type: boolean
      is_handwritten:
        type: boolean
      after_hyphen:
        type: boolean
        description: Line follows a hyphenated word
      error_id:
        type: string
        enum: [image_not_supported, image_max_size, math_confidence, image_no_content]
        description: Reason line was excluded
  
  WordDataObject:
    type: object
    properties:
      type:
        type: string
        enum: [text, math, table, diagram, equation_number]
      subtype:
        type: string
        required: false
        enum: [chemistry, triangle]
      cnt:
        type: array[array[integer, integer]]
        description: Contour coordinates
      text:
        type: string
        description: Mathpix Markdown for word
      latex:
        type: string
        description: Math mode LaTeX
      confidence:
        type: number
        range: [0, 1]
      confidence_rate:
        type: number
        range: [0, 1]
  
  DetectedAlphabetObject:
    type: object
    properties:
      en:
        type: boolean
        description: English detected
      hi:
        type: boolean
        description: Hindi Devanagari detected
      zh:
        type: boolean
        description: Chinese detected
      ja:
        type: boolean
        description: Japanese Kana detected
      ko:
        type: boolean
        description: Korean Hangul detected
      ru:
        type: boolean
        description: Russian detected
      th:
        type: boolean
        description: Thai detected
      ta:
        type: boolean
        description: Tamil detected
      te:
        type: boolean
        description: Telugu detected
      gu:
        type: boolean
        description: Gujarati detected
      bn:
        type: boolean
        description: Bengali detected
      vi:
        type: boolean
        description: Vietnamese detected

supported_image_formats:
  - jpeg/jpg
  - png
  - gif
  - bmp
  - tiff
  - webp

image_constraints:
  recommended_size: "<100KB for optimal latency"
  max_text_rows: 12  # Images with >12 rows priced as PDF page

# Legacy v3/latex endpoint specific parameters
legacy_v3_latex:
  additional_parameters:
    ocr:
      type: array[string]
      default: ["math"]
      description: Content types to recognize
      values:
        - math: Math only
        - text: Include text (use ["math", "text"])
    
    formats:
      type: array[string]
      description: LaTeX output formats
      values:
        - text: Text mode with math in delimiters
        - text_display: Same as text but prefers display math
        - latex_normal: Direct LaTeX representation
        - latex_styled: Improved visual appearance (\left, \right)
        - latex_simplified: Optimized for symbolic processing
        - latex_list: Split into list of simplified strings
        - mathml: MathML output
        - asciimath: AsciiMath output
        - wolfram: Wolfram Alpha compatible string
    
    format_options:
      type: object
      description: Per-format customization
      properties:
        transforms:
          type: array[string]
          values:
            - rm_spaces: Remove superfluous spaces
            - rm_newlines: Replace newlines with spaces
            - rm_fonts: Remove font commands
            - rm_style_syms: Replace styled commands
            - rm_text: Omit text outside math
            - long_frac: Convert longdiv to frac
        math_delims:
          type: array[string, string]
          description: Math mode delimiters
        displaymath_delims:
          type: array[string, string]
          description: Display math delimiters
    
    skip_recrop:
      type: boolean
      default: false
      description: Skip cropping irrelevant image parts
    
    beam_size:
      type: integer
      range: [1, 5]
      description: Number of recognition candidates
    
    n_best:
      type: integer
      range: [1, beam_size]
      description: Return top N results
  
  additional_response_fields:
    position:
      type: object
      description: Equation bounding box
      properties:
        top_left_x:
          type: integer
        top_left_y:
          type: integer
        width:
          type: integer
        height:
          type: integer
    
    detection_map:
      type: object
      properties:
        contains_chart:
          type: integer (0 or 1)
        contains_diagram:
          type: integer (0 or 1)
        contains_graph:
          type: integer (0 or 1)
        contains_table:
          type: integer (0 or 1)
        contains_geometry:
          type: integer (0 or 1)
        is_blank:
          type: integer (0 or 1)
        is_inverted:
          type: integer (0 or 1)
        is_not_math:
          type: integer (0 or 1)
        is_printed:
          type: integer (0 or 1)
    
    detection_list:
      type: array[string]
      description: List of detected properties
    
    latex_confidence:
      type: number
      range: [0, 1]
    
    latex_confidence_rate:
      type: number
      range: [0, 1]
    
    candidates:
      type: array[object]
      description: Alternative recognition results (when n_best > 1)
```

---

## pdf/SPEC.yaml - PDF Processing API

```yaml
# Mathpix PDF Processing API Specification
# Endpoint: POST /v3/pdf

endpoint:
  path: /v3/pdf
  method: POST
  description: Asynchronous PDF to Markdown/LaTeX/DOCX conversion
  max_file_size: 1GB
  processing_mode: asynchronous

supported_inputs:
  - PDF
  - EPUB
  - DOCX
  - PPTX
  - AZW/AZW3/KFX (Kindle)
  - MOBI
  - DJVU
  - DOC
  - WPD (WordPerfect)
  - ODT (OpenDocument)

supported_outputs:
  - mmd (Mathpix Markdown)
  - md (Standard Markdown)
  - docx (MS Word)
  - tex.zip (LaTeX with images)
  - html
  - pdf (HTML rendering)
  - latex.pdf (LaTeX rendering)
  - pptx (PowerPoint)
  - mmd.zip (MMD with images)
  - md.zip (MD with images)
  - html.zip (HTML with images)
  - lines.json (Line-by-line data)
  - lines.mmd.json (MMD line data - deprecated)

request:
  content_types:
    - application/json
    - multipart/form-data
  
  headers:
    app_id:
      type: string
      required: true
    app_key:
      type: string
      required: true
    Content-Type:
      type: string
      required: true

  parameters:
    url:
      type: string
      required: true (if not using file upload)
      description: HTTP URL where PDF can be downloaded
    
    file:
      type: binary
      required: true (if not using url)
      description: PDF file for multipart/form-data upload
    
    options_json:
      type: string (JSON)
      required: false
      description: Stringified JSON options when using file upload
    
    streaming:
      type: boolean
      required: false
      default: false
      description: Enable page-by-page streaming results
    
    page_ranges:
      type: string
      required: false
      description: Comma-separated page selection
      examples:
        - "2,4-6"  # Pages 2, 4, 5, 6
        - "2--2"   # Page 2 to second-to-last
    
    conversion_formats:
      type: object
      required: false
      description: Auto-convert on completion
      properties:
        md:
          type: boolean
          default: false
        docx:
          type: boolean
          default: false
        tex.zip:
          type: boolean
          default: false
        html:
          type: boolean
          default: false
        pdf:
          type: boolean
          default: false
        latex.pdf:
          type: boolean
          default: false
        pptx:
          type: boolean
          default: false
        mmd.zip:
          type: boolean
          default: false
        md.zip:
          type: boolean
          default: false
        html.zip:
          type: boolean
          default: false
    
    # OCR Options (same as v3/text)
    alphabets_allowed:
      type: object
      description: Control allowed alphabets
    
    rm_spaces:
      type: boolean
      default: true
    
    rm_fonts:
      type: boolean
      default: false
    
    idiomatic_eqn_arrays:
      type: boolean
      default: false
    
    include_equation_tags:
      type: boolean
      default: false
    
    include_smiles:
      type: boolean
      default: true
      description: Chemistry diagram OCR
    
    include_chemistry_as_image:
      type: boolean
      default: false
      description: Return chemistry as image with SMILES alt-text
    
    include_diagram_text:
      type: boolean
      default: false
    
    include_page_info:
      type: boolean
      default: false
      description: Include headers, footers, page numbers
    
    numbers_default_to_math:
      type: boolean
      default: false
    
    math_inline_delimiters:
      type: array[string, string]
      default: ["\\(", "\\)"]
    
    math_display_delimiters:
      type: array[string, string]
      default: ["\\[", "\\]"]
    
    enable_tables_fallback:
      type: boolean
      default: false
    
    fullwidth_punctuation:
      type: boolean
      default: null
    
    # Section Numbering
    auto_number_sections:
      type: boolean
      default: false
      description: Auto-number sections (mutually exclusive)
    
    remove_section_numbering:
      type: boolean
      default: false
      description: Remove existing numbering (mutually exclusive)
    
    preserve_section_numbering:
      type: boolean
      default: true
      description: Keep existing numbering (mutually exclusive)
    
    metadata:
      type: object
      description: Key-value metadata

response:
  upload_response:
    pdf_id:
      type: string
      description: Tracking ID for status and results
      example: "5049b56d6cf916e713be03206f306f1a"
    
    error:
      type: string
      required: false
    
    error_info:
      type: object
      required: false

# Status endpoint
status_endpoint:
  path: /v3/pdf/{pdf_id}
  method: GET
  
  response:
    status:
      type: string
      enum: [received, loaded, split, completed, error]
      description: Processing status
    
    num_pages:
      type: integer
      description: Total pages in document
    
    num_pages_completed:
      type: integer
      description: Pages processed so far
    
    percent_done:
      type: number
      description: Processing percentage

# Streaming endpoint
streaming_endpoint:
  path: /v3/pdf/{pdf_id}/stream
  method: GET
  description: Stream page-by-page results (requires streaming=true on upload)
  
  response_per_page:
    text:
      type: string
      description: Mathpix Markdown for page
    
    page_idx:
      type: integer
      description: Page index (1-based)
    
    pdf_selected_len:
      type: integer
      description: Total pages in selection
    
    pdf_id:
      type: string
    
    version:
      type: string
      description: Engine version

# Results endpoints
results_endpoints:
  mmd:
    path: /v3/pdf/{pdf_id}.mmd
    method: GET
    returns: Mathpix Markdown text file
  
  md:
    path: /v3/pdf/{pdf_id}.md
    method: GET
    returns: Plain Markdown text file
  
  docx:
    path: /v3/pdf/{pdf_id}.docx
    method: GET
    returns: Word document
  
  tex:
    path: /v3/pdf/{pdf_id}.tex
    method: GET
    returns: LaTeX zip file with images
  
  html:
    path: /v3/pdf/{pdf_id}.html
    method: GET
    returns: HTML file
  
  pdf_html:
    path: /v3/pdf/{pdf_id}.pdf
    method: GET
    returns: PDF with HTML rendering
  
  pdf_latex:
    path: /v3/pdf/{pdf_id}.latex.pdf
    method: GET
    returns: PDF with LaTeX rendering
  
  pptx:
    path: /v3/pdf/{pdf_id}.pptx
    method: GET
    returns: PowerPoint file
  
  lines_json:
    path: /v3/pdf/{pdf_id}.lines.json
    method: GET
    returns: Line-by-line data with geometry

# Conversion status endpoint
conversion_status_endpoint:
  path: /v3/converter/{pdf_id}
  method: GET
  
  response:
    status:
      type: string
      enum: [completed]
    
    conversion_status:
      type: object
      description: Per-format status
      properties:
        docx:
          status:
            type: string
            enum: [processing, completed, error]
          error_info:
            type: object
            required: false

# Delete endpoint
delete_endpoint:
  path: /v3/pdf/{pdf_id}
  method: DELETE
  description: Permanently delete PDF and all outputs
  retention_after_delete:
    - status (always "complete")
    - input_file name
    - num_pages
    - timestamps (created_at, deleted_at)
    - version

# Lines data schema
lines_json_schema:
  pages:
    type: array[PdfPageData]
  
  PdfPageData:
    image_id:
      type: string
      description: "{pdf_id}-{page_number}"
    page:
      type: integer
    page_width:
      type: integer
    page_height:
      type: integer
    lines:
      type: array[PdfLineData]
  
  PdfLineData:
    id:
      type: string
    parent_id:
      type: string
      required: false
    children_ids:
      type: array[string]
      required: false
    type:
      type: string
    subtype:
      type: string
      required: false
    line:
      type: integer
    column:
      type: integer
    font_size:
      type: integer
    text:
      type: string
      description: Searchable text
    text_display:
      type: string
      description: MMD with context (sections, images)
    conversion_output:
      type: boolean
    is_printed:
      type: boolean
    is_handwritten:
      type: boolean
    region:
      type: object
      properties:
        top_left_x:
          type: integer
        top_left_y:
          type: integer
        width:
          type: integer
        height:
          type: integer
    cnt:
      type: array[array[integer, integer]]
    confidence:
      type: number
      range: [0, 1]
    confidence_rate:
      type: number
      range: [0, 1]

# Query PDF results
query_endpoint:
  path: /v3/pdf-results
  method: GET
  description: Search PDF processing history
  
  parameters:
    page:
      type: integer
      default: 1
    per_page:
      type: integer
      default: 100
    from_date:
      type: string (ISO datetime)
    to_date:
      type: string (ISO datetime)
```

---

## latex/SPEC.yaml - Document Converter API

```yaml
# Mathpix Document Converter API Specification
# Endpoint: POST /v3/converter

endpoint:
  path: /v3/converter
  method: POST
  description: Convert Mathpix Markdown to other formats
  max_body_size: 10MB

request:
  headers:
    app_id:
      type: string
      required: true
    app_key:
      type: string
      required: true
    Content-Type:
      type: string
      value: application/json

  parameters:
    mmd:
      type: string
      required: true
      description: Mathpix Markdown document text
    
    formats:
      type: object
      required: true
      description: Output formats to generate
      properties:
        md:
          type: boolean
          default: false
          description: Plain Markdown
        docx:
          type: boolean
          default: false
          description: MS Word document
        tex.zip:
          type: boolean
          default: false
          description: LaTeX with images
        html:
          type: boolean
          default: false
          description: HTML file
        pdf:
          type: boolean
          default: false
          description: PDF with HTML rendering
        latex.pdf:
          type: boolean
          default: false
          description: PDF with LaTeX rendering
        pptx:
          type: boolean
          default: false
          description: PowerPoint
        mmd.zip:
          type: boolean
          default: false
          description: MMD with images
        md.zip:
          type: boolean
          default: false
          description: Markdown with images
        html.zip:
          type: boolean
          default: false
          description: HTML with images
    
    conversion_options:
      type: object
      required: false
      description: Format-specific options
      
      docx_options:
        font:
          type: string
          default: "Times New Roman"
          description: Document font family
        fontSize:
          type: integer
          default: 12
          description: Base font size in points
      
      html_options:
        title:
          type: string
          description: HTML page title
        include_svg:
          type: boolean
          default: false
          description: Render math as SVG
      
      tex_options:
        document_class:
          type: string
          default: "article"
          description: LaTeX document class
      
      general_options:
        resource_load_timeout_sec:
          type: integer
          description: Resource loading timeout

response:
  conversion_id:
    type: string
    description: ID to track conversion status and retrieve results

# Status endpoint
status_endpoint:
  path: /v3/converter/{conversion_id}
  method: GET
  
  response:
    status:
      type: string
      enum: [completed, processing, error]
    
    conversion_status:
      type: object
      description: Per-format status

# Results endpoint
results_endpoint:
  path: /v3/converter/{conversion_id}.{format}
  method: GET
  formats:
    - mmd
    - md
    - docx
    - tex (returns .tex.zip)
    - html
    - pdf
    - latex.pdf
    - pptx
    - mmd.zip
    - md.zip
    - html.zip
```

---

## batch/SPEC.yaml - Batch Processing API

```yaml
# Mathpix Batch Processing API Specification
# Endpoint: POST /v3/batch

endpoint:
  path: /v3/batch
  method: POST
  description: Process multiple images in single request
  recommended_use: Non-latency-sensitive workflows
  note: Consider using v3/text with async flag for new implementations

request:
  headers:
    app_id:
      type: string
      required: true
    app_key:
      type: string
      required: true
    Content-Type:
      type: string
      value: application/json

  parameters:
    urls:
      type: object
      required: true
      description: Key-URL pairs for each image
      example:
        image1: "https://example.com/math1.jpg"
        image2:
          url: "https://example.com/math2.jpg"
          region:
            top_left_x: 0
            top_left_y: 0
            width: 100
            height: 100
          formats: ["latex_simplified"]
    
    callback:
      type: object
      required: true
      description: Where to send results
      properties:
        post:
          type: string
          required: true
          description: URL to POST results to
        reply:
          type: object
          required: false
          description: Additional fields for response
        body:
          type: object
          required: false
          description: Additional data in callback
        headers:
          type: object
          required: false
          description: Headers for callback POST
    
    ocr_behavior:
      type: string
      required: false
      enum: [text, latex]
      default: latex
      description: Set to "text" for v3/text behavior
    
    # All v3/latex parameters except src
    formats:
      type: array[string]
    confidence_threshold:
      type: number
    confidence_rate_threshold:
      type: number
    # ... other v3/latex params

response:
  batch_id:
    type: string
    description: Unique batch identifier

# Status endpoint
status_endpoint:
  path: /v3/batch/{batch_id}
  method: GET
  description: Check batch processing status
  
  response:
    urls:
      type: array[string]
      description: Original URL keys
    
    results:
      type: object
      description: Key-result pairs for completed images
    
    callback:
      type: object
      description: Original callback configuration

# Callback payload
callback_payload:
  reply:
    batch_id:
      type: string
    # Plus any callback.reply fields from request
  
  result:
    type: object
    description: Key-result pairs for all images
    example:
      image1:
        latex: "x^2 + y^2 = 9"
        latex_confidence: 0.99
        # ... other v3/latex response fields
      image2:
        latex: "\\frac{a}{b}"
        # ...

retention:
  duration: 2 days
  note: Results available via GET for ~2 days after completion
```

---

## strokes/SPEC.yaml - Handwriting/Strokes API

```yaml
# Mathpix Strokes/Digital Ink API Specification
# Endpoint: POST /v3/strokes

endpoint:
  path: /v3/strokes
  method: POST
  description: Digital ink/handwriting recognition
  features:
    - Handwritten math recognition
    - Text recognition (Hindi, Latin alphabets)
    - Live drawing with intermediate results
    - Scribble to erase
    - Strikethrough support

request:
  headers:
    app_id:
      type: string
      required: true (or app_token)
    app_key:
      type: string
      required: true (or app_token)
    app_token:
      type: string
      required: false
      description: Client-side token (alternative to app_id/app_key)
    Content-Type:
      type: string
      value: application/json

  parameters:
    strokes:
      type: object
      required: true
      description: Stroke coordinate data
      properties:
        strokes:
          type: object
          properties:
            x:
              type: array[array[number]]
              description: X coordinates per stroke
              example: [[131,131,130,130,131], [231,231,233,235]]
            y:
              type: array[array[number]]
              description: Y coordinates per stroke
              example: [[213,213,212,211,210], [231,231,232,235]]
    
    strokes_session_id:
      type: string
      required: false
      description: Session ID for live updates (from app-tokens endpoint)
      note: Requires app_token header
      billing: Billed on first stroke, not on token request
    
    # All v3/text parameters are supported
    formats:
      type: array[string]
      default: ["text"]
    
    data_options:
      type: object
    
    math_inline_delimiters:
      type: array[string, string]
      default: ["\\(", "\\)"]
    
    math_display_delimiters:
      type: array[string, string]
      default: ["\\[", "\\]"]
    
    rm_spaces:
      type: boolean
      default: true
    
    rm_fonts:
      type: boolean
      default: false
    
    confidence_threshold:
      type: number
      range: [0, 1]
    
    confidence_rate_threshold:
      type: number
      range: [0, 1]
    
    include_line_data:
      type: boolean
      default: false
    
    include_word_data:
      type: boolean
      default: false
    
    alphabets_allowed:
      type: object
    
    metadata:
      type: object
    
    tags:
      type: array[string]

response:
  request_id:
    type: string
    description: Unique request identifier
  
  text:
    type: string
    description: Mathpix Markdown with math in delimiters
    example: "\\( 3 x^{2} \\)"
  
  latex_styled:
    type: string
    description: Math LaTeX for equation content
    example: "3 x^{2}"
  
  confidence:
    type: number
    range: [0, 1]
  
  confidence_rate:
    type: number
    range: [0, 1]
  
  is_printed:
    type: boolean
    description: Always false for strokes
  
  is_handwritten:
    type: boolean
    description: Always true for strokes
  
  auto_rotate_confidence:
    type: number
    range: [0, 1]
  
  auto_rotate_degrees:
    type: integer
    enum: [0, 90, -90, 180]
  
  version:
    type: string
    example: "RSK-M100"
  
  data:
    type: array[DataObject]
    required: false
  
  html:
    type: string
    required: false
  
  line_data:
    type: array[LineDataObject]
    required: false
  
  word_data:
    type: array[WordDataObject]
    required: false

live_updates:
  description: Live drawing with intermediate results
  
  setup:
    1: Request app_token with include_strokes_session_id=true
    2: Use strokes_session_id in v3/strokes requests
    3: Send incremental strokes for live updates
  
  pricing:
    - "Session pricing: More expensive than single v3/strokes call"
    - "Session pricing: Less expensive than multiple v3/strokes calls"
    - "Billed on first strokes submission, not token request"
  
  smart_actions:
    scribble_to_erase: true
    strikethrough: true
```

---

## common/SPEC.yaml - Shared Schemas, Auth, Errors

```yaml
# Mathpix Common API Elements
# Authentication, Errors, Shared Schemas

authentication:
  server_side:
    description: Use app_id and app_key headers
    headers:
      app_id:
        type: string
        required: true
        description: Application identifier from console.mathpix.com
      app_key:
        type: string
        required: true
        description: API key from console.mathpix.com
    
    warning: Never include API keys in client-side code
  
  client_side:
    description: Use temporary app_token for client apps
    
    token_endpoint:
      path: /v3/app-tokens
      method: POST
      
      request_headers:
        app_key:
          type: string
          required: true
      
      request_parameters:
        include_strokes_session_id:
          type: boolean
          default: false
          description: Include strokes session for live updates
        
        expires:
          type: integer (seconds)
          default: 300
          range: [30, 43200]  # 30s to 12 hours
          note: Range is [30, 300] when include_strokes_session_id=true
      
      response:
        app_token:
          type: string
          description: Token for v3/text, v3/latex, v3/strokes
        
        strokes_session_id:
          type: string
          required: false
          description: For live digital ink (when requested)
        
        app_token_expires_at:
          type: number (Unix timestamp)
    
    limitations:
      - Cannot access PDF functionality
      - Cannot access historical data
      - Cannot access account admin data
      - Cannot make batch/async requests
    
    usage:
      headers:
        app_token:
          type: string
          description: Use instead of app_id/app_key

# Error handling
errors:
  http_status_codes:
    200: Success (or handled error)
    401: http_unauthorized (invalid credentials)
    429: http_max_requests (rate limited)
  
  error_response_schema:
    error:
      type: string
      description: Human-readable error message (US locale)
    
    error_info:
      type: object
      properties:
        id:
          type: string
          description: Unique error identifier
        message:
          type: string
          description: Error description
        detail:
          type: object
          required: false
          description: Additional error context
  
  error_ids:
    http_unauthorized:
      description: Invalid credentials
      http_status: 401
      recovery: Check app_id and app_key
    
    http_max_requests:
      description: Too many requests
      http_status: 429
      detail_fields: [count]
      recovery: Implement backoff and retry
    
    json_syntax:
      description: Cannot parse request JSON
      http_status: 200
      recovery: Validate JSON syntax
    
    image_missing:
      description: No image specified in request
      http_status: 200
      recovery: Provide src or file
    
    image_download_error:
      description: Cannot download image from URL
      http_status: 200
      detail_fields: [url]
      recovery: Check URL accessibility
    
    image_decode_error:
      description: Cannot decode image data
      http_status: 200
      recovery: Check image format and encoding
    
    image_no_content:
      description: No recognizable content in image
      http_status: 200
      recovery: Ensure image contains text/math
    
    image_not_supported:
      description: Unsupported content (e.g., pure diagram)
      http_status: 200
      recovery: Use appropriate endpoint or parameters
    
    image_max_size:
      description: Image too large to process
      http_status: 200
      recovery: Resize or compress image
    
    opts_bad_callback:
      description: Invalid callback configuration
      http_status: 200
      detail_fields: [post, reply, batch_id]
      recovery: Check callback URL and parameters
    
    opts_unknown_ocr:
      description: Unknown ocr option
      http_status: 200
      detail_fields: [ocr]
      recovery: Use valid ocr values
    
    opts_unknown_format:
      description: Unknown format option
      http_status: 200
      detail_fields: [formats]
      recovery: Use valid format values
    
    math_confidence:
      description: Recognition confidence below threshold
      http_status: 200
      recovery: Lower threshold or improve image quality
    
    math_syntax:
      description: Result is not valid LaTeX
      http_status: 200
      recovery: Check source image quality
    
    batch_unknown_id:
      description: Batch ID not found
      http_status: 200
      detail_fields: [batch_id]
      recovery: Check ID and timing (results expire after ~2 days)
    
    sys_exception:
      description: Server error
      http_status: 200
      recovery: Report to support@mathpix.com

# Query OCR Results
query_ocr_results:
  endpoint:
    path: /v3/ocr-results
    method: GET
    description: Search previous v3/text, v3/strokes, v3/latex results
    note: Only works with API keys created after July 5, 2020
    note2: Results with improve_mathpix=false not included
  
  request_parameters:
    page:
      type: integer
      default: 1
    
    per_page:
      type: integer
      default: 100
    
    from_date:
      type: string (ISO datetime)
      description: Start date (inclusive)
    
    to_date:
      type: string (ISO datetime)
      description: End date (exclusive)
    
    app_id:
      type: string
      description: Filter by specific app_id
    
    text:
      type: string
      description: Search in result.text
    
    text_display:
      type: string
      description: Search in result.text_display
    
    latex_styled:
      type: string
      description: Search in result.latex_styled
    
    tags:
      type: array[string]
      description: Filter by tags
    
    is_printed:
      type: boolean
    
    is_handwritten:
      type: boolean
    
    contains_table:
      type: boolean
    
    contains_chemistry:
      type: boolean
    
    contains_diagram:
      type: boolean
    
    contains_triangle:
      type: boolean
  
  response:
    ocr_results:
      type: array[OcrResultObject]
    
    OcrResultObject:
      timestamp:
        type: string (ISO datetime)
      endpoint:
        type: string
        enum: [/v3/text, /v3/strokes, /v3/latex]
      duration:
        type: number (seconds)
      request_args:
        type: object
      result:
        type: object
        description: Original response
      detections:
        type: object
        properties:
          contains_chemistry:
            type: boolean
          contains_diagram:
            type: boolean
          is_handwritten:
            type: boolean
          is_printed:
            type: boolean
          contains_table:
            type: boolean
          contains_triangle:
            type: boolean

# Query OCR Usage
query_ocr_usage:
  endpoint:
    path: /v3/ocr-usage
    method: GET
    description: Track API usage statistics
  
  request_parameters:
    from_date:
      type: string (ISO datetime)
    
    to_date:
      type: string (ISO datetime)
    
    group_by:
      type: string
      enum: [usage_type, request_args_hash, app_id]
    
    timespan:
      type: string
      description: Aggregation period
  
  response:
    ocr_usage:
      type: array[UsageObject]
    
    UsageObject:
      from_date:
        type: string (ISO datetime)
      app_id:
        type: array[string]
      usage_type:
        type: string
        enum: [image, image-async, pdf, strokes, strokes-session]
      request_args_hash:
        type: array[string]
      count:
        type: integer

# Callback Object (shared schema)
callback_object:
  description: Configuration for async result delivery
  properties:
    post:
      type: string
      required: true
      description: URL to POST results
    
    reply:
      type: object
      required: false
      description: Additional fields in response
    
    body:
      type: object
      required: false
      description: Extra data to include in callback
    
    headers:
      type: object
      required: false
      description: HTTP headers for callback POST

# Latency Optimization
latency_best_practices:
  - "Keep images under 100KB for optimal speed"
  - "Use JPEG compression and downsizing"
  - "Use multipart/form-data upload instead of base64"
  - "Implement user cropping UI to minimize image size"
  - "Use latency-based routing for global users"
  - "Use EU endpoint for EU data processing compliance"
  
  regions:
    us_east_1: N. Virginia
    eu_central_1: Frankfurt (for EU compliance)

# Privacy Settings
privacy:
  improve_mathpix:
    type: boolean
    default: true
    description: Allow Mathpix to retain output for improvement
    setting_location: Request metadata or client configuration
  
  data_retention:
    default: 30 days
    opt_out: 24 hours (when improve_mathpix=false)
    immediate_deletion: Contact support@mathpix.com

# Supported Math Commands (LaTeX vocabulary)
supported_commands:
  greek_letters:
    lowercase: [alpha, beta, gamma, delta, epsilon, zeta, eta, theta, kappa, lambda, mu, nu, xi, pi, rho, sigma, tau, phi, chi, psi, omega, varphi]
    uppercase: [Gamma, Delta, Theta, Lambda, Xi, Pi, Phi, Psi, Omega]
  
  operators:
    - "\\frac"
    - "\\sqrt"
    - "\\sum"
    - "\\prod"
    - "\\int"
    - "\\oint"
    - "\\lim"
    - "\\operatorname"
  
  relations:
    - "\\leq"
    - "\\geq"
    - "\\neq"
    - "\\approx"
    - "\\equiv"
    - "\\sim"
    - "\\simeq"
    - "\\cong"
    - "\\propto"
    - "\\in"
    - "\\notin"
    - "\\subset"
    - "\\supset"
    - "\\subseteq"
    - "\\supseteq"
  
  arrows:
    - "\\rightarrow"
    - "\\Rightarrow"
    - "\\leftrightarrow"
    - "\\Leftrightarrow"
  
  delimiters:
    - "\\left("
    - "\\right)"
    - "\\left["
    - "\\right]"
    - "\\left\\{"
    - "\\right\\}"
    - "\\left|"
    - "\\right|"
    - "\\langle"
    - "\\rangle"
    - "\\lceil"
    - "\\rceil"
    - "\\lfloor"
    - "\\rfloor"
  
  environments:
    - "\\begin{array}"
    - "\\end{array}"
    - aligned (via idiomatic_eqn_arrays)
    - gathered (via idiomatic_eqn_arrays)
    - cases (via idiomatic_eqn_arrays)
  
  special:
    - "\\longdiv" (long division - custom Mathpix command)
    - "\\text"
    - "\\mathbf"
    - "\\mathrm"
    - "\\mathcal"
    - "\\mathbb"
    - "\\overline"
    - "\\vec"
    - "\\hat"
    - "\\tilde"
    - "\\dot"
  
  special_symbols:
    - "\\infty"
    - "\\nabla"
    - "\\partial"
    - "\\forall"
    - "\\exists"
    - "\\emptyset"
    - "\\cdot"
    - "\\cdots"
    - "\\vdots"
    - "\\ddots"
    - "\\times"
    - "\\div"
    - "\\pm"
    - "\\mp"
    - "\\cap"
    - "\\cup"
    - "\\wedge"
    - "\\vee"
    - "\\oplus"
    - "\\otimes"
    - "\\parallel"
    - "\\perp"
    - "\\angle"
    - "\\square"
    - "\\star"
    - "\\circ"
    - "\\dagger"
    - "\\ell"
    - "\\hbar"
    - "\\prime"
    - "\\bot"
    - "\\therefore"
    - "\\because"
```

---

## Usage Examples for Claude Code CLI

```yaml
# Example: Process a math image
curl_example:
  command: |
    curl -X POST https://api.mathpix.com/v3/text \
      -H 'app_id: YOUR_APP_ID' \
      -H 'app_key: YOUR_APP_KEY' \
      -H 'Content-Type: application/json' \
      --data '{
        "src": "https://example.com/math_image.jpg",
        "formats": ["text", "data"],
        "data_options": {
          "include_latex": true,
          "include_asciimath": true
        },
        "math_inline_delimiters": ["$", "$"]
      }'

python_example:
  code: |
    import requests
    import json

    response = requests.post(
        "https://api.mathpix.com/v3/text",
        json={
            "src": "https://example.com/math_image.jpg",
            "formats": ["text", "data"],
            "data_options": {
                "include_latex": True,
                "include_asciimath": True
            }
        },
        headers={
            "app_id": "YOUR_APP_ID",
            "app_key": "YOUR_APP_KEY",
            "Content-Type": "application/json"
        }
    )
    result = response.json()

# Example: Process PDF with conversion
pdf_processing:
  upload: |
    curl -X POST https://api.mathpix.com/v3/pdf \
      -H 'app_id: YOUR_APP_ID' \
      -H 'app_key: YOUR_APP_KEY' \
      -H 'Content-Type: application/json' \
      --data '{
        "url": "https://example.com/document.pdf",
        "conversion_formats": {
          "docx": true,
          "tex.zip": true
        }
      }'
  
  check_status: |
    curl -X GET https://api.mathpix.com/v3/pdf/{pdf_id} \
      -H 'app_id: YOUR_APP_ID' \
      -H 'app_key: YOUR_APP_KEY'
  
  download_result: |
    curl -X GET https://api.mathpix.com/v3/pdf/{pdf_id}.mmd \
      -H 'app_id: YOUR_APP_ID' \
      -H 'app_key: YOUR_APP_KEY' > result.mmd
```

---

This comprehensive YAML documentation extraction covers all Mathpix API endpoints, parameters, response schemas, error codes, and best practices. The documentation is structured for direct consumption by Claude Code CLI for pipeline improvement tasks.