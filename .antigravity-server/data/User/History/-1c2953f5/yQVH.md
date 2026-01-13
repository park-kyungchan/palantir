# HWPX Remediation Log (January 2026)

## 1. Exception Handling & Observability Fixes
Following the deep audit of the HWPX codebase, several "exception swallowing" patterns were identified and remediated to ensure alignment with Orion ODA standards.

### 1.1 Compiler Font Size Parsing
- **File**: `lib/compiler.py` (Line 321)
- **Issue**: A bare `except: pass` was swallowing errors during font size parsing from CSS-like strings (e.g., "10pt"). This made it impossible to diagnose why certain elements defaulted to unexpected sizes.
- **Fix**: Replaced with specific exception capture and logging.
  ```python
  try:
      size_val = float(style_obj.font_size.replace("pt", ""))
  except (ValueError, AttributeError) as e:
      logger.debug("Failed to parse font_size '%s': %s", style_obj.font_size, e)
  ```
- **Result**: Improved debuggability while maintaining graceful fallback.

### 1.2 Ingestor Table Detection
- **File**: `lib/ingestors/text_action_Ingestor.py` (Line 66)
- **Issue**: `except Exception:` was used without capturing the error or logging it in the fallback logic for `find_tables()`.
- **Fix**: Captured the exception and added `logger.debug()`.
  ```python
  except Exception as e:
      # Fallback logic if find_tables crashes
      import logging
      logging.getLogger(__name__).debug("find_tables failed: %s", e)
  ```
- **Result**: Failures in the PyMuPDF `find_tables` method (which requires specific versions) are now observable.

---
## 3. Refactoring Hazards: Automated Regex Scripts
During Phase 10 (Table Formatting), an attempt to automate the injection of cursor logic led to several critical regressions.

### 3.1 Non-Unique Anchor Matches
- **Symptom**: `IndentationError` and logic corruption in `_insert_text`.
- **Cause**: The regex anchor `self._pending_column_break = False` matched multiple locations (initialization, paragraph insertion, table creation). The script injected state-reset lines (`self._current_table = None`) into the middle of paragraph generation logic.
- **Remediation**: Reverted script changes and manually implemented the container logic.
- **Lesson**: Avoid broad regex replacements on common state variables. Use `count=1` or strict block identifiers.

### 3.2 Method Overlap / "Zombie Code"
- **Symptom**: `SyntaxError: unterminated triple-quoted string literal`.
- **Cause**: Overlapping `multi_replace` patterns left trailing fragments of old docstrings and implementation tails at the end of methods.
- **Remediation**: Manually purged redundant lines (219-268) in `header_manager.py`.

### 3.3 Initialization Gaps
- **Symptom**: `AttributeError: 'HwpxDocumentBuilder' object has no attribute '_current_container'`.
- **Cause**: Script failed to match the `__init__` pattern due to slight whitespace variations, leaving new state variables uninitialized.
- **Remediation**: Manually added initialization to `__init__` and `_init_document`.

### 3.4 Stale Reset Logic in Controls
- **Symptom**: `InsertEquation` and other inline controls defaulted to document root even when inside a table cell.
- **Cause**: Similar to Section 3.1, the automated script injected `self._current_table = None` into `_insert_equation`, `_insert_image`, and `_insert_textbox`. 
- **Remediation**: Manually removed reset lines in Phase 12 and applied the `container = self._current_container` pattern.

### 3.5 Refactoring Signature Mismatch (Phase 13)
- **Symptom**: `TypeError: HeaderManager.get_or_create_para_pr() got an unexpected keyword argument 'indent'`.
- **Cause**: During the refactor to support `numbering_id`, the `indent` and `line_spacing` parameters were inadvertently removed from the method signature in `header_manager.py` while still being passed by `document_builder.py`.
- **Remediation**: Restored the parameters and updated the internal cache key to be composite: `f"{align_str}_{indent}_{line_spacing}_{numbering_id}"`.
- **Lesson**: Signature parity must be maintained when refactoring central style methods to avoid breaking dependent stateful builders.

### 3.6 Uninitialized Caches
- **Symptom**: `AttributeError: 'HeaderManager' object has no attribute '_para_pr_cache'`.
- **Cause**: New style caches were added to methods but the constructor (`__init__`) was not updated to initialize the dictionary objects.
- **Remediation**: Initialized `_para_pr_cache`, `_char_pr_cache`, and element references (`para_properties`, `numberings`) in `HeaderManager.__init__`.

### 3.7 Phase 14 Regression: Style Decay
- **Symptom**: `manual_verify_styles.py` fails to detect CENTER alignment in `header.xml`.
- **Cause**: (Detected) `SetAlign` handler used `.upper()` ("CENTER"), while `HeaderManager` lookup map expected Title Case ("Center").
- **Remediation**: Removed `.upper()` in `document_builder.py`.
- **Status**: ✅ REMEDIATED
- **Verification**: `tests/manual_verify_styles.py` PASS.

### 3.8 Phase 14 Regression: PageSetup Margin Loss
- **Symptom**: `manual_verify_pagesetup.py` fails to find `<hp:margin>` tag within `<hp:pagePr>`.
- **Cause**: (Detected) `_update_page_setup` originally only updated margins if the element already existed in the skeleton. Secondary cause: "Truth Value" trap—newly created empty elements evaluate to `False` in deprecated Python ElementTree patterns, causing the verification script's `if margin_tag:` to fail even when the tag was present.
- **Remediation**: Modified `_update_page_setup` to automatically create `<hp:margin>` using `ET.SubElement` if missing. Updated verification script to use `if margin_tag is not None:`.
- **Status**: ✅ REMEDIATED
- **Verification**: `tests/manual_verify_pagesetup.py` PASS.

---
## 4. E2E Pipeline Unification (Phase 15 Remediation)
Following the deep audit of the E2E flow (`sample.pdf` pilot), the identified integration gaps between the high-fidelity builder and the legacy pipeline flows have been remediated.

### 4.1 Interface Mismatch
- **Issue**: `main.py` passing `--no-ocr` (mapped to `use_ocr`) vs `pipeline.py` expecting `use_mathpix`.
- **Fix**: Updated `main.py` to instantiate `HWPXPipeline` using the `use_mathpix` keyword argument, aligning the entry point with the core constructor.
- **Status**: ✅ REMEDIATED

### 4.2 Legacy Generator Hijack
- **Issue**: `HWPXPipeline` was wired to the legacy `HWPGenerator`, bypassing high-fidelity features.
- **Fix**: Swapped `HWPGenerator` for `HwpxDocumentBuilder` within `lib/pipeline.py`. The `run()` method now calls `builder.build(self.compiler.actions, hwpx_output)`.
- **Status**: ✅ REMEDIATED

### 4.3 Pilot Test Execution
- **Outcome**: The `sample.pdf` pilot test was initiated using `python main.py sample.pdf -o sample_pilot.json --no-ocr`.
- **Finding**: Initial execution yielded no console output and no files, suggesting a silent failure or an unhandled exception in the newly integrated path. Further investigation into the Docling/Mathpix ingestor flow is required for the pilot to succeed.

**Status**: ✅ INTEGRATED (Awaiting Success in Batch Processing)
