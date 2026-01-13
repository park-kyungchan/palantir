# Audit: Parameter Set Table Analysis

**Target Document**: `ParameterSetTable_2504.pdf`
**Primary Goal**: Verify the internal structure of HWP Parameter Sets and establish linkage with the Action Table.

## 1. Structural Findings
Unlike the flat table structure of `ActionTable_2504.pdf`, the Parameter Set Table is organized as a series of sections.

- **Header Format**: `[Number]) [ParameterSetID] : [Description]`
  - Example: `72) InsertText : 텍스트 삽입`
- **Inner Table Columns**:
  - `Item ID`: The name used in `SetItem` OLE calls (e.g., `Text`, `Color`).
  - `Type`: The HWP Parameter Item Type (e.g., `PIT_BSTR`, `PIT_UI1`, `PIT_UI2`).
  - `Description`: Details regarding the parameter's role and possible values (enums).

## 2. Dependency Analysis
The audit confirmed a direct 1:1 or 1:N linkage between the `ParameterSet ID` column in the Action Table and the section headers in the Parameter Set Table.

| Source: ActionTable | Linkage | Target: ParameterSetTable |
|---|-|---|
| `InsertText` | → | `72) InsertText` |
| `TableCreate` | → | `116) TableCreate` |
| `BreakPage` (`-`) | → | N/A (Direct Run) |

## 3. Parsing Requirements
To successfully ingest this knowledge, the parser must:
1. **Segment by Section**: Use a regex pattern `^\d+\)\s+(\w+)\s+:` to split the text into discrete parameter set definitions.
2. **Contextual Description Harvesting**: Capture the multi-line enum definitions (e.g., `0 = 쪽 번호`, `1 = 각주 번호`) which are often split across lines in the `Description` column.
3. **Type Normalization**: Ensure `Item Type` is captured as it determines the OLE method to use (e.g., `SetItem` vs specialized set accessors).

## 4. Integration Status
The `lib/knowledge/schema.py` has been updated to accommodate these findings with `ParameterSetDefinition` and `ParameterItem` models.
