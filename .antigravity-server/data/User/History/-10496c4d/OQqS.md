# Walkthrough: WSL2 to Windows Reconstruction Handoff

## 1. Context
The HWPX Pipeline operates in a hybrid environment:
- **WSL2 (Linux)**: Handles heavy AI tasks (Layout Detection, OCR, IR Compilation).
- **Windows**: Hosts Hancom Office 2024 and the OLE/COM automation server.

## 2. The Handoff Mechanism
The `Builder` acts as the bridge. Instead of attempting a direct network call, it generates a portable payload.

### Step 1: Action Serialization (WSL)
The Pipeline runs `Compiler.compile()` to produce a JSON action list. This is useful for auditing but not executable.

### Step 2: Code Generation (WSL)
The `Builder` takes the actions and transpiles them into `reconstruct.py`. 
- **Path Handling**: The builder ensures that any paths (like images) are properly escaped for Windows (`\\`).
- **Logic Embedding**: All HWP state management (Parameter Sets) is baked into the script.

### Step 3: Execution (Windows)
The user (or a bridge agent) runs `python reconstruct.py` on the Windows host.
1. **Dispatcher**: `win32com.client.gencache.EnsureDispatch('HWPFrame.HwpObject')` connects to the running HWP instance.
2. **Security**: `hwp.RegisterModule` is called to suppress the "Allow local file access?" security prompt.
3. **Execution**: The script replays the compiled actions exactly as planned in the Linux environment.

## 3. Key Benefits of the Script-Based Handoff
- **Decoupling**: The Windows side doesn't need to know about Docling, YOLO, or Pytorch.
- **Auditability**: The generated `.py` script can be inspected before execution.
- **Resilience**: If the Windows host is offline, the script can be saved and run later.
