# OWPML/HWPX Native Capabilities Reference

**Standard**: KS X 6101:2011 (OWPML - Open Word-Processor Markup Language)
**Sources**: 
- Hancom official specification PDFs
- `Skeleton.hwpx` reference file
- `hancom-io/hwpx-owpml-model` GitHub

---

## 1. Document Structure Overview

```
hwpx_file.hwpx (ZIP Archive)
├── mimetype                    # "application/hwp+zip"
├── META-INF/
│   └── container.xml          # Points to content.hpf
├── Contents/
│   ├── content.hpf            # OPF manifest (metadata, spine)
│   ├── header.xml             # Styles: charPr, paraPr, borderFill
│   ├── section0.xml           # Body content
│   └── section1.xml, ...      # Additional sections
├── BinData/                    # Images, OLE objects
└── settings.xml, version.xml   # Config files
```

---

## 2. XML Namespaces

| Prefix | URI | Description |
|--------|-----|-------------|
| `hp` | `http://www.hancom.co.kr/hwpml/2011/paragraph` | Paragraph elements |
| `hs` | `http://www.hancom.co.kr/hwpml/2011/section` | Section elements |
| `hh` | `http://www.hancom.co.kr/hwpml/2011/head` | Header/styles |
| `hc` | `http://www.hancom.co.kr/hwpml/2011/core` | Core elements |

---

## 3. Multi-Column Layout (colPr)

### Location
```
<hp:p> (first paragraph)
  └── <hp:run>
       ├── <hp:secPr> ... </hp:secPr>  ← Section properties
       └── <hp:ctrl>
            └── <hp:colPr ... />       ← Column definition HERE
           </hp:ctrl>
```

### Complete colPr Element
```xml
<hp:ctrl>
  <hp:colPr 
    id=""
    type="NEWSPAPER"        <!-- NEWSPAPER|BALANCED|PARALLEL -->
    layout="LEFT"           <!-- LEFT|RIGHT|MIRROR -->
    colCount="2"            <!-- Number of columns -->
    sameSz="1"              <!-- Equal width: 1=true, 0=false -->
    sameGap="850"           <!-- Gap in HWPUNIT (1mm ≈ 283 HWPUNIT) -->
  />
</hp:ctrl>
```

### Column Break
```xml
<hp:p columnBreak="1" ...>  <!-- Forces column break -->
```

---

## 4. Equation (수식)

### HWP Equation Script Syntax (NOT LaTeX!)

| HWP Script | Rendering | LaTeX Equivalent |
|------------|-----------|------------------|
| `a OVER b` | a/b (분수) | `\frac{a}{b}` |
| `a^2` or `a SUP 2` | a² | `a^2` |
| `a_n` or `a SUB n` | aₙ | `a_n` |
| `SQRT{x}` | √x | `\sqrt{x}` |
| `^3SQRT{x}` | ³√x | `\sqrt[3]{x}` |
| `SUM_{n=1}^N` | Σ | `\sum_{n=1}^{N}` |
| `INT_a^b` | ∫ | `\int_a^b` |
| `LEFT( ... RIGHT)` | 자동크기 괄호 | `\left( \right)` |
| `MATRIX{a&b#c&d}` | 행렬 | `\begin{matrix}` |
| `lim_{x->0}` | 극한 | `\lim_{x \to 0}` |

### Equation XML Structure
```xml
<hp:ctrl>
  <hp:eqEdit 
    version="2" 
    baseLine="BOTTOM"
    textColor="#000000"
    baseUnit="PUNKT">
    <hp:script>x^{2}+y^{2}=r^{2}</hp:script>
  </hp:eqEdit>
</hp:ctrl>
```

> **Note**: `<hp:script>` content uses HWP equation syntax, not LaTeX!

### LaTeX to HWP Script Conversion Examples
| LaTeX | HWP Script |
|-------|------------|
| `\frac{a+b}{a-b}` | `{a+b} OVER {a-b}` |
| `\sqrt{x^2+1}` | `SQRT{x^2+1}` |
| `\sum_{n=1}^{N}` | `SUM_{n=1}^N` |
| `\int_0^3` | `INT_0^3` |
| `\lim_{x \to 0}` | `lim_{x->0}` |

---

## 5. Section Properties (secPr)

```xml
<hp:secPr 
  textDirection="HORIZONTAL"
  spaceColumns="1134"           <!-- Default column spacing -->
  tabStop="8000"
  outlineShapeIDRef="1"
  masterPageCnt="0">
  
  <hp:pagePr 
    landscape="WIDELY"          <!-- Page orientation -->
    width="59528"               <!-- A4 width in HWPUNIT -->
    height="84186"              <!-- A4 height -->
    gutterType="LEFT_ONLY">
    <hp:margin 
      left="8504" right="8504" 
      top="5668" bottom="4252"
      header="4252" footer="4252"/>
  </hp:pagePr>
  
  <hp:startNum page="0" equation="0"/>
  
</hp:secPr>
```

---

## 6. Paragraph Structure

```xml
<hp:p 
  id="123456"
  paraPrIDRef="0"        <!-- Reference to header.xml paraPr -->
  styleIDRef="0"         <!-- Reference to header.xml style -->
  pageBreak="0"          <!-- Force page break: 0|1 -->
  columnBreak="0"        <!-- Force column break: 0|1 -->
  merged="0">
  
  <hp:run charPrIDRef="0">  <!-- Character style reference -->
    <hp:t>Text content here</hp:t>
  </hp:run>
  
  <hp:linesegarray>
    <hp:lineseg textpos="0" vertpos="0" ... />
  </hp:linesegarray>
  
</hp:p>
```

---

## 7. Control Elements (hp:ctrl)

Controls are non-text objects embedded in runs:

| Control Type | XML Element | Description |
|--------------|-------------|-------------|
| Column | `<hp:colPr>` | Multi-column layout |
| Equation | `<hp:eqEdit>` | Math formula |
| Table | `<hp:tbl>` | Table |
| Image | `<hp:pic>` | Picture |
| Shape | `<hp:shapeObject>` | Drawing object |

### Control Structure Pattern
```xml
<hp:run>
  <hp:ctrl>
    <hp:colPr ... />   <!-- OR -->
    <hp:eqEdit>...</hp:eqEdit>  <!-- OR -->
    <hp:tbl>...</hp:tbl>
  </hp:ctrl>
</hp:run>
```

---

## 8. HWPUNIT Conversion

| Unit | HWPUNIT Value |
|------|---------------|
| 1 mm | ≈ 283 HWPUNIT |
| 1 inch | = 7200 HWPUNIT |
| 1 point | ≈ 100 HWPUNIT |
| A4 width | = 59528 HWPUNIT (210mm) |
| A4 height | = 84186 HWPUNIT (297mm) |

---

## 9. Implementation Checklist

### For Multi-Column
- [ ] Modify first paragraph's `<hp:run>` to include `<hp:ctrl><hp:colPr>`
- [ ] Set `colCount="N"` for N columns
- [ ] Set `sameGap` for column spacing
- [ ] Use `columnBreak="1"` on paragraph for breaks

### For Equations
- [ ] Create `<hp:ctrl><hp:eqEdit>` element
- [ ] Convert LaTeX to HWP script syntax
- [ ] Place inside `<hp:run>` where equation should appear

---

## 10. Reference Files

| File | Location |
|------|----------|
| HWP 5.0 Spec | `docs/HWP_5.0_Specification.pdf` |
| Equation Spec | `docs/HWP_Equation_Specification.pdf` |
| Reference HWPX | `Skeleton.hwpx` |
