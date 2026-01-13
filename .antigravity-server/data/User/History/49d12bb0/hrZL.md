# Walkthrough: XLSX Structure Analysis Script

I have implemented a script to analyze the structure of `.xlsx` files. This tool will help you understand the data composition (sheets, columns, rows) of the files from Google Drive.

## 1. Feature Overview

### [analyze_xlsx_structure.py](file:///home/palantir/park-kyungchan/palantir/scripts/analyze_xlsx_structure.py)
This script recursively scans a directory, identifies all `.xlsx` files, and generates both a JSON report and a readable Markdown summary.

**Key Features:**
- **Recursive Scan**: Finds files in nested subdirectories.
- **Robustness**: Handles errors (e.g., corrupted files) gracefully.
- **Detailed Stats**: Extracts row counts, column headers, and inferred data types.
- **Dual Output**: Machine-readable JSON + Human-readable Markdown.

## 2. Usage Guide

### Prerequisites
Ensure dependencies are installed (already verified in your environment):
```bash
pip install pandas openpyxl
```

### Running the Analysis
1.  **Prepare Data**: Place your `.xlsx` files in a directory (e.g., `data/raw`).
2.  **Execute**:
    ```bash
    python scripts/analyze_xlsx_structure.py --input <path/to/data> --output <path/to/report.json>
    ```

### Example
```bash
# Analyze files in 'data/raw' and save report to 'analysis_report.json'
python scripts/analyze_xlsx_structure.py --input data/raw --output analysis_report.json
```

## 3. Verification Results

I verified the script using a dedicated unit test suite that simulated:
1.  **Valid Files**: Multi-sheet workbooks with known data.
2.  **Nested Directories**: Confirming recursive scanning works.
3.  **Invalid Files**: Ensuring non-xlsx files are ignored.

**Test Command:**
```bash
PYTHONPATH=. python3 -m pytest temp_verification/test_xlsx_analysis.py
```

**Result:**
```
temp_verification/test_xlsx_analysis.py ...                            [100%]
3 passed in 0.53s
```
All tests passed, confirming the script correctly identifies files, reads content, and outputs valid stats.
