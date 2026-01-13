# HWPX Pipeline Corrective Implementation Plan

## Background: Audit Findings

**Root Cause**: Previous implementation used WRONG XML structures:
- ❌ `columnBreak="1"` on paragraph (does NOT create multi-column)
- ❌ Text placeholder `[수식: ...]` (does NOT render equations)

**Correct Approach** (from KS X 6101 / Hancom specs):
- ✅ `<hp:ctrl><hp:colPr colCount="2"/>` inside first paragraph's run
- ✅ `<hp:ctrl><hp:eqEdit><hp:script>` with HWP equation syntax

---

## Proposed Changes

### Phase 1: Fix Multi-Column (colPr)

#### [MODIFY] `lib/owpml/document_builder.py`

**Current (WRONG)**:
```python
def _insert_column_break(self):
    p = ET.SubElement(..., {'columnBreak': '1'})  # ← Wrong!
```

**Corrected**:
```python
def _set_column_layout(self, col_count: int, gap_hwpunit: int = 850):
    """Modify first paragraph to include colPr control."""
    # Find first paragraph's first run
    first_para = self.section_elem.find(f'.//{_hp("p")}')
    first_run = first_para.find(f'.//{_hp("run")}')
    
    # Find secPr and insert colPr ctrl after it
    sec_pr = first_run.find(_hp("secPr"))
    
    # Create ctrl with colPr
    ctrl = ET.Element(_hp('ctrl'))
    col_pr = ET.SubElement(ctrl, _hp('colPr'), {
        'id': '',
        'type': 'NEWSPAPER',
        'layout': 'LEFT',
        'colCount': str(col_count),
        'sameSz': '1',
        'sameGap': str(gap_hwpunit)
    })
    
    # Insert ctrl after secPr
    idx = list(first_run).index(sec_pr)
    first_run.insert(idx + 1, ctrl)
```

---

### Phase 2: Implement Equation (eqEdit)

#### [NEW] `lib/owpml/equation_converter.py`

**Purpose**: Convert LaTeX to HWP equation script

| LaTeX | HWP Script |
|-------|------------|
| `\frac{a}{b}` | `{a} OVER {b}` |
| `\sqrt{x}` | `SQRT{x}` |
| `\sum_{i}^{n}` | `SUM_{i}^{n}` |
| `\int_a^b` | `INT_a^b` |

#### [MODIFY] `lib/owpml/document_builder.py`

**Add eqEdit insertion**:
```python
def _insert_equation(self, hwp_script: str):
    """Insert equation control element."""
    run = ET.SubElement(current_para, _hp('run'), {'charPrIDRef': '0'})
    ctrl = ET.SubElement(run, _hp('ctrl'))
    eq_edit = ET.SubElement(ctrl, _hp('eqEdit'), {
        'version': '2',
        'baseLine': 'BOTTOM',
        'textColor': '#000000',
        'baseUnit': 'PUNKT'
    })
    script = ET.SubElement(eq_edit, _hp('script'))
    script.text = hwp_script
```

---

### Phase 3: Update Action Processing

#### [MODIFY] `lib/owpml/document_builder.py`

```python
def _process_action(self, action: HwpAction):
    if isinstance(action, MultiColumn):
        self._set_column_layout(action.count, action.gap)
        
    elif isinstance(action, BreakColumn):
        self._insert_column_break_paragraph()  # Set columnBreak="1" on next para
        
    elif isinstance(action, InsertEquation):
        hwp_script = latex_to_hwp(action.script)  # Convert LaTeX → HWP
        self._insert_equation(hwp_script)
```

---

## Verification Plan

### Automated Tests
1. Generate `test_2column.hwpx` with `colCount="2"` and `columnBreak`
2. Generate `test_equation.hwpx` with `<hp:eqEdit>` elements
3. Validate XML structure against Skeleton.hwpx

### Manual Verification
1. Open generated files in HWP 2024
2. Verify 2-column layout renders correctly
3. Verify equations render correctly

---

## Files to Modify

| Action | Path | Description |
|--------|------|-------------|
| MODIFY | `lib/owpml/document_builder.py` | Fix colPr and eqEdit |
| NEW | `lib/owpml/equation_converter.py` | LaTeX → HWP script |
| MODIFY | `lib/models.py` | Ensure BreakColumn, MultiColumn models |
| UPDATE | `docs/OWPML_NATIVE_CAPABILITIES.md` | Reference doc |

---

## Quality Gate

- [ ] colPr element in correct location (first para → run → after secPr)
- [ ] eqEdit element with hp:script child
- [ ] HWP 2024 opens file without crash
- [ ] 2-column layout visible
- [ ] Equations render correctly
