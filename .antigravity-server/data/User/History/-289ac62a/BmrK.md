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

## 5. Infrastructure & Performance
### 5.1 Lazy-Loading Strategy
Integration with Mathpix allowed the pipeline to adopt a **Hybrid Ingestion Model**. To avoid the heavy memory and time overhead of loading `Docling` or `transformers` (which can cause ~30s delays or timeouts), the pipeline uses lazy imports:
- `lib/pipeline.py` only imports heavyweight ML libraries if `use_mathpix=False`.
- This ensures high-speed execution when using the lightweight Cloud API.

### 5.2 Authentication Verification
Mathpix typically requires both `app_id` and `app_key`. 
- **Verification Trace**: Verified using `curl` that a generic or test `app_id` works with a valid `app_key` for basic OCR tasks.
- **Environment**: Keys are injected via `MATHPIX_APP_ID` and `MATHPIX_APP_KEY` environment variables.

## 6. Troubleshooting
### 6.1 KeyError: 'pdf_id' (Internal Error)
- **Symptom**: The pipeline fails with `KeyError: 'pdf_id'` even if the response status is 200, containing `{'error': 'Internal error'}`.
- **Cause**: Passing complex nested dictionaries (like `conversion_formats`) directly in the `data` parameter of a multipart/form-data request (`requests.post(..., files=..., data=...)`) can confuse the server.
- **Resolution**: Use the `options_json` field. All configuration parameters should be packed into a single JSON string and sent as `data={"options_json": json.dumps(options)}`.
