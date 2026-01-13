# Implementation: IR-to-HWP Compiler

The `Compiler` is the engine that translates high-level document models (IR) into the granular `HwpAction` ontology. It handles state tracking and structural decomposition.

## 1. Architectural Role
The Compiler receives a `Document` object and produces a sequential list of JSON-serializable actions. This list is then sent across the WSL Bridge to the Windows-side `Executor`.

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

## 3. Key Components (`lib/compiler.py`)
- `compile(doc)`: Root method returning a list of dict-serialized actions.
- `_compile_element(elem)`: Polymorphic dispatcher for IR elements.
- `_compile_text_run(run)`: Handles font property logic.

## 4. Current Limitations
- **Style Tables**: Currently does not parse HWPX `header.xml` style tables; it relies on direct property overrides.
- **Absolute Positioning**: Limited support for floating images outside of `InsertTextBox`.
- **Direct Rendering Gap**: There is currently no Linux-native pipeline to reconstruct a `DigitalTwin` (SVDOM) directly into a PDF or PNG image. Visual verification depends on the ODA `visualizer.py` (annotations) or through full actuation via the `WSLBridge` to the Windows host.
