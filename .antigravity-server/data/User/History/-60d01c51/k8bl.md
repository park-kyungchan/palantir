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

## 3. Reference Implementation
The implementation uses `pandas` as the core engine to ensure high-fidelity type inference and `pathlib` for modern filesystem interaction.

```python
import pandas as pd
from pathlib import Path

def analyze_sheet(file_path: str, sheet_name: str):
    """Analyzes dimensions and headers of a sheet."""
    df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl')
    return {
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns": list(df.columns.astype(str)),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()}
    }

def analyze_file(file_path: Path):
    """Opens workbook and iterates through sheets."""
    xl = pd.ExcelFile(file_path, engine='openpyxl')
    stats = {"sheet_names": xl.sheet_names, "sheets": {}}
    for sheet in xl.sheet_names:
        stats["sheets"][sheet] = analyze_sheet(str(file_path), sheet)
    return stats
```

## 4. Verification Pattern (TDD)
To ensure the analyzer handles diverse Excel variants, a `pytest` suite should accompany the script. 

### 4.1 Mocking XLSX Data
Use a fixture to generate temporary files:
```python
@pytest.fixture
def sample_xlsx(tmp_path):
    path = tmp_path / "test.xlsx"
    pd.DataFrame({'A': [1], 'B': ['x']}).to_excel(path, index=False)
    return path
```

### 4.2 Assertion Strategy
1.  **Schema Match**: Verify inferred `dtypes` match expected (e.g., `int64`, `object`).
2.  **Dimension Match**: Assert `row_count` and `column_count`.
3.  **Discovery**: Ensure recursive scans find nested `.xlsx` but ignore `~$*` temp files.

### 4.3 Isolated Verification Strategy
In complex projects where global test configurations (e.g., `conftest.py`) introduce heavy dependencies (SQLAlchemy, asyncio, etc.) unrelated to the utility, use an isolation pattern:
1.  **Placement**: Move the utility test to a dedicated `temp_verification/` directory to avoid automatic `conftest.py` loading.
2.  **Path Management**: Execute with explicit environment variable setting: `PYTHONPATH=. python3 -m pytest temp_verification/test_xlsx_analysis.py`.
3.  **Dependency Guarding**: Ensure `requirements.txt` or `pyproject.toml` reflects the minimum toolset (`pandas`, `openpyxl`) to allow standalone execution in constrained environments.

## 5. Governance Alignment
This implementation pattern aligns with the **Orion ODA Planning Protocol** which mandates:
1.  **Traceability**: Clear link between user intent and script behavior.
2.  **Verifiability**: Automated testing of core logic.
3.  **Extensibility**: Standardized JSON output for integration into larger ingestion or LLM-augmentation workflows.
