# Plan: Advanced OWPML Element Coverage (Phases 15-19)

## 1. Objective
Achieve full structural fidelity for scientific objects and interactive controls by integrating native HWPX engine logic from official C++ models.

## 2. Implementation Methodology
A **Hybrid Strategy** is employed:
- **Primary Source**: `python-hwpx` internal models (Python-native patterns).
- **validation Source**: `hancom-io/hwpx-owpml-model` (Attribute & Element names).
- **Verification**: `Skeleton.hwpx` comparison.

## 3. Targeted Phases

### Phase 15: Footnotes & Endnotes
- **Goal**: Implement `InsertFootnote` and `InsertEndnote` actions.
- **Reference**: `<hp:footNote>` tag mapping in `SectionDefinitionType.h`.
- **Status**: 🛠️ **RESEARCHING**

### Phase 16: Headers & Footers
- **Goal**: Extend `SetPageSetup` to populate `<hp:header>` and `<hp:footer>` contents.
- **Reference**: `HwpxDocument.add_paragraph(section=section, ...)` from `python-hwpx`.

### Phase 17: Advanced Table Formatting
- **Goal**: Cell background patterns, gradient fills, and vertical text alignment.
- **Reference**: `hh:borderFill` extension in `header_manager.py`.

### Phase 18: Drawing Shapes & Vector Objects
- **Goal**: Basic geometric shapes (`hp:rect`, `hp:ellipse`) and line connectors.
- **Reference**: `AbstractDrawingObjectType.h` for absolute coordinate attributes.

---

## 4. Risks & Mitigation
| Risk | Impact | Mitigation |
|---|---|---|
| Attribute Drift | Invalid HWPX | Use `hwpx-owpml-model` as the definitive schema reference. |
| Memory Bloat | Browser Lag | Maintain singleton `HeaderManager` instance across conversion sessions. |
| Namespace Collision | Parsing Error | Hardcode standard OWPML 2011/2016 URIs. |

**Status**: 🛠️ **PLANNING** (Ready for Execution)
