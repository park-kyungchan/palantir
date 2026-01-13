# Architecture: Hybrid WSL2-Windows Pipeline

The system utilizes a cross-OS orchestration model to leverage Linux-based AI/Parsing tools and Windows-native OLE automation.

## 1. System Components

### A. Orchestrator (WSL2 / Linux)
- **Environment**: Ubuntu.
- **Tools**: Python-based ingestion (Docling, Surya), IR (Intermediate Representation) Compilation.
- **Output**: A serialized JSON payload (`pipeline_payload.json`) containing a sequence of HWP Action Models.

### B. Bridge (WSLBridge)
- **Role**: Mediates between Linux and Windows.
- **Mechanism**: Translates Linux file paths to Windows UNC paths (e.g., `\\wsl.localhost\...`) and invokes the Windows executor via `powershell.exe`.

### C. Executor (Windows Host)
- **Environment**: Windows 10/11 with Hancom Office 2024 installed.
- **Mechanism**: `pyhwpx` library interacting with HWP via OLE Automation.
- **Responsibility**: Interprets the JSON payload and performs real-time actions (InsertText, CreateTable, SaveAs) in the HWP instance.

## 2. Data Flow (ETL Model)
1. **Extract**: `IngestorFactory` selects an engine to parse the source PDF/HWPX.
2. **Transform**: The `Compiler` maps layout elements (sections, paragraphs, tables) to HWP-specific action sets.
3. **Load**: The `WSLBridge` hands off the payload to `executor_win.py`, which populates the final HWPX document.

## 3. Communication Pattern
- **Direction**: Unidirectional (WSL2 -> Windows).
- **Communication Protocol**: Subprocess invocation of `powershell.exe` with command-line arguments.
