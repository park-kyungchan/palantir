# DocLayout-YOLO Compatibility & Patching Guide

The `DocLayout-YOLO` model, specifically when loaded via the `ultralytics` library in certain environments, can exhibit two major compatibility issues that prevent standard inference.

## 1. Issue: `AttributeError: 'Conv' object has no attribute 'bn'`

### Symptom
Inference fails during the forward pass with `AttributeError: 'Conv' object has no attribute 'bn'` inside the `doclayout_yolo/nn/modules/g2l_crm.py` or similar modules. This occurs because the model attributes are queried at runtime but are missing from the loaded state dict or class definition.

### Resolution: Runtime Injection
Inject a dummy `nn.Identity()` layer for the missing `bn` attribute immediately after loading the model. A recursive search for both direct `bn` attributes and sub-module `dcv.bn` structures is often necessary.

```python
import torch.nn as nn

def patch_model_bn(model):
    count = 0
    # Process all modules recursively
    for m in model.modules():
        # Direct attribute check (for fused modules)
        if "Conv" in m.__class__.__name__ and not hasattr(m, 'bn'):
            setattr(m, 'bn', nn.Identity())
            count += 1
        
        # Sub-module attribute check (specific to G2L-CRM blocks)
        if hasattr(m, 'dcv') and not hasattr(m.dcv, 'bn'):
            m.dcv.bn = nn.Identity()
            count += 1
    return count
```

## 2. Issue: `AttributeError: 'dict' object has no attribute 'shape'`

### Symptom
After fixing the `bn` error, the call to `results = model(img)` fails within `ultralytics/utils/nms.py` (specifically in `non_max_suppression`).
```
  File "ultralytics/utils/nms.py", line 66, in non_max_suppression
    if prediction.shape[-1] == 6 or end2end:
AttributeError: 'dict' object has no attribute 'shape'
```

### Cause
The `DocLayout-YOLO` model architecture returns a dictionary of tensors (often containing keys like `'one2one'`, `'one2many'`) rather than the single concatenated prediction Tensor that the default `ultralytics` Non-Max Suppression (NMS) logic expects.

### Diagnosis
Inspect the raw output of the underlying PyTorch model:
```python
model = YOLO("path/to/model.pt")
# Direct forward pass on the internal model
raw_out = model.model(dummy_input)
print(type(raw_out)) # Output: <class 'dict'>
print(raw_out.keys()) # Output: dict_keys(['one2one', 'one2many', ...])
```

### Resolution: Transparent Model Wrapper
To fix the output format mismatch while maintaining compatibility with `ultralytics` internal calls (like `.fuse()` or attribute access), implement a transparent wrapper.

```python
import torch.nn as nn

class DocLayoutWrapper(nn.Module):
    """
    Wrapper to handle DocLayout-YOLO output format incompatibility.
    Extracts 'one2one' tensor from dict and delegates methods to the base model.
    """
    def __init__(self, model):
        super().__init__()
        self.model = model
    
    def forward(self, *args, **kwargs):
        res = self.model(*args, **kwargs)
        if isinstance(res, dict) and 'one2one' in res:
            return res['one2one']
        return res
        
    def fuse(self, *args, **kwargs):
        # Ultralytics internals (like AutoBackend) often call .fuse(verbose=False)
        # Failure to accept *args/**kwargs leads to TypeError.
        if hasattr(self.model, 'fuse'):
            try:
                self.model.fuse(*args, **kwargs)
            except TypeError:
                # Handle cases where the underlying model's fuse doesn't accept args
                self.model.fuse()
        return self
        
    def __getattr__(self, name):
        # Delegate attribute access to the underlying model
        # Critical for 'pt', 'yaml', 'stride', etc. lookups by Ultralytics
        try:
            return super().__getattr__(name)
        except AttributeError:
            return getattr(self.model, name)
```

### 3. Troubleshooting Persistent `bn` Errors
If `AttributeError: 'Conv' object has no attribute 'bn'` persists even after patching:
- **Execution Order**: Ensure the patch is applied *after* calling `YOLO(model_path)` and *before* any inference.
- **Deeper Inspection**: Some versions of `doclayout-yolo` use custom convolutional layers that might not be detected by simple class-name checks. Use `named_modules()` to iterate and print the class names of all modules to identify targets. Specifically, check modules like `G2L_CRM` which may contain internal instances (e.g., `dcv`) that require an explicit `bn` attribute.
- **Verification of Patch Execution**: If the error persists, use a "Hard Stop" exception to confirm the code path is reached:
    ```python
    def _load_model(self):
        # ... loading logic ...
        raise RuntimeError("VERIFYING PATCH ENTRY") 
        # If this doesn't crash the script with this error, the method isn't being called!
    ```
- **Logging vs Printing**: In some environments, `ultralytics` or other inference engines may capture or redirect `stdout`, causing `print()` statements to be lost. Use `logger.error()` or `logger.warning()` to ensure debug visibility.
- **Bypassing Log Capture (stderr)**: If both `print` and `logger` fail to show output in a constrained environment (e.g. during a remote execution or within a library that hooks stdout/stderr), use raw `sys.stderr.write` to force visibility:
    ```python
    import sys
    sys.stderr.write("DEBUG: Forcing output to stderr\n")
    ```
- **Bytecode Stale check**: If code changes appear ignored, clear Python cache: `find . -name "__pycache__" -type d -exec rm -rf {} +`.
- **Deep Investigation into Nested Objects**: Discovery revealed that simple iteration over `model.named_modules()` might miss certain attributes if they aren't registered as sub-modules. Specifically, in `doclayout_yolo`, the `DilatedBottleneck` module (often used in `G2L_CRM`) contains a `self.dcv` attribute which is a `Conv` instance that lacks `bn`.
    ```python
    if "DilatedBottleneck" in m.__class__.__name__:
        if hasattr(m, 'dcv') and not hasattr(m.dcv, 'bn'):
            setattr(m.dcv, 'bn', nn.Identity())
    ```
```python
self._model = YOLO(path)
# Patch 'bn' attributes...
# Wrap internal model
self._model.model = DocLayoutWrapper(self._model.model)
```

*Note: The `one2one` tensor is the primary output for end-to-end (DINO-style) YOLO variants used in DocLayout-YOLO.*
