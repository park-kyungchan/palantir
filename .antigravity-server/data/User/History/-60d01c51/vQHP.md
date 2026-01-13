# XLSX Structural Analysis Design Pattern

## 1. Overview
This pattern describes a standardized approach for probing unknown datasets stored in `.xlsx` format. It is designed to inform ingestion pipelines or data modeling tasks by providing a high-level schema and metadata report.

## 2. Core Components

### 2.1 Script: `analyze_xlsx_structure.py`
- **Objective**: Automate the discovery and schema extraction of multiple Excel workbooks.
- **Dependencies**: `pandas`, `openpyxl`.

### 2.2 Functional Requirements
1.  **Recursive Discovery**: Search input directories for files matching `*.xlsx`.
2.  **Workbook Metadata Extraction**:
    - File size, path, and last modification date.
    - Global sheet names.
3.  **Sheet Schema Analysis**:
    - Row count and column count.
    - Column headers (Field names).
    - Inferred data types per column (using pandas' type inference).
    - Basic stats (e.g., null counts).
4.  **Reporting**:
    - **JSON Output**: For machine consumption (e.g., automated document generation).
    - **Markdown Summary**: For human review.

## 3. Implementation Logic (Pseudo-code)

```python
import pandas as pd
import os

def analyze_file(path):
    workbook = pd.ExcelFile(path)
    report = {"sheets": {}}
    for sheet_name in workbook.sheet_names:
        df = pd.read_excel(path, sheet_name=sheet_name)
        report["sheets"][sheet_name] = {
            "columns": df.columns.tolist(),
            "types": df.dtypes.astype(str).to_dict(),
            "row_count": len(df)
        }
    return report

def main(input_dir):
    results = {}
    for root, _, files in os.walk(input_dir):
        for f in files:
            if f.endswith(".xlsx"):
                path = os.path.join(root, f)
                results[f] = analyze_file(path)
    # Save results to output
```

## 4. Governance Alignment
This implementation pattern aligns with the **Orion ODA Planning Protocol** by providing a predictable, testable, and documented approach to data analysis tasks.
