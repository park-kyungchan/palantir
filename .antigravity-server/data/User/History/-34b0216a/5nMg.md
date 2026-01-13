# DocLayout-YOLO Compatibility & Patching Guide

The `DocLayout-YOLO` model, specifically when loaded via the `ultralytics` library in certain environments, can exhibit two major compatibility issues that prevent standard inference.

## 1. Issue: `AttributeError: 'Conv' object has no attribute 'bn'`

### Symptom
Inference fails during the forward pass with `AttributeError: 'Conv' object has no attribute 'bn'` inside the `doclayout_yolo/nn/modules/g2l_crm.py` or similar modules. This occurs because the model attributes are queried at runtime but are missing from the loaded state dict or class definition.

### Resolution: Runtime Injection
Inject a dummy `nn.Identity()` layer for the missing `bn` attribute immediately after loading the model. A recursive search for both direct `bn` attributes and sub-module `dcv.bn` structures (especially within `DilatedBlock` and `DilatedBottleneck` components) is necessary.

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
- **Hard-coded Attribute Injection**: If `named_modules()` iteration fails to resolve the issue (e.g., due to dynamic attribute creation), manually inject the attribute into the specific instance if the path is known:
    ```python
    if "DilatedBottleneck" in m.__class__.__name__:
        if hasattr(m, 'dcv') and not hasattr(m.dcv, 'bn'):
            setattr(m.dcv, 'bn', nn.Identity())
    ```

- **Unregistered Submodule Attributes (The "Invisible" Path)**: In some versions of `doclayout-yolo` (e.g., G2L-CRM components), certain `Conv` modules like `dcv` are assigned as plain attributes (`self.dcv = Conv(...)`) but might not be correctly registered in the module hierarchy. In this case, `named_modules()` will skip them. You must explicitly check for these attributes when visiting the parent module (often a `DilatedBlock` or `DilatedBottleneck`):
    ```python
    for name, m in model.named_modules():
        cname = m.__class__.__name__
        # named_modules() iterates over G2L_CRM stages but might skip nested dcv attributes
        if any(target in cname for target in ["DilatedBlock", "DilatedBottleneck"]):
            if hasattr(m, 'dcv') and not hasattr(m.dcv, 'bn'):
                 sys.stderr.write(f"DEBUG: Patching hidden dcv in {name}\n")
                 m.dcv.bn = nn.Identity()
    ```

- **Deep Hierarchy Discovery**: Analysis of `named_modules()` traces for `DocLayout-YOLO` reveals a deeply nested structure for layout-dense stages:
    `G2L_CRM` -> `m` (ModuleList) -> `DilatedBottleneck` -> `dilated_block` (DilatedBlock) -> `dcv` (Conv).
    If a patch fails at one level, verify if the `dcv` attribute is actually located on a child module (like `dilated_block`) rather than the visited parent.

- **Inline Patching (The "Guaranteed execution" Strategy)**: In large pipelines where model loading might be cached or occur via different entry points, applying the patch inside the `_load_model` method might be insufficient. Implement an "Inline Patch" within the main `detect()` method using a state flag to force application on the first inference:
    ```python
    def detect(self, image):
        # Guarantee patch application before inference
        if not hasattr(self, '_patched_flag'):
             if not self._model_loaded:
                  self._load_model()
             
             # Patch logic here (Conv check + DilatedBottleneck check)
             # ...
             self._patched_flag = True
        
        # Proceeed with inference
        return self._model(image, ...)
    ```

- **Import Caching Issues**: If changes to `detector.py` are not reflected in a complex pipeline (like `docling` ingestion), it may be due to Python's module caching. As a diagnostic/quick fix, copy the module to a new file (e.g., `detector_patched.py`) and update imports to force a fresh load.

### 3.4 The "Ultimate Robustness" Strategy: Global Class-Level Monkey Patching
If attribute injection via `named_modules()` fails to persist at runtime (e.g., due to deep-copying by the inference engine, lazy re-initialization, or internal model fusion), the most reliable fix is to apply a **Monkey Patch** directly to the target class method.

- **Advantage**: Since the fix is applied to the class definition itself, it automatically applies to all existing and future instances of that class, regardless of how they are instantiated or manipulated by the `ultralytics` backend.
- **Implementation**: The patch should be applied at the **top level of the module** where the model is utilized (e.g., at the start of `lib/layout/detector.py`), immediately after imports.

```python
from doclayout_yolo.nn.modules.g2l_crm import DilatedBlock
import torch.nn.functional as F
import torch.nn as nn

def safe_dilated_conv(self, x, dilation):
    """Monkey-patched dilated_conv to handle missing bn lazily."""
    # Lazily inject bn if missing at the moment of execution
    if not hasattr(self.dcv, 'bn'):
        # Using nn.Identity as a drop-in replacement for BatchNorm
        self.dcv.bn = nn.Identity()
        
    act = self.dcv.act
    bn = self.dcv.bn
    weight = self.dcv.conv.weight
    padding = dilation * (self.k//2)
    return act(bn(F.conv2d(x, weight, stride=1, padding=padding, dilation=dilation)))

# Globally overwrite the class method before any model loading begins
DilatedBlock.dilated_conv = safe_dilated_conv
```

