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

**Status**: ✅ REMEDIATED
**Verification**: `tests/manual_verify_table_formatting.py` and `tests/manual_verify_nested_tables.py` PASS
