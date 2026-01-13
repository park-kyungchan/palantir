# Deep Audit Report: OWPML Multi-Column & Equation Implementation

**Date**: 2026-01-07
**Auditor**: Antigravity
**Severity**: 🔴 CRITICAL

---

## Executive Summary

Current `HwpxDocumentBuilder` implementation has **fundamental structural errors** in handling:
1. **Multi-Column Layout** - Using wrong XML structure
2. **Equation Rendering** - Using text placeholders instead of proper `<hp:eqEdit>` elements

---

## Stage A: Surface Scan

### Files Analyzed
| File | Finding |
|------|---------|
| `Skeleton.hwpx/section0.xml` | Contains correct `<hp:ctrl><hp:colPr>` structure |
| `lib/owpml/document_builder.py` | Uses incorrect `columnBreak="1"` attribute |
| `python-hwpx` source | No equation support classes |

### Legacy Artifacts
- **CLEAN** - No deprecated patterns found

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

**Root Cause**: `colCount` must be in `<hp:colPr>` CONTROL element, not paragraph attribute.

---

### ❌ Finding 2: Equation Rendering (CRITICAL)

**Expected OWPML Structure**:
```xml
<hp:ctrl>
  <hp:eqEdit version="2">
    <hp:script>x^{2}+y^{2}=r^{2}</hp:script>
  </hp:eqEdit>
</hp:ctrl>
```

**Current (WRONG)**:
```python
# document_builder.py
placeholder_text = f"[수식: {action.script}]"
self._insert_text(InsertText(text=placeholder_text))
```

**Root Cause**: Equations require `<hp:eqEdit>` control element with HWP equation script syntax.

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
1. Modify first paragraph to include `<hp:ctrl><hp:colPr colCount="N"/>` 
2. Insert colPr AFTER secPr in the same run
3. `colCount` attribute determines column count

### Phase 2: Implement Equation (hp:eqEdit)
1. Create `<hp:ctrl><hp:eqEdit>` element
2. Insert `<hp:script>` with equation text
3. Place inside `<hp:run>` where equation should appear

### Phase 3: Verify with HWP 2024
1. Generate test file with 2-column and equation
2. Open in HWP 2024 to validate rendering

---

## Technical Reference

### colPr Attributes (from Skeleton.hwpx)
| Attribute | Description | Example |
|-----------|-------------|---------|
| `colCount` | Number of columns | `"2"` |
| `type` | Column type | `"NEWSPAPER"` |
| `layout` | Layout direction | `"LEFT"` |
| `sameSz` | Equal width | `"1"` (true) |
| `sameGap` | Gap in HWPUNIT | `"850"` |

### eqEdit Structure (研究需要)
```xml
<hp:ctrl>
  <hp:eqEdit version="2" baseLine="X" textColor="#000000">
    <hp:script>LaTeX-like script here</hp:script>
  </hp:eqEdit>
</hp:ctrl>
```

---

## Conclusion

**Ready to Execute**: ❌ NO

Must implement proper OWPML control elements before regenerating HWPX files.