### 4. Visibility and Logging in Inference Engines
- **Log Suppression**: Libraries like `ultralytics` or `pydantic` (via `docling`) often capture `stdout`.
- **Bypassing Capture**: Use `sys.stderr.write` or file-to-disk logging (`with open('patch.log', 'w') as f: f.write(...)`) to verify patch execution in complex pipelines.

- **Isolate Testing Strategy**: When debugging deep model attributes (like `bn` in `DilatedBottleneck`), full pipeline runs can be slow and may suppress logs. Use an isolation script (`scripts/test_patch.py`) to verify model state without running full inference.

---

## 4. Development Journey (Walkthrough)

This section details the systematic process used to evolve the solution from instance-level patching to the final robust monkey-patching strategy.

### Phase 1: Identifying the Attribute Gap
Using deep module inspection (via `named_modules()`), we identified that certain custom convolutional layers (`Conv`) inside the `G2L_CRM` and `DilatedBlock` modules do not have the expected `bn` (Batch Normalization) attribute.

### Phase 2: Implementation of the "Guaranteed Patch"
Initial attempts to patch during `_load_model` were sometimes bypassed by Python's module caching or lazy loading in the `docling` pipeline. To ensure execution, we implemented an **Inline Patch** with a state flag.

### Phase 3: Solving the Output Format Conflict
`DocLayout-YOLO` returns a dictionary (containing `'one2one'`), but `ultralytics` expects a Tensor. We created a `DocLayoutWrapper` that extracts the `'one2one'` tensor in the `forward` pass and delegates all other calls.

### Phase 4: Verification in Constrained Environments
In complex pipelines (like `Docling` -> `Inference`), `stdout` logs are often suppressed. We bypassed this using **Stderr Logging** (`sys.stderr.write`) and **File-on-Disk Logging**.

### Phase 5: The Ultimate Fix - Monkey Patching
Despite inline patching, some attributes (like `dcv.bn`) appeared to "disappear" at runtime, likely due to object cloning. The final resolution was to **monkey patch the class method** directly. This fix was moved to the **top level of `lib/layout/detector.py`** to alter the `DilatedBlock` class globally before any instances are created.

---

## 5. [Retrospective] 디버깅 및 해결 과정 요약 (Korean Summary)

DocLayout-YOLO 모델의 `AttributeError: 'Conv' object has no attribute 'bn'` 오류를 해결하기 위해 진행했던 77단계의 디버깅 및 시행착오 요약입니다.

### 🚩 핵심 문제
**증상**: `DilatedBottleneck` 모듈 내부의 `dcv`에서 `bn` 속성이 없다며 충돌 발생.
**원인**: Ultralytics/YOLO의 로딩/퓨전 과정에서 속성이 소실되거나, 인스턴스가 동적으로 복제되면서 패치가 적용되지 않는 현상.

### 🛠️ 디버깅 및 해결 과정
1. **초기 패치 (실패)**: `_load_model`에서 모듈 순회 패치를 시도했으나, 통합 파이프라인에서 에러 지속.
2. **패러독스 분석**: 로그상으로는 패치되었으나 실제 추론 시점에 속성이 사라짐을 확인. `deepcopy`나 재구성 과정에서의 소실로 추정.
3. **타겟 정밀화**: `DilatedBottleneck.dcv` 경로를 특정하여 로그를 강화했으나 인스턴스 패치의 한계 확인.
4. **전략 수정 (성공)**: 인스턴스가 아닌 **클래스 메서드 자체를 런타임에 덮어쓰기(Monkey Patch)**하는 전략으로 선회. `DilatedBlock.dilated_conv`를 재정의하여 레이지 주입 로직을 심고 모듈 로드 시점에 전역 적용.

### ✅ 최종 결과
`lib/layout/detector.py` 상단에 **전역 몽키 패치**를 적용하여 모든 호환성 문제를 해결했으며, `verify_ir.py`를 통해 IR 생성이 정상적으로 작동함을 검증했습니다.

---

## 6. Summary Execution Sequence
The correct sequence for stable integration of DocLayout-YOLO is:
1. **Apply Monkey Patch** to `DilatedBlock.dilated_conv` at the **module level** (top of `detector.py`).
2. Initialize `YOLO(model_path)`.
3. Move to device (`.to(device)`).
4. **Patch remaining `bn` attributes** across `named_modules()`.
5. **Wrap model** with `DocLayoutWrapper` to normalize `dict` output to `Tensor`.
6. Clear bytecode cache (`__pycache__`) if changes appear ignored.
7. Execute inference.

*Note: The `one2one` tensor is the primary output for end-to-end (DINO-style) YOLO variants used in DocLayout-YOLO.*

---

## 7. Model Label Mapping (DocStructBench)
For reference, the `DocLayout-YOLO` models trained on the DocStructBench dataset utilize the following label mapping:
0.  `title`
1.  `plain text`
2.  `abandon`
3.  `figure`
4.  `figure_caption`
5.  `table`
6.  `table_caption`
7.  `table_footnote`
8.  `isolate_formula`
9.  `formula_caption`
10. `page_header`
11. `page_footer`
12. `page_number`
13. `header` (Section Header)

The `SemanticTagger` maps these generic labels to domain-specific types like `PROBLEM_BOX` and `ANSWER_BOX` using secondary heuristics.
