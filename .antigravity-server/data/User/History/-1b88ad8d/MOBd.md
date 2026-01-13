# Math Workbook Action Templates

To improve the efficiency and consistency of document reconstruction, particularly for math workbooks, a library of reusable action templates was established. These templates map high-level document concepts to sequences of `HwpAction` objects.

## 1. Core Templates

### 1.1 Problem Header (`problem_header`)
Maps a problem number to OWPML's hanging indent layout.
- **Visual Pattern**: Number is flush left, body is indented.
- **Logic**: 
  - `SetParaShape(left_margin=20, indent=-20)`
  - `InsertText(text="N. ")`

### 1.2 Two-Column Layout (`two_column_layout`)
Manages the transition into and out of multi-column flows.
- **Logic (Start)**: `MultiColumn(count=2, same_size=True, gap=850)`
- **Logic (Break)**: `BreakColumn` (raw action)
- **Logic (End)**: `MultiColumn(count=1)`

### 1.3 Answer Highlight (`answer_box`)
Applies specific emphasis to answer keys.
- **Logic**:
  - `SetFontBold(is_bold=True)`
  - `SetFontSize(size=14.0)`
  - `InsertText(text="VALUE")`
  - Reset styles (`bold=False`, `size=10.0`)

## 2. Implementation in Python

The templates are implemented as a static class `MathWorkbookTemplates` (alias `T`) to support functional composition.

```python
class MathWorkbookTemplates:
    @staticmethod
    def problem_header(problem_number: int) -> List[HwpAction]:
        return [
            SetParaShape(left_margin=20, indent=-20),
            InsertText(text=f"{problem_number}. ")
        ]
    
    @staticmethod
    def answer_box(answer_text: str) -> List[HwpAction]:
        return [
            SetFontBold(is_bold=True),
            SetFontSize(size=14.0),
            InsertText(text=answer_text),
            SetFontBold(is_bold=False),
            SetFontSize(size=10.0)
        ]
```

## 3. High-Fidelity Sequence Pattern

For a 2-column workbook page like `sample.pdf`, the recommended action sequence is:

1. `CreateBorderBox(border_type="Solid")` (Encapsulate entire content)
2. `MultiColumn(count=2)` (Start 2-column)
3. Iterate Left Column Problems (4, 5, 6)
4. `BreakColumn` (Move to right)
5. Iterate Right Column Problems (7, 8, 9)
6. `MultiColumn(count=1)` (Reset)
