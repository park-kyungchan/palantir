# Implementation: IR-to-HWP Compiler

The `Compiler` is the engine that translates high-level document models (IR) into the granular `HwpAction` ontology. It handles state tracking and structural decomposition.

## 1. Architectural Role
The Compiler receives a document object (supporting both the legacy `lib.ir` and the modern `lib.digital_twin.schema.DigitalTwin`) and produces a sequential list of JSON-serializable actions. It serves as a polyglot translator, reconciling structural differences between verschiedenen ingestion outputs.

## 2. Compilation Strategy
The compiler uses a **Recursive Dispatch** pattern to process the document tree.

### 2.1 State Tracking
To minimize redundant API calls, the Compiler maintains internal state for:
- Current Font Size
- Bold Status
- Alignment
- Line Spacing

It only emits a `SetAction` when the style in the IR deviates from the current compiler state.

### 2.2 Structural Handling
- **Sections**: Triggers `SetPageSetup` and global column defaults.
- **Paragraphs**: Groups `TextRun`, `Equation`, and `Image` elements. It ensures proper alignment and spacing are set before text insertion.
- **Tables**:
    1. Emits `CreateTable`.
    2. Iterates through rows and cells.
    3. Emits `MoveToCell`.
    4. Recursively compiles the contents of the cell.
- **Multi-Column Containers**:
    - Uses `BreakSection(continuous=True)` to switch column counts without forcing a new physical page.
    - Emits `MultiColumn` settings.
    - Uses `BreakColumn` to navigate between logical columns.

### 2.3 Semantic Style Mapping
The compiler translates high-level semantic tags identified during ingestion into specific HWP formatting patterns:
- **ProblemBox**: Mapped to a `Paragraph` where a `SetParaShape` action is emitted at the start to apply a **Hanging Indent** (usually -20pt to -30pt). A `SetParaShape(left_margin=0, indent=0)` reset is emitted after the paragraph elements.
- **AnswerBox**: Mapped to a **1x1 Table** construct. The content is recursively compiled inside the single cell, and `SetCellBorder` is used to create a visible frame.
- **Header**: Mapped to bold text with a font size increase (e.g., 14pt).

## 3. Key Components (`lib/compiler.py`)
- `compile(doc)`: Root method accepting a `DigitalTwin` and returning a list of dict-serialized actions.
- `_compile_element(elem)`: Polymorphic dispatcher for `Section` elements.
- `_compile_paragraph(para)`: Applies Semantic Tags (indentation, bolding) and iterates through runs.
- `_compile_run(run)`: Standardized handler for `Run` objects (Text, Equation, Image).

## 3.4 Heuristic vs. Schema Mapping (Pydantic Validation)
A critical implementation detail in ODA v6.0 is the reconciliation of high-level heuristic labels with strict Pydantic schemas:
- **Challenge**: The `SemanticTagger` and `DoclingIngestor` often use strings (e.g., `style="ProblemBox"`) for rapid tagging.
- **Constraint**: The `DigitalTwin (SVDOM) Paragraph` model originally expected a `Style` object.
- **Resolution**: Updated `lib/digital_twin/schema.py` to support `Union[Style, str]`. The Compiler performs equality checks that handle both structured `Style` objects and string aliases.

## 3.5 Dual Schema Compatibility
The compiler is designed to be backwards compatible with the dataclass-based `lib.ir` models while prioritizing the Pydantic `DigitalTwin` schema.
- **Polymorphic Type Checking**: `_compile_element` and `_compile_run` use multi-type `isinstance` checks: `isinstance(elem, (Paragraph, IRParagraph))` and `isinstance(run, IRTextRun)`.
- **Dynamic Attribute Access**: To handle naming discrepancies (e.g., `runs` in DigitalTwin vs `elements` in IR), the compiler uses defensive extraction:
  ```python
  runs = getattr(para, 'runs', None) or getattr(para, 'elements', [])
  ```
- **Run Property Normalization**: Reconciles flat attributes (e.g., `run.font_size` in IR) with nested structures (e.g., `run.style.font_size` in DigitalTwin) by performing cascading checks in `_compile_run`.
- **Type Differentiation**: Resolved an `AttributeError` where the compiler accessed `run.type` directly on objects (like `Equation`) that lacked the attribute. The logic was updated to use a calculated `rtype` variable (derived from `type(run).__name__` or `run.type` if available) to ensure stable dispatching.
- **Alignment Mapping**: Reconciles legacy `para.alignment` (direct attribute) with `para.style.alignment` (nested object).
- **Remote Asset Downloading**: Automatically handles `http(s)` paths in `Image` objects.
    - **Caching**: Uses MD5 hashing of URLs to avoid redundant downloads.
    - **Storage**: Maps remote assets to a local `images_mathpix/` directory.
    - **Absolute Binding**: Converts relative or remote paths to absolute local paths prior to emitting `InsertImage` actions to ensure the HWP automation engine can locate the files.

## 4. Current Limitations
- **Style Tables**: Currently does not parse HWPX `header.xml` style tables; it relies on direct property overrides.
- **Absolute Positioning**: Limited support for floating images outside of `InsertTextBox`.
- **Direct Rendering Gap**: There is currently no Linux-native pipeline to reconstruct a `DigitalTwin` (SVDOM) directly into a PDF or PNG image. Visual verification depends on the ODA `visualizer.py` (annotations) or through full actuation via the `WSLBridge` to the Windows host.

## 5. Knowledge Base Integration (ActionTable)
The Compiler is now grounded in the official HWP reference manual via the `ActionDatabase`.

### 5.1 Validation Logic
- **Initialization**: On `__init__`, the Compiler loads its internal "Engine Brain" from `lib/knowledge/hwpx/action_db.json`.
- **Action Validation**: The `_validate_action(action)` method ensures that any generated `HwpAction` corresponds to a valid Action ID in the Hancom API.
- **Strict Mode**: A `strict_mode` flag controls whether the compiler should fail or merely warn when an unrecognized action is encountered.

### 5.2 Benefits
- **API Fidelity**: Prevents the generation of "hallucinated" action names that would fail on the Windows executor.
- **Automatic Parameter Mapping**: Logic can be extended to automatically retrieve the correct `ParameterSet` for any given action from the KB.
