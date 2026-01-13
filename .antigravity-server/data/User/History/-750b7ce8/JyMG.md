# KS X 6101:2024 & AI Agent Framework Research (January 2026)

## 1. Executive Summary
The 2024 revision of **KS X 6101 (OWPML)** represents a fundamental shift from document rendering to **data interoperability and AI friendliness**. This report details the technical evolution of the standard and proposes a Python-based **Agentic RAG** framework for precision HWPX control.

## 2. KS X 6101:2024 Evolution
The latest revision (2024-10-30) prioritizes structural clarity over visual representation.

| Revison Area | Technical Improvement | AI/Agent Benefit |
|---|---|---|
| **Metadata** | Standardized `<opf:meta>` for history and tags. | Enhances RAG search quality and context awareness. |
| **Interoperability** | Optimized schema for PDF/A and web conversion. | Prevents layout breakage during cross-format generation. |
| **Visualization** | Advanced definitions for charts and graphics. | Allows AI to generate complex visual data structures. |

## 3. HWPX Container Anatomy (OPC Compliance)
A high-fidelity pipeline must strictly adhere to the Open Packaging Conventions (OPC):

- **`mimetype`**: Must be the **first file**, **not compressed**, and contain `application/hwp+zip`.
- **`content.hpf`**: The "Map" of the document. Defines Section order (Spine) and all Resource IDs (Manifest).
- **`header.xml`**: Global property registry.本本 (section0.xml) only references IDs defined here.
- **Reference Mechanism**: Uses a relational-style ID system (e.g., `<hp:run charPrIDRef="2">`). Requires sequential logic: Define in Header -> Get ID -> Reference in Section.

## 4. Agentic RAG Architecture
To overcome the lack of training data for OWPML, an **Agentic RAG** strategy is proposed:

### 4.1 Schema-Aware Knowledge Base
- **Structural Chunking**: Split documentation by XML Element units (`<hp:tbl>`, `<hp:pic>`).
- **Metadata Bundling**: Include mandatory attributes, child constraints, and validation rules in each chunk.

### 4.2 Planning & Reasoning Module
- **Chain of Thought**: Agent must check dependency (Header) before inserting content (Section).
- **Multi-Agent Role**:
  - **Planner**: Maps user intent to XML schema requirements.
  - **Coder**: Implements the "Unzip-Modify-Repack" Python logic.

## 5. Engineering Pipeline: "Unzip-Modify-Repack"
A robust Python framework should use `zipfile`, `xml.etree`, and `lxml` for the following flow:

1. **Deconstruction**: Unzip to temp folder, parse `content.hpf` to identify active sections.
2. **Manipulation**:
   - Register Namespaces (`hp`, `hh`, `ha`, `opf`) to prevent "ns0" prefixing.
   - Synchronize IDs: Fetch max ID from HeaderManager and increment for new objects.
3. **Reconstruction**: 
   - Write XML with `encoding='utf-8'` and XML declarations.
   - Re-zip with `mimetype` as the first uncompressed entry.

## 6. Advanced Object Management
- **Tables**: Logic must handle `<hp:tblGrid>` (column widths) and correctly skip "Ghost Cells" in merged regions using `<hp:cellSpan>`.
- **Images**: Workflow: Copy to `BinData/` -> Register in `<opf:manifest>` -> Reference in `<hp:pic>` -> Update `<hh:beginNum>` in Header.

## 7. Resource Acquisition & Technical Ground Truth

Given that the full **KS X 6101:2024** specification costs ~₩167,200 and is not freely available, the following resources serve as the developer's technical ground truth:

### 7.1 Hancom Official GitHub: `hwpx-owpml-model`
- **Link**: [`hancom-io/hwpx-owpml-model`](https://github.com/hancom-io/hwpx-owpml-model)
- **Role**: Official OWPML filter model (C++).
- **Utility**: Header files (`.h`) define the definitive XML element hierarchies and attribute types (e.g., `SectionDefinitionType.h`).

### 7.2 The "Golden Template" (`Skeleton.hwpx`)
- **Strategy**: Use an official skeleton file as the base for all generation.
- **Benefits**: Guarantees correct header structures and baseline ID mappings that Hancom Word expects.

### 7.3 Supplementary Links
- **Hancom Developer Portal**: [developer.hancom.com](https://developer.hancom.com)
- **Legacy Specs**: [hancom.com/support/downloadCenter/hwpOwpml](https://www.hancom.com/support/downloadCenter/hwpOwpml)

---
*Derived from the "KS X 6101:2024 Technical Standards Research" (Architect Report, Jan 2026).*
