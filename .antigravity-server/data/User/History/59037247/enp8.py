import os
import json
import pytest
import pandas as pd
from pathlib import Path
from scripts.analyze_xlsx_structure import scan_directory, analyze_file

@pytest.fixture
def sample_xlsx_dir(tmp_path):
    """Creates a temporary directory with a sample xlsx file."""
    d = tmp_path / "xlsx_data"
    d.mkdir()
    
    file_path = d / "test.xlsx"
    
    # Create a DataFrame and save to XLSX
    df1 = pd.DataFrame({'A': [1, 2, 3], 'B': ['x', 'y', 'z']})
    df2 = pd.DataFrame({'C': [1.1, 2.2], 'D': [True, False]})
    
    with pd.ExcelWriter(file_path) as writer:
        df1.to_excel(writer, sheet_name='Sheet1', index=False)
        df2.to_excel(writer, sheet_name='Sheet2', index=False)
        
    return d

def test_analyze_file(sample_xlsx_dir):
    """Test analysis of a single file."""
    file_path = sample_xlsx_dir / "test.xlsx"
    result = analyze_file(file_path)
    
    assert result['file_name'] == "test.xlsx"
    assert "Sheet1" in result['sheet_names']
    assert "Sheet2" in result['sheet_names']
    
    # Check Sheet1 stats
    s1 = result['sheets']['Sheet1']
    assert s1['row_count'] == 3
    assert s1['column_count'] == 2
    assert "A" in s1['columns']
    
    # Check Sheet2 stats
    s2 = result['sheets']['Sheet2']
    assert s2['row_count'] == 2

def test_scan_directory(sample_xlsx_dir):
    """Test recursive scanning."""
    # Add a nested valid file
    nested_dir = sample_xlsx_dir / "subdir"
    nested_dir.mkdir()
    
    nested_file = nested_dir / "nested.xlsx"
    pd.DataFrame({'X': [1]}).to_excel(nested_file, index=False)
    
    # Add an invalid file (not xlsx extension)
    (sample_xlsx_dir / "ignored.txt").write_text("ignore me")
    
    # Run scan
    results = scan_directory(str(sample_xlsx_dir))
    
    assert len(results) == 2
    filenames = sorted([r['file_name'] for r in results])
    assert filenames == ['nested.xlsx', 'test.xlsx']

def test_cli_execution(sample_xlsx_dir, tmp_path):
    """Test full CLI flow via subprocess or direct main invocation equivalent."""
    output_json = tmp_path / "report.json"
    
    # Direct function call simulation of CLI main logic
    results = scan_directory(str(sample_xlsx_dir))
    
    with open(output_json, 'w') as f:
        json.dump(results, f)
        
    assert output_json.exists()
    assert len(json.loads(output_json.read_text())) >= 1
