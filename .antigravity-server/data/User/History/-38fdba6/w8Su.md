# WSL2-Windows Integration and Configuration

The HWPX reconstruction system utilizes a hybrid cross-OS orchestration model to leverage Linux-based AI tools and Windows-native OLE automation.

## 1. System Architecture

### A. Orchestrator (WSL2 / Linux)
- **Environment**: Ubuntu.
- **Tools**: Ingestion (Docling, EasyOCR), IR Compilation.
- **Output**: JSON action payload for the Windows Executor.

### B. Bridge (WSLBridge)
- **Mechanism**: Translates Linux file paths to Windows UNC paths (e.g., `\\wsl.localhost\...`) and invokes the Windows executor via `powershell.exe`.

### C. Executor (Windows Host)
- **Environment**: Windows with Hancom Office 2024.
- **Mechanism**: `pyhwpx` via OLE Automation.

## 2. Environment Setup (WSL2)

### 2.1 Externally Managed Environments (PEP 668)
In modern Ubuntu, `pip install` on system Python is blocked.
**Solution**: Use Virtual Environments.
```bash
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
```

### 2.2 Dependency Management
- **Linux**: ML stack (`torch`, `ultralytics`, `docling`, `easyocr`). Storage footprint: ~5GB.
- **Windows**: `pyhwpx` (OLE/COM interface).

## 3. Communication Pattern
- **Direction**: Unidirectional (WSL2 -> Windows).
- **Protocol**: Subprocess invocation of `powershell.exe`.
- **UNC Path Mapping**: Ensure the Windows host has permissions to access the WSL filesystem via the network provider.

## 4. Operational Constraints
- **RAM**: Minimum 16GB recommended for vision models.
- **Git identity**: Ensure `git config user.email` and `user.name` are set locally to prevent commit failures on the workstation.
