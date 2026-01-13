# DocLayout-YOLO Compatibility & Patching Guide

The `DocLayout-YOLO` model, specifically when loaded via the `ultralytics` library in certain environments, can exhibit two major compatibility issues that prevent standard inference.

## 1. Issue: `AttributeError: 'Conv' object has no attribute 'bn'`

### Symptom
Inference fails during the forward pass with `AttributeError: 'Conv' object has no attribute 'bn'` inside the `doclayout_yolo/nn/modules/g2l_crm.py` or similar modules. This occurs because the model attributes are queried at runtime but are missing from the loaded state dict or class definition.

### Resolution: Runtime Injection
Inject a dummy `nn.Identity()` layer for the missing `bn` attribute immediately after loading the model.

```python
import torch.nn as nn

def patch_model_bn(model):
    count = 0
    for m in model.modules():
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

### Resolution Strategy: Model Wrapping
Wrap the model or modify the inference call to extract the primary prediction tensor (usually the `'one2one'` key for end-to-end models) before passing it to the `ultralytics` post-processing pipeline.

*Note: In the HWPX pipeline, this is handled by custom extraction logic in `LayoutDetector` to ensure compatibility with the standard `ultralytics` Results objects.*
