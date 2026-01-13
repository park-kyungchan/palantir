# Deep Audit Report: OWPML Multi-Column & Equation Implementation

**Date**: 2026-01-07
**Auditor**: Antigravity
**Severity**: 🔴 CRITICAL

---

## Executive Summary

Current `HwpxDocumentBuilder` implementation has **fundamental structural errors** in handling:
1. **Multi-Column Layout** - Using wrong XML structure (paragraph attribute instead of control).
2. **Equation Rendering** - Using text placeholders instead of proper `<hp:eqEdit>` elements.

---

## Stage A: Surface Scan

### Files Analyzed
| File | Finding |
|------|---------|
| `Skeleton.hwpx/section0.xml` | Contains correct `<hp:ctrl><hp:colPr>` structure inside paragraph runs. |
| `lib/owpml/document_builder.py` | Uses incorrect `columnBreak="1"` paragraph attribute. |
| `python-hwpx` source | Lacks native high-level equation abstraction; requires manual XML injection. |

### Legacy Artifacts
- **CLEAN** - No deprecated patterns found.

---

## Stage B: Logic Trace

### ❌ Finding 1: Multi-Column Structure (CRITICAL)

**Expected (from Skeleton.hwpx)**:
```xml
<hp:p ...>
  <hp:run>
    <hp:secPr .../>
    <hp:ctrl>
      <hp:colPr id="" type="NEWSPAPER" layout="LEFT" colCount="2" sameSz="1" sameGap="850"/>
    </hp:ctrl>
  </hp:run>
</hp:p>
```

**Current (WRONG)**:
```python
# document_builder.py line 143
p = ET.SubElement(..., {'columnBreak': '1'})  # ← Wrong approach!
```

**Root Cause**: `colCount` must be in `<hp:colPr>` CONTROL element within a run, not a paragraph attribute.

---

## Stage C: Quality Gate

| Check | Status |
|-------|--------|
| Multi-Column Implementation | ❌ FAIL |
| Equation Implementation | ❌ FAIL |
| Text Insertion | ✅ PASS |
| File Structure | ✅ PASS |

**Quality Gate**: 🔴 **FAIL**

---

## Corrective Action Plan

### Phase 1: Fix Multi-Column (hp:colPr)
1. Modify the document initialization to include `<hp:ctrl><hp:colPr colCount="N"/>`.
2. Ensure the control is placed AFTER the section properties (`secPr`) in the first paragraph's first run.

### Phase 2: Implement Equation (hp:eqEdit)
1. Replace text placeholders with `<hp:ctrl><hp:eqEdit>` elements.
2. Insert `<hp:script>` with the HWP-encoded equation formula.

---

## Technical Reference: KS X 6101 Compliance

| Element | Level | Namespace | Container |
|---------|-------|-----------|-----------|
| `colPr` | Run-level | `hp` | `hp:ctrl` |
| `eqEdit`| Run-level | `hp` | `hp:ctrl` |
| `secPr` | Run-level | `hp` | First `hp:run` of section |
