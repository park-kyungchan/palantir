# Implementation: IR-to-HWP Compiler

The `Compiler` is the engine that translates high-level document models (IR or Digital Twin) into the granular `HwpAction` ontology.

## 1. Architectural Role
The Compiler receives a document object and produces a sequential list of JSON-serializable actions. It serves as a polyglot translator, reconciling structural differences between various ingestion outputs (OCR, Markdown, etc.).

## 2. Compilation Strategy
The compiler uses a **Recursive Dispatch** pattern to process the document tree.

### 2.1 State-Aware Compilation
To minimize redundant formatting calls, the compiler maintains internal state for:
- Font Size, Bold, Alignment, Line Spacing.
It only emits a change action when the IR deviates from the current state.

### 2.2 Structural Handling
- **Paragraphs**: Groups `TextRun`, `Equation`, and `Image` elements, ensuring alignment and spacing are set before text insertion.
- **Tables**: Emits `CreateTable`, then iterates through cells using `MoveToCell` to compile cell contents recursively.
- **Multi-Column Containers**: Uses `BreakSection` or invisible tables to manage layout flow.

## 3. Semantic Style Mapping
The compiler translates high-level semantic tags into HWP formatting patterns:
- **ProblemBox**: Mapped to a paragraph with a **Hanging Indent** (using `SetParaShape`).
- **AnswerBox**: Mapped to a **1x1 Invisible Table** construct to ensure strict vertical/horizontal bounding.
- **Header**: Mapped to bold text with font size increases.

## 4. Resource Management
- **Remote Asset Downloading**: Automatically handles `http(s)` paths in `Image` objects, caching images locally via MD5 hashing to avoid redundant network calls.
- **Knowledge Base Validation**: The compiler validates action names against the `ActionDatabase` to prevent generating "hallucinated" or invalid HWP API calls.
