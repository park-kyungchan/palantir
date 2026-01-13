# Advanced OWPML Element Coverage - Implementation Plan

**Date:** 2026-01-08
**Protocol:** `/01_plan` (3-Stage Planning)
**Objective:** Assess feasibility of covering advanced OWPML elements using `hancom-io/hwpx-owpml-model`.

---

## Stage A: Blueprint (Surface Scan)

### Evidence Summary
| Item | Finding |
|:---|:---|
| **hancom-io/hwpx-owpml-model** | C++ filter model. MIT Licensed. 100+ element classes in `OWPML/Class/Para/`. |
| **Element Priority Keywords** | `tbl` (11 hits), `eqEdit` (0 hits - likely different naming), `ctrl` (not searched directly). |
| **Current Implementation** | `HwpxDocumentBuilder` has 19 methods covering core elements. |

### Complexity Assessment
**LARGE** (6-7 Phases Required)

---

## Stage B: Integration Trace

### Current Implementation Status

| Category | Implemented | Gap |
|:---|:---|:---|
| **Text & Paragraphs** | ✅ InsertText, SetParaShape, SetAlign | - |
| **Tables** | ✅ CreateTable, MoveToCell, SetCellBorder, MergeCells | Complex nested tables, cell merging edge cases |
| **Equations** | ✅ InsertEquation (LaTeX -> HWP Script) | Advanced formatting, multi-line equations |
| **Images** | ✅ InsertImage (inline) | Floating images, cropping |
| **TextBoxes** | ✅ InsertTextBox | Linked textboxes |
| **Lists** | ✅ SetNumbering (Bullet/Number) | Multi-level nested lists |
| **Page Setup** | ✅ SetPageSetup | Headers, Footers |
| **Footnotes/Endnotes** | ❌ | Full implementation needed |
| **Chart/OLE** | ❌ | Out of scope (complex) |
| **Field Controls** | ❌ | Partial (memo fields) |
| **Drawing Shapes** | ❌ | Lines, Arrows, Freeform |

### Hancom Model Cross-Reference Utility

The `hwpx-owpml-model` C++ headers can provide:
1.  **Element Names**: XML tag names for each control type.
2.  **Attribute Lists**: Required and optional attributes per element.
3.  **Nesting Rules**: Parent-child relationships.

**Limitation**: C++ model is a *filter* (read/parse), not a *generator*. It defines structures but doesn't show generation logic.

---

## Stage C: Quality Gate & Feasibility

### Feasibility Assessment

| Question | Answer |
|:---|:---|
| **Can hwpx-owpml-model fully close gaps?** | **PARTIAL**. It provides element definitions but lacks generation examples. |
| **Is Python port feasible?** | YES, but requires significant effort (translating C++ class structures to Python Element creation). |
| **Alternative approach?** | Use `python-hwpx` source code for Python-native patterns, supplemented by Hancom model for reference. |
| **Recommended hybrid strategy?** | YES - Primary: `python-hwpx` internals. Secondary: `hwpx-owpml-model` for element verification. |

### Risk Assessment

| Risk | Probability | Impact | Mitigation |
|:---|:---|:---|:---|
| C++ → Python translation errors | Medium | High | Cross-verify with actual HWPX output from Hancom Word. |
| Incomplete attribute coverage | Medium | Medium | Skeleton.hwpx provides baseline attributes. |
| Scope creep (100+ elements) | High | High | Prioritize by user demand (Footnotes → Shapes → Charts). |

---

## Proposed Implementation Phases

### Phase 15: Footnotes & Endnotes
- **Goal**: Implement `InsertFootnote`, `InsertEndnote` actions.
- **Reference**: `OWPML/Class/Para/FootnoteType.h` (if exists).
- **Test**: Verify rendering in HWP 2024.

### Phase 16: Headers & Footers
- **Goal**: Extend `SetPageSetup` to include header/footer content.
- **Reference**: `python-hwpx` docs on `headerApply`/`footerApply`.

### Phase 17: Advanced Table Formatting
- **Goal**: Cell background gradients, border patterns, vertical text.
- **Reference**: `OWPML/Class/Para/CellType.h`, `borderFill` in Head.

### Phase 18: Drawing Shapes
- **Goal**: Lines, Arrows, Basic Polygons.
- **Reference**: `AbstractDrawingObjectType.h`, `ShapeObjectType.h`.
- **Scope Limit**: Exclude freeform (complex bezier).

### Phase 19: Field Controls
- **Goal**: Hyperlinks, Bookmarks, Cross-references.
- **Reference**: `FieldType.h` (if exists).

---

## Conclusion & Recommendation

| Verdict | Rationale |
|:---|:---|
| **유효함 (Feasible)** | `hwpx-owpml-model`은 엘리먼트 정의 레퍼런스로 활용 가능. Python 구현은 `python-hwpx` 소스 코드와 병행 참조 전략 권장. |
| **권장 우선순위** | Phase 15 (Footnotes) → Phase 16 (Headers/Footers) → Phase 17 (Advanced Tables). |
| **리소스 예상** | 각 Phase 당 3-5시간 (Deep Audit + Implementation + Verification). |

---

> [!IMPORTANT]
> `hwpx-owpml-model` Clone은 **참조용**으로만 사용. 직접 빌드나 C++ 코드 실행은 불필요.
> `docs/` 폴더 내 `python-hwpx` 사용 가이드와 병행하여 진행.
