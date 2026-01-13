# HWPX Reconstruction Pipeline: Purpose & Architecture

This document combines the high-level project goals with the technical "Digital Twin" paradigm used to achieve high-fidelity document conversion.

## 1. Project Purpose

The **HWPX Reconstruction Pipeline** is a specialized automation framework designed to solve the challenge of high-fidelity document conversion into the Hancom Office (HWPX) format. 

### Core Problem
Standard document converters often fail to maintain the complex structural integrity of Hancom Office documents (e.g., specific table behaviors, multi-column newspaper layouts, and OLE-based form elements). This project bridges the gap by using native automation to "reconstruct" documents in the actual application.

### Control Manual Integration
Beyond simple reconstruction, the parsed artifacts (e.g., `ActionTable_2504.pdf`) serve as **Operational Manuals** for the AI Agent. These documents define the Action IDs and ParameterSet IDs required to programmatically control Hancom Office 2024 on the Windows host.

## 2. The Digital Twin & SVDOM Paradigm

The "Digital Twin" approach move from traditional OCR/Layout analysis to a **Vision-Native De-rendering** strategy.

### The Semantic-Visual DOM (SVDOM)
The core data structure is a Hybrid JSON Schema called the SVDOM. It enforces strict separation of concerns:
1.  **Content (The "What")**: Raw data (text, LaTeX math, images).
2.  **Style (The "How")**: Visual presentation metadata (alignment, fonts, padding).
3.  **Geometry (The "Where")**: Physical bounding boxes (`bbox`) for "Vision-Native" verification.

### Strategic Objectives
- **Fidelity**: Use Vision LLMs (e.g., Gemini 3.0 Pro) to "de-render" pixels directly into SVDOM, bypassing structural failures of traditional OCR.
- **Interactivity**: Enable natural language editing of the document structure.
- **Precision**: Extract math as LaTeX and tables as semantic arrays.

## 3. Key Features & Flow
- **Vision-Native De-rendering**: Gemini 3.0 Pro transforms PDF pixels into SVDOM JSON.
- **Multi-Engine Ingestion**: Support for `Docling`, `Surya`, and `PyMuPDF`.
- **Hancom Office 2024 Support**: Optimized for OOXML-compliant HWPX structures.
- **Automated Reconstruction**: The Agent "types" and "builds" the document using internal action models based on the SVDOM.
