# Protocol: Interactive Editing (Read-Edit-Write)

The Digital Twin paradigm enables a robust **Read-Edit-Write** loop for document engineering. The system processes user intent by manipulating the SVDOM (Semantic-Visual DOM).

## 1. Scenario-Based Protocols

### Scenario A: Content Modification (The "Fix")
When a user requests a content correction (e.g., "Fix the typo in the math formula in Q3"):
1.  **Identification**: The agent searches for the block with `role="question"` and matching content or an explicit `id`.
2.  **Targeting**: Accesses the `block.content` object.
3.  **Atomic Update**: Modifies only the required field (e.g., `latex`). Other fields (Style/Geometry) are preserved to maintain visual consistency.

### Scenario B: Layout Adjustment (The "Transform")
When a user requests a structural change (e.g., "Add 10px padding to all questions"):
1.  **Batch Selection**: Uses `twin.query_blocks(role="question")` to gather all relevant atoms.
2.  **Attribute Injection**: Iterates through selections and updates the `block.style.padding` property.
3.  **Propagation**: The changes are applied to the SVDOM, which is then re-rendered into the final output.

## 2. Export Strategy

The conversion from the Digital Twin JSON back to a viewable format follows a two-stage compilation:
1.  **Intermediate Compilation**: The SVDOM is walked to generate a structured string (e.g., HTML/CSS or Markdown).
2.  **Final Rendering**: 
    - **Digital/Web**: Rendered as HTML where `Style` properties map to CSS.
    - **High-Fidelity Document**: Rendered via `WeasyPrint` or LaTeX, ensuring that `GlobalSettings` (page margins/padding) are respected.

## 3. Validation Utility

The `scripts/demo_digital_twin.py` utility serves as the verification harness for this protocol, simulating the full lifecycle from an initial "de-rendered" state through multiple edit scenarios to a final Markdown export.
