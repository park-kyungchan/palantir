# HWPX Reconstruction Pipeline: Project Purpose

The **HWPX Reconstruction Pipeline** is a specialized automation framework designed to solve the challenge of high-fidelity document conversion into the Hancom Office (HWPX) format. 

## Core Problem
Standard document converters often fail to maintain the complex structural integrity of Hancom Office documents (e.g., specific table behaviors, multi-column newspaper layouts, and OLE-based form elements). This project bridges the gap by using native automation to "reconstruct" documents in the actual application.

## Control Manual Integration
Beyond simple reconstruction, the parsed artifacts (e.g., `ActionTable_2504.pdf`) serve as **Operational Manuals** for the AI Agent. These documents define the Action IDs and ParameterSet IDs required to programmatically control Hancom Office 2024 on the Windows host, enabling the Agent to execute precise document engineering tasks using native API sequences.

## Key Features
- **High-Fidelity Reconstruction**: Instead of simple file-format conversion, the system "types" and "builds" the document using Hancom's internal action models.
- **Vision-Native De-rendering**: Leverages Gemini 3.0 Pro to transform complex PDF pixels (Math/Tables) directly into a structured "Digital Twin" JSON.
- **Multi-Engine Ingestion**: Support for `Docling` (layout analysis), `Surya` (fast OCR), and `PyMuPDF` (text extraction).
- **Hancom Office 2024 Support**: Optimized for the latest version of the office suite, including OOXML-compliant HWPX structures.
- **Automated Security Bypass**: Implements techniques to suppress HWP's internal security dialogs for unattended execution.

## Use Cases
- **Church Bulletin Automation**: Generating weekly "주일주보" (Sunday Bulletins) with multi-column newspaper layouts and embedded tables.
- Converting legacy PDFs to editable HWPX files.
- Re-verifying and repairing corrupted HWPX structures.
- Automated document generation from standardized JSON payloads.
