# Korean Math/Science PDF Generation Feasibility Report

**Date:** 2026-02-09
**Scope:** Korean-language mathematical and scientific document PDF generation
**Status:** Research Complete

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Korean LaTeX Packages (kotex / ko.TeX)](#2-korean-latex-packages)
3. [Python Libraries for LaTeX PDF Generation](#3-python-libraries)
4. [Mathpix Markdown (MMD) to PDF Pipeline](#4-mathpix-mmd-to-pdf)
5. [Alternative Approaches](#5-alternative-approaches)
6. [Diagram and Chart Handling](#6-diagram-and-chart-handling)
7. [Korean Education Sector Workflow](#7-korean-education-sector)
8. [Comparative Analysis Matrix](#8-comparative-analysis)
9. [Recommended Approaches](#9-recommendations)
10. [Sources](#10-sources)

---

## 1. Executive Summary

Generating high-quality Korean math/science PDFs is a well-solved problem with multiple
viable approaches. The Korean TeX ecosystem (kotex) is mature and actively maintained.
The key decision axis is: **offline/self-hosted vs. API-dependent** and
**TeX-based vs. HTML-based rendering**.

**Top 3 recommended approaches (ranked):**

| Rank | Approach | Best For | Korean + Math Quality |
|------|----------|----------|----------------------|
| 1 | Pandoc + XeLaTeX + kotex | Robust offline generation | Excellent |
| 2 | HTML + MathJax + Puppeteer | No TeX dependency, web-first | Very Good |
| 3 | Mathpix API (MMD to PDF) | Cloud-native, rapid prototyping | Very Good |

**Key insight:** For Korean math exam papers specifically, the combination of
XeLaTeX + kotex + Nanum/Noto CJK fonts is the gold standard. This mirrors what
the Korean academic community has used for decades.

---

## 2. Korean LaTeX Packages

### 2.1 kotex (ko.TeX) Ecosystem

kotex is the comprehensive Korean typesetting system for LaTeX, officially sponsored
by the Korean TeX Society (KTS). It includes:

| Package | Engine | Purpose |
|---------|--------|---------|
| `kotex-utf` | pdfLaTeX | UTF-8 Korean with pdfLaTeX (legacy) |
| `xetexko` | XeLaTeX | Korean typesetting with XeTeX |
| `luatexko` | LuaLaTeX | Korean typesetting with LuaTeX |
| `cjk-ko` | pdfLaTeX | CJK support via kotex interface |
| `kotex-oblivoir` | All | Korean document class (oblivoir) |
| `kotex-plain` | All | Plain TeX Korean support |
| `kotex-utils` | All | Utility macros |

**Status (2025-2026):** Actively maintained. All packages available on CTAN and
included in TeX Live distributions. The `\usepackage{kotex}` command auto-detects
the engine and loads the appropriate backend (xetexko for XeLaTeX, luatexko for LuaLaTeX).

### 2.2 XeLaTeX vs LuaLaTeX for Korean

| Criterion | XeLaTeX + xetexko | LuaLaTeX + luatexko |
|-----------|-------------------|---------------------|
| **Maturity** | Very mature, widely used | Mature, growing adoption |
| **Speed** | Fast for typical documents | Slower first compile, faster incremental |
| **Font Access** | System fonts via fontspec | System fonts via fontspec |
| **Korean Spacing** | Excellent (native hangul breaks) | Excellent (Lua-scripted fine control) |
| **Scripting** | None | Lua scripting for custom typography |
| **CJK Punctuation** | Good | Better (customizable via Lua callbacks) |
| **Ecosystem Compat** | Broad package compatibility | Some packages incompatible |
| **Recommendation** | **Primary choice** for Korean | Advanced use cases |

**Verdict:** XeLaTeX is the recommended default for Korean math documents. LuaLaTeX
is worth considering only when Lua-based customization is required.

### 2.3 Font Support

**Freely available Korean fonts for LaTeX:**

| Font Family | Style | Source | Notes |
|-------------|-------|--------|-------|
| Nanum Myeongjo (나눔명조) | Serif | Naver/Sandoll | Most popular for body text |
| Nanum Gothic (나눔고딕) | Sans-serif | Naver/Sandoll | Popular for headings |
| Nanum Pen Script (나눔손글씨) | Handwriting | Naver/Sandoll | Informal documents |
| Noto Serif CJK KR | Serif | Google/Adobe | Excellent coverage, free |
| Noto Sans CJK KR | Sans-serif | Google/Adobe | Excellent coverage, free |
| Noto Sans Mono CJK KR | Monospace | Google/Adobe | Code listings |
| Un fonts (은글꼴) | Various | KLDP | Traditional, widely available |
| Malgun Gothic (맑은 고딕) | Sans-serif | Microsoft | Windows systems only |

**Recommended minimal setup:**
```latex
\documentclass{article}
\usepackage{xeCJK}
\usepackage{amsmath, amssymb}

\setCJKmainfont{Noto Serif CJK KR}
\setCJKsansfont{Noto Sans CJK KR}
\setCJKmonofont{Noto Sans Mono CJK KR}

\begin{document}
다음 방정식을 풀어라.
\begin{equation}
  \int_0^{\pi} \sin^2 x \, dx = \frac{\pi}{2}
\end{equation}
\end{document}
```

Compile with: `xelatex document.tex`

### 2.4 Installation

```bash
# Ubuntu/Debian — full Korean TeX support
sudo apt-get install texlive-xetex texlive-lang-korean texlive-fonts-recommended

# Noto CJK fonts
sudo apt-get install fonts-noto-cjk fonts-noto-cjk-extra

# Nanum fonts
sudo apt-get install fonts-nanum fonts-nanum-extra

# Or via tlmgr (TeX Live Manager)
tlmgr install kotex-plain kotex-utf kotex-oblivoir xetexko luatexko cjk-ko
```

---

## 3. Python Libraries for LaTeX PDF Generation

### 3.1 PyLaTeX

**Repository:** https://github.com/JelteF/PyLaTeX
**Version:** 1.4.2 (latest)
**Korean Support:** Indirect — requires manual preamble configuration

PyLaTeX generates LaTeX source files programmatically. It does NOT compile them to PDF
itself; it requires a LaTeX engine on the system.

**Korean integration approach:**
```python
from pylatex import Document, Package, Command, NoEscape, Math
from pylatex.utils import italic

doc = Document(documentclass='article')

# Add Korean support packages
doc.preamble.append(Package('xeCJK'))
doc.preamble.append(Package('amsmath'))
doc.preamble.append(NoEscape(r'\setCJKmainfont{Noto Serif CJK KR}'))

# Add content
doc.append(NoEscape(r'다음 방정식을 풀어라.'))
doc.append(Math(data=[NoEscape(r'\int_0^{\pi} \sin^2 x \, dx = \frac{\pi}{2}')]))

# Compile with XeLaTeX
doc.generate_pdf('output', compiler='xelatex', clean_tex=False)
```

**Pros:**
- Pythonic API for building LaTeX documents
- Supports math, tables, figures, TikZ
- UTF-8 support (resolved since 2015, issue #55)

**Cons:**
- No built-in Korean/CJK awareness
- Requires XeLaTeX installed on system
- Last major update was some time ago; maintenance is minimal
- Must manually add all Korean-related preamble commands

### 3.2 fpdf2

**Repository:** https://github.com/py-pdf/fpdf2
**Version:** 2.8.5 (Oct 2025)
**Korean Support:** Direct — via Unicode font embedding

```python
from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_text_shaping(True)  # Required for Korean

# Add Korean font
pdf.add_font(fname='/usr/share/fonts/truetype/nanum/NanumMyeongjo.ttf')
pdf.set_font('NanumMyeongjo', size=14)

# Write Korean text
pdf.cell(text='다음 방정식을 풀어라.')

# For math: fpdf2 has NO native LaTeX math rendering
# Workaround: render math as image and embed
pdf.image('equation.png', x=10, y=40, w=100)

pdf.output('output.pdf')
```

**Pros:**
- Pure Python, no external dependencies for basic PDF
- Excellent Unicode/CJK support with font fallback
- Font subsetting (small file sizes)
- Active development (v2.8.5 Oct 2025)

**Cons:**
- **NO native LaTeX math rendering** — critical limitation for math documents
- Math must be pre-rendered as images (PNG/SVG) and embedded
- No document structure features (table of contents, cross-references)

### 3.3 WeasyPrint

**Repository:** https://github.com/Kozea/WeasyPrint
**Version:** 68.x (2025)
**Korean Support:** Via system fonts, but with performance issues

**Pros:**
- HTML/CSS to PDF — leverages web standards
- Korean text works with proper fonts installed

**Cons:**
- **NO native math equation support** (issue #59, open since 2013)
- Slow performance with CJK fonts (issue #2120)
- Korean text has been reported as blank in some configurations
- Not suitable for math/science documents without pre-rendered math

### 3.4 ReportLab

**Version:** 4.4.9
**Korean Support:** Built-in Asian font support

```python
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

pdfmetrics.registerFont(UnicodeCIDFont('HYSMyeongJoStd-Medium'))

c = canvas.Canvas('output.pdf', pagesize=A4)
c.setFont('HYSMyeongJoStd-Medium', 12)
c.drawString(72, 720, '다음 방정식을 풀어라.')
c.save()
```

**Pros:**
- Built-in Korean font support (HYSMyeongJoStd-Medium, HYGothic-Medium)
- Commercial-grade PDF library
- Good for charts and graphs

**Cons:**
- **NO native LaTeX math rendering**
- Low-level API (manual positioning)
- Commercial license for advanced features
- Asian CID fonts depend on Acrobat Reader font packs

### 3.5 Comparison Matrix

| Library | Korean Text | Math Equations | Diagrams | Ease of Use | Maintenance |
|---------|------------|---------------|----------|-------------|-------------|
| PyLaTeX + XeLaTeX | Via kotex | Native LaTeX | TikZ | Medium | Low |
| fpdf2 | Native Unicode | Images only | Images only | Easy | Active |
| WeasyPrint | Via fonts | Not supported | CSS/images | Easy | Active |
| ReportLab | CID fonts | Not supported | Canvas API | Medium | Active |

**Verdict for Korean math documents:** PyLaTeX + XeLaTeX is the only Python library
that provides native LaTeX math rendering alongside Korean text support. All others
require math to be pre-rendered as images.

### 3.6 Direct Subprocess Approach (Recommended for Automation)

The most flexible Python approach for Korean math PDFs is to generate `.tex` files
directly (via string templates or Jinja2) and compile with XeLaTeX:

```python
import subprocess
import tempfile
import os

TEMPLATE = r"""
\documentclass[12pt]{article}
\usepackage{xeCJK}
\usepackage{amsmath, amssymb, amsthm}
\setCJKmainfont{Noto Serif CJK KR}

\begin{document}
%(content)s
\end{document}
"""

def generate_korean_math_pdf(content: str, output_path: str) -> str:
    """Generate a Korean math PDF from LaTeX content."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tex_path = os.path.join(tmpdir, 'document.tex')
        with open(tex_path, 'w', encoding='utf-8') as f:
            f.write(TEMPLATE % {'content': content})

        result = subprocess.run(
            ['xelatex', '-interaction=nonstopmode', '-output-directory', tmpdir, tex_path],
            capture_output=True, text=True, timeout=60
        )

        if result.returncode != 0:
            raise RuntimeError(f"XeLaTeX compilation failed:\n{result.stderr}")

        pdf_path = os.path.join(tmpdir, 'document.pdf')
        os.rename(pdf_path, output_path)

    return output_path
```

---

## 4. Mathpix Markdown (MMD) to PDF Pipeline

### 4.1 Overview

Mathpix provides a cloud API for converting Mathpix Markdown (MMD) to PDF.
MMD extends standard Markdown with LaTeX math notation, tables, and other
STEM-specific features.

### 4.2 API Endpoint

```
POST https://api.mathpix.com/v3/converter
```

**Request body:**
```json
{
  "mmd": "# Korean Math Example\n\n다음 방정식을 풀어라.\n\n$$\\int_0^{\\pi} \\sin^2 x \\, dx$$",
  "formats": {"pdf": true}
}
```

**Response:** Returns a PDF file URL for download.

### 4.3 Korean Language Support

- Korean (Hangeul) is explicitly listed as a supported language
- When Korean text is detected, the backend automatically switches to **XeLaTeX** compilation
- Supports mixed Korean text + LaTeX math notation
- MathJax rendering for web preview; XeLaTeX for PDF output

### 4.4 Pricing

| Volume | Per Page Cost |
|--------|--------------|
| 0-1M pages | $0.005 |
| 1M+ pages | $0.0035 |
| Enterprise | Custom pricing |

No free tier for the Convert API. A $29 credit is provided for testing.
The free Snip app can be used for testing capabilities.

### 4.5 Pros and Cons

**Pros:**
- Handles Korean + math seamlessly (auto XeLaTeX for CJK)
- No local TeX installation required
- Consistent output quality
- Python SDK available (`mpxpy`)
- CLI tool available (`mpx convert input.mmd output.pdf`)

**Cons:**
- API-dependent (no offline mode)
- Cost per page (adds up for high volume)
- Limited control over PDF layout/styling
- Latency for API calls
- Proprietary service (vendor lock-in risk)

### 4.6 Workflow

```
MMD (Markdown + LaTeX math)
  |
  v
Mathpix API (/v3/converter)
  |--- detects Korean text
  |--- selects XeLaTeX engine
  |--- compiles with CJK fonts
  v
PDF output (download URL)
```

---

## 5. Alternative Approaches

### 5.1 HTML + MathJax + Puppeteer/Playwright

This approach renders math in a browser and captures the result as PDF.

**Architecture:**
```
HTML template (Korean text + LaTeX math in $...$ delimiters)
  |
  v
MathJax 4.0 renders math to SVG/CHTML
  |
  v
Puppeteer/Playwright captures page as PDF
  |
  v
PDF output
```

**Implementation example (Node.js):**
```javascript
const puppeteer = require('puppeteer');

const html = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body { font-family: 'Noto Serif CJK KR', serif; font-size: 14pt; }
    .math { font-size: 16pt; }
  </style>
  <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>
</head>
<body>
  <p>다음 방정식을 풀어라.</p>
  <p>$$\\int_0^{\\pi} \\sin^2 x \\, dx = \\frac{\\pi}{2}$$</p>
</body>
</html>`;

const browser = await puppeteer.launch();
const page = await browser.newPage();
await page.setContent(html, { waitUntil: 'networkidle0' });
await page.pdf({ path: 'output.pdf', format: 'A4' });
await browser.close();
```

**Pros:**
- No TeX installation required
- MathJax has explicit Korean language support (speech, accessibility)
- CSS-based styling (familiar to web developers)
- MathJax 4.0 (Dec 2025) has excellent rendering quality
- Can run in Docker containers easily

**Cons:**
- Requires Chromium/headless browser dependency
- Slightly less precise math typesetting than native LaTeX
- Font rendering depends on browser engine
- PDF page breaks less controllable than LaTeX
- Larger dependency footprint (Chromium ~300MB)

**Python variant using Playwright:**
```python
from playwright.sync_api import sync_playwright

def html_to_pdf(html_content: str, output_path: str):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html_content, wait_until='networkidle')
        page.pdf(path=output_path, format='A4')
        browser.close()
```

### 5.2 Typst

**Status:** Emerging alternative to LaTeX. Version 0.13 (Feb 2025).

**Korean support:**
```typst
#set text(font: ("New Computer Modern", "Noto Serif CJK KR"), size: 12pt)
#set page(paper: "a4")

다음 방정식을 풀어라.

$ integral_0^pi sin^2 x dif x = pi / 2 $
```

Compile with: `typst compile document.typ output.pdf`

**CJK status (as of Typst 0.13):**
- Basic CJK line-breaking: Works
- Font fallback (Latin + CJK): Works
- CJK-Latin spacing: Improved in 0.13
- First paragraph indentation: Added in 0.13
- Punctuation compression: Not yet implemented
- Vertical text layout: Not supported
- Ruby annotations: Community packages only

**Pros:**
- Extremely fast compilation (10-100x faster than LaTeX)
- Simple, modern syntax
- Incremental compilation
- Math rendering quality approaching LaTeX
- Built-in scripting (no separate package system for logic)
- Active development, rapidly improving

**Cons:**
- CJK support still incomplete (GitHub issue #276 remains open)
- No equivalent to kotex's sophisticated Korean typography
- Smaller ecosystem than LaTeX (fewer templates, packages)
- No Korean-specific exam templates yet
- Breaking changes between versions

**Verdict:** Monitor Typst for future adoption. Not yet recommended for
production Korean math documents where typography quality matters.

### 5.3 Pandoc

Pandoc serves as a universal document converter, including Markdown to PDF via LaTeX.

**Korean math PDF via Pandoc:**
```bash
pandoc document.md \
  --pdf-engine=xelatex \
  -V mainfont="Noto Serif CJK KR" \
  -V mathfont="STIX Two Math" \
  -V CJKmainfont="Noto Serif CJK KR" \
  -V geometry:margin=2.5cm \
  --highlight-style=tango \
  -o output.pdf
```

**Or with a YAML header in the Markdown file:**
```yaml
---
title: "수학 시험지"
author: "교사 이름"
date: "2026-02-09"
mainfont: "Noto Serif CJK KR"
CJKmainfont: "Noto Serif CJK KR"
mathfont: "STIX Two Math"
geometry: margin=2.5cm
output:
  pdf_document:
    latex_engine: xelatex
---
```

**Pros:**
- Markdown input (simpler than raw LaTeX)
- Well-tested Korean support path via XeLaTeX
- Extensive format conversion (MD, HTML, DOCX, LaTeX, PDF)
- Can include raw LaTeX blocks in Markdown for complex math
- Active development, large community

**Cons:**
- Still requires XeLaTeX for PDF output
- Less control over layout than raw LaTeX
- Complex documents may hit Pandoc template limitations
- Lua filters needed for advanced customization

---

## 6. Diagram and Chart Handling

### 6.1 TikZ (Native LaTeX)

TikZ is the standard for mathematical diagrams in LaTeX documents.

**Example — coordinate plane with Korean labels:**
```latex
\begin{tikzpicture}
  \draw[->] (-3,0) -- (3,0) node[right] {$x$축};
  \draw[->] (0,-2) -- (0,3) node[above] {$y$축};
  \draw[domain=-2:2, smooth, thick, blue] plot (\x, {\x*\x});
  \node at (1.5, 2.5) {$y = x^2$};
  \node[below] at (0, -2.5) {이차함수의 그래프};
\end{tikzpicture}
```

**Pros:** Vector graphics, native LaTeX integration, Korean text in labels
**Cons:** Verbose syntax, steep learning curve

### 6.2 SVG/PNG Embedding

```latex
\usepackage{graphicx}

% PNG embedding
\includegraphics[width=0.8\textwidth]{diagram.png}

% SVG embedding (requires svg package + Inkscape)
\usepackage{svg}
\includesvg[width=0.8\textwidth]{diagram.svg}
```

**For the HTML+MathJax approach:**
```html
<img src="diagram.svg" alt="수학 다이어그램" style="width: 80%;" />
```

### 6.3 Matplotlib Charts with Korean

```python
import matplotlib.pyplot as plt
import matplotlib
import numpy as np

# Korean font setup
matplotlib.rcParams['font.family'] = 'Nanum Gothic'
matplotlib.rcParams['axes.unicode_minus'] = False  # Fix minus sign

x = np.linspace(0, 2*np.pi, 100)
y = np.sin(x)

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(x, y, 'b-', linewidth=2)
ax.set_xlabel('각도 (라디안)')
ax.set_ylabel('사인 값')
ax.set_title('사인 함수 그래프')
ax.grid(True)

# Save as PNG for embedding in LaTeX/HTML
fig.savefig('sin_graph.png', dpi=300, bbox_inches='tight')
# Or as SVG for vector quality
fig.savefig('sin_graph.svg', bbox_inches='tight')
```

**Korean font setup for different platforms:**
| Platform | Font | Setup |
|----------|------|-------|
| Linux | Nanum Gothic | `sudo apt install fonts-nanum` |
| macOS | AppleGothic | Pre-installed |
| Windows | Malgun Gothic | Pre-installed |
| Google Colab | Nanum Gothic | `!apt install fonts-nanum && rm ~/.cache/matplotlib -rf` |

### 6.4 Diagram Approach Comparison

| Method | Vector | Korean Labels | LaTeX Integration | HTML Integration |
|--------|--------|--------------|-------------------|-----------------|
| TikZ | Yes | Yes (native) | Native | Via conversion |
| SVG embed | Yes | Yes | Via svg package | Native |
| PNG embed | No | Yes | Via graphicx | Native |
| Matplotlib | Both | Yes (with font) | Export to file | Export to file |
| draw.io | Yes | Yes | Export SVG/PNG | Export SVG/PNG |

---

## 7. Korean Education Sector Workflow

### 7.1 Current State of Korean Math Content Creation

**Dominant tool: HWP (한글)**
- 99% of Korean learning centers create test content in HWP format
- HWP is developed by Hancom (한컴오피스)
- Built-in Korean equation editor (non-LaTeX format)
- Export to PDF is built-in
- HWP format (.hwp, .hwpx) is proprietary but widely used

**Why HWP dominates:**
- Pre-installed on Korean government and education computers
- Familiar to all Korean educators
- Built-in Korean formatting and spacing
- Government document standard

### 7.2 HWP to LaTeX Conversion

**Bapul HML Equation Parser (open source, 2016+):**
- Converts HWP equations to LaTeX
- Originally developed by the edtech startup Bapul
- Key motivation: HWP equations are images; LaTeX makes them searchable text
- Published as open source on GitHub

**Conversion workflow:**
```
HWP document → HML (XML export) → Parse equations → LaTeX output
```

### 7.3 Korean Math Education Platforms

| Platform | Features | Output Format |
|----------|----------|---------------|
| MathForAll (매쓰포올) | Free elementary math worksheets | PDF |
| Matholic (매쓰홀릭) | Problem bank, textbook-aligned | HWP/PDF |
| MathPro (매쓰프로) | Custom test paper creation | HWP/PDF |
| FlowMath (플로우수학) | Interactive math platform | Web/PDF |
| TocTocMath (톡톡수학) | Math learning platform | Web |
| EduHub (에듀허브) | Math OCR + auto HWP conversion | HWP |

### 7.4 Implications for Automated PDF Generation

1. **Input format consideration:** Content may arrive in HWP format.
   An HWP-to-LaTeX or HWP-to-Markdown conversion step may be needed.
2. **Layout expectations:** Korean exam papers follow specific formatting
   conventions (header with school name, grade, exam period; two-column
   for multiple choice; specific numbering styles).
3. **Font expectations:** Educators expect specific fonts — typically
   HY family fonts (HY신명조, HY중고딕) or Nanum family.
4. **Math notation:** Korean math uses the same LaTeX notation as
   international standards, but some conventions differ:
   - Function notation: $f(x)$ (same)
   - Set notation: sometimes uses Korean letters for set names
   - Geometry: angle notation may use Korean characters

---

## 8. Comparative Analysis Matrix

### 8.1 Full Comparison

| Criterion | XeLaTeX + kotex | Pandoc + XeLaTeX | HTML + MathJax | Mathpix API | Typst | fpdf2 |
|-----------|----------------|-----------------|----------------|-------------|-------|-------|
| **Korean text** | Excellent | Excellent | Very Good | Very Good | Good | Good |
| **Math quality** | Excellent | Excellent | Very Good | Very Good | Good+ | None |
| **Offline** | Yes | Yes | Yes | No | Yes | Yes |
| **Speed** | Medium | Medium | Fast | Slow (API) | Very Fast | Fast |
| **Dependencies** | TeX Live (~4GB) | TeX Live + Pandoc | Chromium (~300MB) | API key only | Typst binary (~30MB) | None |
| **Automation** | subprocess | subprocess | Playwright | HTTP API | subprocess | Native Python |
| **Diagrams** | TikZ (native) | TikZ + images | HTML/SVG | Images only | Typst graphics | Images only |
| **Exam templates** | Many available | Via LaTeX | Custom CSS | Limited | Few | Manual |
| **Learning curve** | High | Medium | Low-Medium | Low | Medium | Low |
| **Cost** | Free | Free | Free | $0.005/page | Free | Free |
| **Maturity** | 30+ years | 15+ years | 15+ years | 5+ years | 3 years | 10+ years |

### 8.2 Decision Matrix by Use Case

| Use Case | Recommended Approach | Rationale |
|----------|---------------------|-----------|
| **High-quality exam papers** | XeLaTeX + kotex | Best typography, established templates |
| **Automated batch generation** | Python + XeLaTeX subprocess | Flexible, scriptable |
| **Web-first workflow** | HTML + MathJax + Playwright | No TeX dependency, CSS styling |
| **Cloud/serverless** | Mathpix API | No local dependencies |
| **Simple worksheets** | Pandoc + XeLaTeX | Markdown input, quick setup |
| **Future-proof prototyping** | Typst | Fast iteration, modern syntax |
| **Charts/data viz + Korean** | Matplotlib + fpdf2 | Pure Python, data-focused |

---

## 9. Recommended Approaches

### 9.1 Primary Recommendation: Pandoc + XeLaTeX + kotex

**Why:** Best balance of quality, automation, and simplicity.

**Setup:**
```bash
# Install dependencies
sudo apt-get install texlive-xetex texlive-lang-korean pandoc
sudo apt-get install fonts-noto-cjk fonts-nanum
```

**Workflow:**
```
Markdown (with LaTeX math) → Pandoc → XeLaTeX → PDF
```

**Ideal for:** Batch generation of Korean math documents from structured data
(e.g., question banks stored as Markdown/JSON).

### 9.2 Secondary Recommendation: HTML + MathJax + Playwright

**Why:** No TeX installation, web-native, good for modern stacks.

**Setup:**
```bash
pip install playwright
playwright install chromium
```

**Workflow:**
```
HTML template + data → MathJax rendering → Playwright PDF capture
```

**Ideal for:** Web applications, serverless environments, or when TeX
installation is impractical.

### 9.3 Tertiary Recommendation: Mathpix API

**Why:** Zero local dependencies, handles Korean + math automatically.

**Setup:**
```bash
pip install mpxpy
# Set MATHPIX_APP_ID and MATHPIX_APP_KEY
```

**Workflow:**
```
MMD content → Mathpix API → PDF download
```

**Ideal for:** Rapid prototyping, small volume, or when content already
exists in Mathpix Markdown format.

### 9.4 Implementation Priority for cow Project

Given the cow project already uses Mathpix APIs (as evidenced by the existing
`docs/mathpix_api_spec.md`, `docs/MATHPIX_API_CONSTRAINTS.md`, and
`docs/mathpix-api-reference/` files), the recommended implementation order is:

1. **Phase 1:** Mathpix MMD-to-PDF (leverages existing API integration)
2. **Phase 2:** Pandoc + XeLaTeX fallback (offline capability)
3. **Phase 3:** HTML + MathJax + Playwright (web preview/export)

---

## 10. Sources

### Korean LaTeX (kotex)
- [CTAN: kotex-utf](https://ctan.org/tex-archive/language/korean/kotex-utf?lang=en)
- [GitHub: kotex-utf](https://github.com/kihwanglee/kotex-utf)
- [GitHub: xetexko](https://github.com/dohyunkim/xetexko)
- [GitHub: luatexko](https://github.com/dohyunkim/luatexko)
- [Overleaf: Korean](https://www.overleaf.com/learn/latex/Korean)
- [ArchWiki: TeX Live/CJK](https://wiki.archlinux.org/title/TeX_Live/CJK)

### Python Libraries
- [PyLaTeX Documentation](https://jeltef.github.io/PyLaTeX/current/)
- [PyLaTeX GitHub](https://github.com/JelteF/PyLaTeX)
- [PyLaTeX Unicode Issue #55](https://github.com/JelteF/PyLaTeX/issues/55)
- [fpdf2 Unicode Documentation](https://py-pdf.github.io/fpdf2/Unicode.html)
- [fpdf2 PyPI](https://pypi.org/project/fpdf2/)
- [WeasyPrint Math Issue #59](https://github.com/Kozea/WeasyPrint/issues/59)
- [WeasyPrint CJK Performance Issue #2120](https://github.com/Kozea/WeasyPrint/issues/2120)
- [ReportLab Fonts Documentation](https://docs.reportlab.com/reportlab/userguide/ch3_fonts/)

### Mathpix
- [Mathpix API Reference](https://docs.mathpix.com/)
- [Mathpix MMD to PDF](https://mathpix.com/markdown-to-pdf)
- [Mathpix Supported Languages](https://mathpix.com/docs/convert/supported_languages)
- [Mathpix API Pricing](https://mathpix.com/pricing/api)
- [Mathpix Python SDK](https://mathpix.com/docs/mpxpy/markdown)

### Typst
- [Typst CJK Support Issue #276](https://github.com/typst/typst/issues/276)
- [Typst 0.13 Release Notes](https://typst.app/blog/2025/typst-0.13/)
- [Typst Math Documentation](https://typst.app/docs/reference/math/)
- [Typst vs LaTeX Comparison](https://advancedmath.org/LaTeX/LaTeX_vs_Typst.html)

### Alternative Tools
- [Pandoc User Guide](https://pandoc.org/MANUAL.html)
- [Pandoc LaTeX Template](https://github.com/Wandmalfarbe/pandoc-latex-template)
- [MathJax Documentation](https://docs.mathjax.org/)
- [Puppeteer + Math (puptex)](https://github.com/ambar/puptex)
- [svg2tikz](https://xyz2tex.github.io/svg2tikz/)

### Korean Education
- [MathForAll (매쓰포올)](https://mathforall.kr/intro/)
- [Matholic (매쓰홀릭)](https://www.matholic.com/)
- [MathPro (매쓰프로)](https://www.mathpro.co.kr/)
- [HWP Equation to LaTeX Converter (ZDNet Korea)](https://zdnet.co.kr/view/?no=20161229092520)
- [Korean LaTeX Hello World](https://statkclee.github.io/latex/latex-korean-helloworld.html)
- [Nanum Myeongjo (Google Fonts)](https://fonts.google.com/specimen/Nanum+Myeongjo)
