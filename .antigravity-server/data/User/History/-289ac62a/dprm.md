# Mathpix Cloud OCR Ingestion

## Overview
Phase 7 introduced Mathpix Cloud OCR as the primary ingestion engine for the HWPX Reconstruction Pipeline. This pivot was driven by the need for pixel-perfect math formula extraction and reliable layout preservation that standard local OCR engines (EasyOCR/Paddle) struggled to achieve for complex math workbooks.

## 1. API Architecture
The `MathpixIngestor` (`lib/ingestors/mathpix_ingestor.py`) interacts with the Mathpix `v3/pdf` endpoint.

- **Endpoint**: `https://api.mathpix.com/v3/pdf`
- **Authentication**: Requires `app_id` and `app_key` headers.
- **Payload**:
    - `conversion_formats`: `{"md": True}` (Mathpix Markdown / MMD).
    - `math_inline_delimiters`: `["$", "$"]`.
    - `math_display_delimiters`: `["$$", "$$"]`.

## 2. Ingestion Workflow
1. **Upload**: PDF is sent to the Mathpix server.
2. **Polling**: The ingestor polls every 2 seconds until the `status` is `completed`.
3. **Retrieval**: The resulting `.md` file (Mathpix Markdown) is downloaded.
4. **Parsing**: The Markdown is passed to the `MarkdownParser` to be converted into the internal IR.

## 3. Cost Analysis (Pay-As-You-Go)
As of January 2026, the pricing for the Convert API is volume-based:

- **Setup Fee**: $19.99 (one-time, includes $29 credit).
- **Tier 1 (0 - 1M pages)**: $0.005 per page (~KRW 6.5).
- **Tier 2 (> 1M pages)**: $0.0035 per page.

| Scale | Estimated Cost (USD) | Estimated Cost (KRW) |
| :--- | :--- | :--- |
| 1 Page | $0.005 | ₩7 |
| 1,000 Pages | $5.00 | ₩6,500 |
| 10,000 Pages | $50.00 | ₩65,000 |

## 4. Why Mathpix?
- **Superior Math OCR**: Robustly handles fractions, roots, and complex summation/integration symbols.
- **Layout Awareness**: Correctly identifies multi-column text and horizontal separators.
- **High Success Rate**: Bypasses local dependency issues (YOLO patches, OCR model crashes).
- **Korean Support**: Strong performance on CJK characters in technical contexts.
