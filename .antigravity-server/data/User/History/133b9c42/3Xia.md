# Implementation: HWPX Ingestion Logic

The `HwpxIngestor` (`lib/ingest_hwpx.py`) is designed for high-fidelity extraction of Structure and Styles directly from HWPX (OOXML-compliant) ZIP archives.

## 1. HWPX Architecture mapping
An HWPX file is a ZIP containing XML components. The ingestor primarily targets `Contents/section0.xml` for logical content and `Contents/header.xml` for global styles.

### 1.1 Namespace Handling
Precise XML parsing requires handling Hancom's specific namespaces:
| Prefix | Namespace URI |
| :--- | :--- |
| `hp` | `http://www.hancom.co.kr/hwpml/2011/paragraph` |
| `hc` | `http://www.hancom.co.kr/hwpml/2011/core` |
| `hh` | `http://www.hancom.co.kr/hwpml/2011/head` |

## 2. Structural Parsing
The ingestor maps hierarchical XML tags to the internal **Intermediate Representation (IR)**:

### 2.1 Paragraphs (`hp:p`)
Maps to `lib.ir.Paragraph`.
- **Properties**: Alignment mapping (`Center`, `Left`, `Right`, `Distribute`).
- **Runs**: Decomposition into `hp:run` elements containing text (`hp:t`).

### 2.2 Tables (`hp:tbl`)
- **Grid Mapping**: Navigates through row/cell nodes.
- **Content**: Recursively parses paragraph nodes found inside cells.

## 3. Style Persistence (Future Work)
- **Current Status**: Local property overrides (e.g., Bold, Font Size) are captured if explicit.
- **Challenge**: HWPX uses `charPrIDRef` to reference shared style tables in `header.xml`. High-fidelity reconstruction requires full resolution of these ID tables to ensure style-perfect cloning.

## 4. Key Implementation Patterns
- **XPath Search**: Uses `.//hp:p` with namespace dictionaries for robust node identification.
- **ZIP Access**: Uses `zipfile.ZipFile` for non-destructive reading of document internals.
