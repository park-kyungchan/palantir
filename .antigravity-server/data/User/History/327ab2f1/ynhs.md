# Pilot Task Implementation Plan: PDF -> IR (Pre-HWPX)

This document outlines the phased execution for parsing complex PDFs (specifically `sample.pdf`) into a structured Intermediate Representation (IR).

## Phase 1: Layout Analysis (Vision Layer)
- **Goal**: Reliable Region Detection using DocLayout-YOLO.
- **Key Actions**:
    - Integrate `LayoutDetector` with `DoclingIngestor`.
    - Implement `bbox` storage in IR paragraphs and tables.
    - Implement IoU-based "Hybrid Ingestion" matching to tag semantic regions (e.g. `AnswerBox`).
- **Status**: **Completed**. Verified layout detection on `sample.pdf` using DocLayout-YOLO. Resolved critical attribute errors and output format mismatches via a combination of runtime monkey-patching and transparent model wrappers. Implemented `CoordinateScaler` for point-to-pixel alignment.

## Phase 2: Content Ingestion (Semantics Layer)
- **Goal**: High-fidelity Text & Math extraction.
- **Key Actions**:
    - Integrate `OCRManager` (Surya/Paddle) for vision-native content extraction.
    - Implement Equation image-to-LaTeX conversion via specialized math models.
    - Optimize reading order for 2-column layouts using `ReadingOrderSorter`.
    - Validate extraction of specific workbook elements (problem numbers, equation constants).
- **Status**: **Completed**. Implemented a robust Vision-Native OCR pillar. Successfully pivoted to `EasyOCR` after identifying intractable internal failures in `PaddleOCR`. Integration includes `OCRManager` orchestration and `DoclingIngestor` routing. Verified end-to-end text extraction from complex manual regions into correctly tagged IR paragraphs.

## Phase 3: IR Unification (Integration Layer)
- **Goal**: Generation of a unified `lib.ir.Document`.
- **Status**: **Completed**. Mapping of Docling items to IR classes is fully implemented. Integrated `SemanticTagger` to automatically identify `ProblemBox` and `AnswerBox` regions via content heuristics. `ir_output.json` generation and semantic tagging verified via `verify_ir.py`.
- **Key Actions**:
    - Finalize mapping of all Docling items to IR classes.
    - Post-process IR to ensure logical grouping (e.g. grouping paragraphs into "Problems").
    - Export `ir_output.json` for validation.

## Critical Risks & Mitigations
- **Coordinate Mismatch**: Docling uses PDF points (origin bottom-left or top-left depending on SDK), while YOLO results from PyMuPDF renderings might be scaled. **Mitigation**: Implement explicit scaling logic in `LayoutDetector`.
- **Korean Math Quality**: OCR might struggle with Korean specific math notations. **Mitigation**: Prefer LaTeX representation from vision/math models and use a manual PUA map for legacy symbols.
