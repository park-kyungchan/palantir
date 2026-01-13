# Ontology and Schemas

## 1. Digital Twin (SVDOM) Schema
The **Digital Twin (SVDOM)** is the platform-independent document model (`lib/digital_twin/schema.py`) used as the bridge between PDF Ingestion and HWPX Reconstruction.

### 1.1 Core Hierarchy
- **DigitalTwin (Root)**: Entry point containing `sections` and `global_settings`.
- **Section**: Divisions (Pages/Chapters) containing `elements`.
- **Elements**: Polymorphic list of `Paragraph`, `Table`, `Figure`, `MultiColumnContainer`, etc.
- **Paragraph**: Contains `runs` (Atomic content: Text, Equation, Image) and a `style` field.
- **Style**: Captures alignment, weight, and size, or high-level semantic strings (e.g., "ProblemBox").

### 1.2 Schema Convergence
The system maintains compatibility between legacy `lib.ir` dataclasses and the new Pydantic schema using a duck-typing approach in the Compiler.

## 2. HWP Action Ontology
The ontology provides a programmatic representation of the Hancom Office API, mapping manuals to executable models.

### 2.1 Action Knowledge Base (`lib/knowledge/schema.py`)
- **ActionDefinition**: Stores `action_id`, `parameter_set_id`, and creation flags.
- **ParameterSetDefinition**: Describes collections of items (e.g., `CharShape`).
- **APIMethod / Property**: Metadata for root automation object interaction.

### 2.2 Runtime Action Models (`lib/models.py`)
Instruction set for reconstruction. Every `HwpAction` is a validated Pydantic model.
- **Formating**: `SetParaShape` (hanging indents), `SetFontSize`.
- **Structural**: `CreateTable`, `MoveToCell`.
- **Object**: `InsertEquation` (LaTeX), `InsertTextBox` (Absolute positioning).

### 2.3 Type Mapping Matrix
| HWP Type | Python Type |
| :--- | :--- |
| **PIT_BSTR** | `str` |
| **PIT_UI / PIT_I** | `int` |
| **PIT_BOOL** | `bool` |
| **PIT_FLOAT** | `float` |
