# HWP Automation: NLP Interface & Action Expansion Design

## 1. Executive Summary
This document outlines the design for a Natural Language Processing (NLP) interface that translates Korean user prompts into ODA-compliant HWP Action Objects. It leverages the Pydantic models defined in `lib/models.py` as the strict schema for intention mapping.

## 2. Architecture: The "Prompt-to-Action" Pipeline

```mermaid
graph LR
    A[User Prompt (Korean)] --> B[NLP Processor];
    B --> C{Parsing Strategy};
    C -- Simple intent --> D[Rule/Regex Engine];
    C -- Complex intent --> E[LLM Dispatcher (Future)];
    D --> F[Action Object (Pydantic)];
    E --> F;
    F --> G[Bridge Transport];
    G --> H[Windows Executor];
```

### 2.1 The Schema (Ontology)
The "Source of Truth" is the Pydantic definition.
- **Why**: Ensures that whatever the NLP produces is *guaranteed* to be executable by the Windows engine.
- **Location**: `/home/palantir/hwpx/lib/models.py`

## 3. Action Vocabulary Expansion
Based on `ActionTable.txt` research, we will expand the Ontology to support:

| Domain | Action ID | Pydantic Model | Parameters |
| :--- | :--- | :--- | :--- |
| **Basic** | `InsertText` | `InsertText` | `text` |
| **Table** | `TableCreate` | `CreateTable` | `rows`, `cols`, `width_type` |
| **Image** | `InsertPicture`* | `InsertImage` | `path`, `width`, `height`, `treat_as_char` |
| **Font** | `CharShape` | `SetFontSize` | `size` (pt) |
| **Font** | `CharShape` | `SetFontBold` | `is_bold` (bool) |
| **Format** | `ParagraphShape` | `SetAlign` | `align_type` (Center, Left, Right) |

*\*Note: `InsertPicture` is mapped to `InsertLinkImageToDoc` or `pyhwpx` wrapper internally.*

## 4. NLP Parsing Strategy (Phase 1)
Since a heavy local LLM is not guaranteed, Phase 1 will implement a **Keyphrase-Driven Intents Engine** using `Enum` mapping and Regex.

### Example Mappings
- **"이미지 삽입해줘: photo.jpg"**
  - Intent: `InsertImage`
  - Arg: `photo.jpg`
- **"5행 3열 표 만들어"**
  - Intent: `CreateTable`
  - Pattern: `(\d+)행\s*(\d+)열`

## 5. Security & Validation
- **Path Validation**: Image paths must be converted to absolute Windows paths via `WSLBridge`.
- **Typing**: Pydantic validates that `rows` is an integer, preventing injection attacks.
