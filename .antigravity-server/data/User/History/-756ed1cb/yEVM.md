# Unified Document Model (UDM) Specification

The Unified Document Model (UDM) is a machine-readable JSON representation of an HWPX document. It is designed to bridge the gap between complex OWPML XML structures and downstream consumers (AI models, data pipelines) by resolving references and providing semantic context.

## 1. Design Rationale

As identified in the OWPML Architecture analysis, HWPX separates declaration (header.xml) and reference (section.xml). This introduces high complexity for data consumers who must maintain state for style IDs.

The UDM solves this by:
1. **Dereferencing**: Pulling properties (font face, size, margins) directly into the paragraph/run objects.
2. **Standardization**: Converting HWP units and internal color codes into standard units (pt, mm, hex).
3. **Semantic Layer**: Adding metadata like `semantic_type` to paragraphs based on layout and style heuristics.

## 2. JSON Schema Definition

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "HWPX Unified Document Model (UDM)",
  "type": "object",
  "required": ["document_metadata", "content_structure"],
  "properties": {
    "document_metadata": {
      "type": "object",
      "properties": {
        "title": { "type": "string" },
        "author": { "type": "string" },
        "created_at": { "type": "string", "format": "date-time" },
        "page_count": { "type": "integer" }
      }
    },
    "layout": {
      "type": "object",
      "properties": {
        "page_width_mm": { "type": "number" },
        "page_height_mm": { "type": "number" },
        "columns": { "type": "integer", "default": 1 },
        "border": {
            "type": "object",
            "properties": {
                "enabled": { "type": "boolean" },
                "type": { "type": "string" }
            }
        }
      }
    },
    "content_structure": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "section_index": { "type": "integer" },
          "column_index": { "type": "integer" },
          "paragraphs": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "id": { "type": "string" },
                "semantic_type": {
                  "type": "string",
                  "enum": ["Heading1", "Heading2", "BodyText", "ProblemNumber", "SubProblem", "Equation", "Answer"]
                },
                "text_content": { "type": "string" },
                "runs": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "text": { "type": "string" },
                      "char_style": {
                        "type": "object",
                        "properties": {
                          "font_family": { "type": "string" },
                          "font_size_pt": { "type": "number" },
                          "is_bold": { "type": "boolean" },
                          "color_hex": { "type": "string" }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

## 3. Implementation Patterns

When generating UDM from HWPX:
- **Style Resolution**: The parser must first build a lookup table from `header.xml`.
- **Paragraph Processing**: Iterate through `<hp:p>` tags, resolving `paraPrIDRef` and `styleIDRef`.
- **Text Extraction**: Merge all `<hp:t>` content within a paragraph to fill `text_content`.
- **Unit Conversion**: `1 HwpUnit = 1/7200 inch`. Formula: `Points = HwpUnits / 100`.
