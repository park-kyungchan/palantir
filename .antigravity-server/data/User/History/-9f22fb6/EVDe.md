# HWPX Action Inventory (Ontology v1.5)

This document provides a comprehensive list of all 27 `HwpAction` models currently implemented in `lib/models.py`. These actions serve as the "Ontology" that the `Compiler` generates and the `HwpxDocumentBuilder` consumes.

## 1. Text & Formatting Actions
| Action | Description | Parameters |
|:---|:---|:---|
| `InsertText` | Standard text insertion. | `text` |
| `InsertCodeBlock` | Code block with optional language. | `text`, `language` |
| `InsertCaption` | Figure/Table caption. | `text` |
| `SetFontSize` | Set font size in pt. | `size` |
| `SetFontBold` | Toggle bold property. | `is_bold` |
| `SetAlign` | Paragraph alignment. | `align_type` (Left, Center, Right, Justify) |
| `SetLetterSpacing` | Ja-gan percentage. | `spacing` (-50 to 50) |
| `SetLineSpacing` | Jul-gan percentage. | `spacing` (e.g., 160) |
| `SetParaShape` | Margins and indents. | `left_margin`, `right_margin`, `indent`, `line_spacing` |

## 2. Table & Grid Actions
| Action | Description | Parameters |
|:---|:---|:---|
| `CreateTable` | Initialize table structure. | `rows`, `cols`, `width_type`, `height_type` |
| `MoveToCell` | Move cursor to cell (0-based). | `row`, `col` |
| `SetCellBorder` | Set border/fill for current cell. | `border_type`, `width`, `color`, `fill_color` |
| `MergeCells` | Merge block of cells. | `start_row`, `start_col`, `row_span`, `col_span` |

## 3. Layout & Section Actions
| Action | Description | Parameters |
|:---|:---|:---|
| `SetPageSetup` | Margins and Orientation. | `paper_size` (A4, etc.), `orientation`, `left`, `right`, `top`, `bottom` |
| `MultiColumn` | Set column layout. | `count`, `same_size`, `gap` |
| `BreakColumn` | Force column break. | - |
| `BreakSection` | Force section break. | `continuous` (bool) |
| `BreakPara` | Insert paragraph break. | - |
| `SetNumbering` | List/Bullet style. | `numbering_type` (None, Number, Bullet) |

## 4. Object & Media Actions
| Action | Description | Parameters |
|:---|:---|:---|
| `InsertImage` | Insert picture (char-treated). | `path`, `width`, `height`, `treat_as_char` |
| `InsertTextBox` | Floating or inline text box. | `text`, `width`, `height`, `x`, `y` |
| `InsertEquation` | Math formula (LaTeX/EQ). | `script` |
| `CreateBorderBox` | Wrapped border container. | `border_type`, `border_width`, `border_color` |

## 5. Metadata & Reference Actions
| Action | Description | Parameters |
|:---|:---|:---|
| `InsertFootnote` | Add inline footnote. | `text` |
| `InsertEndnote` | Add inline endnote. | `text` |
| `MoveToField` | Target named field (ClickHere). | `field`, `text` |

## 6. System & I/O Actions
| Action | Description | Parameters |
|:---|:---|:---|
| `Open` | Open existing document. | `path`, `format` |
| `FileSaveAs` | Save/Export document. | `path`, `format` (HWP, HWPX, PDF) |

---
**Reference**: Defined in `/home/palantir/hwpx/lib/models.py`.
