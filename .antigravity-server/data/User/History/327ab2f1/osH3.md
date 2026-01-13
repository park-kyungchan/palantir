# Pilot Task Implementation Plan: PDF -> IR (Pre-HWPX)

This document outlines the phased execution for parsing complex PDFs (specifically `sample.pdf`) into a structured Intermediate Representation (IR).

## Phase 1: Layout Analysis (Vision Layer)
- **Goal**: Reliable Region Detection using DocLayout-YOLO.
- **Key Actions**:
    - Integrate `LayoutDetector` with `DoclingIngestor`.
    - Implement `bbox` storage in IR paragraphs and tables.
    - Implement IoU-based "Hybrid Ingestion" matching to tag semantic regions (e.g. `AnswerBox`).
- **Status**: Completed implementation and logic verification via `scripts/verify_layout.py`. Note: Docling encountered `utf-8` encoding errors on `sample.pdf` and YOLO weights showed attribute mismatches (`bn`); logic was verified using injected regions and a PyMuPDF fallback refined to support layout hints.

## Phase 2: Content Ingestion (Semantics Layer)
- **Goal**: High-fidelity Text & Math extraction.
- **Key Actions**:
    - Use Docling's math model for LaTeX extraction.
    - Optimize reading order for 2-column layouts using `ReadingOrderSorter`.
    - Validate extraction of specific workbook elements (problem numbers, equation constants).
- **Status**: In Progress. Initial schema for `Equation` mapping is implemented. Qualitative validation of Korean-specific LaTeX output is pending for `sample.pdf`.

## Phase 3: IR Unification (Integration Layer)
- **Goal**: Generation of a unified `lib.ir.Document`.
- **Key Actions**:
    - Finalize mapping of all Docling items to IR classes.
    - Post-process IR to ensure logical grouping (e.g. grouping paragraphs into "Problems").
    - Export `ir_output.json` for validation.

## Critical Risks & Mitigations
- **Coordinate Mismatch**: Docling uses PDF points (origin bottom-left or top-left depending on SDK), while YOLO results from PyMuPDF renderings might be scaled. **Mitigation**: Implement explicit scaling logic in `LayoutDetector`.
- **Korean Math Quality**: OCR might struggle with Korean specific math notations. **Mitigation**: Prefer LaTeX representation from vision/math models and use a manual PUA map for legacy symbols.
