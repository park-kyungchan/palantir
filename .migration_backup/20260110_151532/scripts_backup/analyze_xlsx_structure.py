#!/usr/bin/env python3
import os
import argparse
import json
import pandas as pd
from typing import Dict, List, Any
from pathlib import Path

def analyze_sheet(file_path: str, sheet_name: str) -> Dict[str, Any]:
    """Analyzes a single sheet for dimensions and headers."""
    try:
        # Read only the header and a few rows to infer types and get columns
        # We start by reading the whole sheet to get accurate row counts, 
        # but for massive files this might be slow. 
        # Optimization: Read headers separately if row count isn't strictly needed, 
        # but stats are requested.
        df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl')
        
        return {
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns.astype(str)),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()}
        }
    except Exception as e:
        return {"error": str(e)}

def analyze_file(file_path: Path) -> Dict[str, Any]:
    """Analyzes a single XLSX file."""
    try:
        xl = pd.ExcelFile(file_path, engine='openpyxl')
        file_stats = {
            "file_name": file_path.name,
            "relative_path": str(file_path), # Will be made relative to root later if needed
            "size_bytes": file_path.stat().st_size,
            "sheet_names": xl.sheet_names,
            "sheets": {}
        }
        
        for sheet in xl.sheet_names:
            file_stats["sheets"][sheet] = analyze_sheet(str(file_path), sheet)
            
        return file_stats
    except Exception as e:
        return {
            "file_name": file_path.name,
            "path": str(file_path),
            "error": f"Failed to open workbook: {str(e)}"
        }

def scan_directory(root_dir: str) -> List[Dict[str, Any]]:
    """Recursively scans directory for xlsx files."""
    results = []
    root_path = Path(root_dir)
    
    if not root_path.exists():
        print(f"Error: Directory {root_dir} not found.")
        return []

    for file_path in root_path.rglob("*.xlsx"):
        # Skip temporary lock files (often start with ~$)
        if file_path.name.startswith("~$"):
            continue
            
        print(f"Analyzing: {file_path}")
        results.append(analyze_file(file_path))
        
    return results

def generate_markdown_summary(data: List[Dict[str, Any]]) -> str:
    """Generates a markdown summary of the analysis."""
    total_files = len(data)
    total_sheets = sum(len(item.get("sheet_names", [])) for item in data if "error" not in item)
    errors = [item for item in data if "error" in item or any("error" in s for s in item.get("sheets", {}).values())]
    
    md = f"# XLSX Structure Analysis Report\n\n"
    md += f"- **Total Files Scanned**: {total_files}\n"
    md += f"- **Total Sheets Found**: {total_sheets}\n"
    md += f"- **Files with Errors**: {len(errors)}\n\n"
    
    md += "## File Details\n\n"
    for item in data:
        md += f"### `{item.get('file_name', 'Unknown')}`\n"
        if "error" in item:
            md += f"> ⚠️ **Error**: {item['error']}\n\n"
            continue
            
        md += f"- **Path**: `{item['relative_path']}`\n"
        md += f"- **Size**: {item['size_bytes'] / 1024:.2f} KB\n"
        md += f"- **Sheets**: {', '.join(item['sheet_names'])}\n\n"
        
        if "sheets" in item:
            md += "| Sheet | Rows | Cols | Columns |\n"
            md += "|-------|------|------|---------|\n"
            for sheet_name, stats in item["sheets"].items():
                if "error" in stats:
                    md += f"| {sheet_name} | ERROR | - | - |\n"
                else:
                    cols = ", ".join(stats['columns'])[:50] + ("..." if len(str(stats['columns'])) > 50 else "")
                    md += f"| {sheet_name} | {stats['row_count']} | {stats['column_count']} | {cols} |\n"
            md += "\n"
            
    return md

def main():
    parser = argparse.ArgumentParser(description="Analyze structure of XLSX files in a directory.")
    parser.add_argument("--input", required=True, help="Input directory to scan")
    parser.add_argument("--output", required=True, help="Output JSON report path")
    
    args = parser.parse_args()
    
    print(f"Scanning directory: {args.input}")
    results = scan_directory(args.input)
    
    print(f"Found {len(results)} files. Writing report...")
    
    # Write JSON
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    # Write Markdown Summary (same filename but .md)
    md_path = str(Path(args.output).with_suffix('.md'))
    md_content = generate_markdown_summary(results)
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
        
    print(f"Done. Reports saved to:\n- {args.output}\n- {md_path}")

if __name__ == "__main__":
    main()
