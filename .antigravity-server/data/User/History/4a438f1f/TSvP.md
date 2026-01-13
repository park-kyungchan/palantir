# HWPX Deep Audit Implementation Plan

> **Target:** `/home/palantir/hwpx/`
> **Protocol:** 3-Stage Audit (Surface → Trace → Quality)
> **ODA Alignment:** Apply patterns from `park-kyungchan/palantir/` codebase

---

## User Review Required

> [!IMPORTANT]
> This audit plan covers **47+ Python files** across the HWPX codebase.
> Please confirm scope before execution.

**Key Decisions:**
1. Should we apply full ODA registry pattern (ActionTypes, ObjectTypes) to HwpAction models?
2. Priority for audit: Core Pipeline vs. Ingestors vs. Utilities?

---

## Proposed Audit Plan

### Stage A: SURFACE SCAN

| Component | Files | Check Items |
|-----------|-------|-------------|
| **Core Pipeline** | `lib/compiler.py`, `lib/models.py`, `lib/ir.py`, `lib/pipeline.py` | Type hints, docstrings, Pydantic validation |
| **OWPML Engine** | `lib/owpml/*.py` (5 files) | OWPML element generation, KS X 6101 compliance |
| **Ingestors** | `lib/ingestors/*.py` (12 files) | PDF/Docling/Surya integration, error handling |
| **Layout Analysis** | `lib/layout/*.py` (6 files) | Column detection, reading order |
| **Math Processing** | `lib/math/*.py` (5 files) | LaTeX recognition, HWP equation conversion |
| **Digital Twin** | `lib/digital_twin/schema.py` | SVDOM schema consistency |
| **Scripts** | `scripts/*.py` (23 files) | Utility scripts, batch processing |

---

### Stage B: LOGIC TRACE (Code-Level)

#### Critical Path 1: PDF → HWPX Conversion

```
[EntryPoint] main.py
    │
    ├── lib/pipeline.py::Pipeline.run()
    │       ↓
    │   lib/ingest_pdf.py::ingest_pdf()
    │       ↓
    │   lib/ingestors/{engine}.py
    │
    ├── lib/ir.py::Document (IR)
    │
    ├── lib/compiler.py::Compiler.compile()
    │       ↓
    │   lib/models.py::HwpAction subclasses
    │
    └── output_actions.py → executor_win.py (Windows)
```

#### Critical Path 2: OWPML Generation

```
[EntryPoint] lib/owpml/generator.py
    │
    ├── lib/owpml/elements.py (OWPML element models)
    ├── lib/owpml/template_builder.py
    └── lib/templates/skeleton/ (HWPX template files)
```

---

### Stage C: QUALITY GATE (ODA Alignment)

#### C1. Type Safety Audit

| File | Current State | Required Action |
|------|---------------|-----------------|
| `lib/models.py` | ✅ Pydantic models | Add `@register_action` decorator pattern |
| `lib/ir.py` | Mixed typing | Add full type hints |
| `lib/compiler.py` | Partial hints | Complete type annotations |

#### C2. ODA Pattern Opportunities

| Pattern | Current | ODA Improvement |
|---------|---------|-----------------|
| **Action Registry** | Manual class inheritance | `@register_action` + `ActionRegistry` |
| **Audit Logging** | Not present | Add `ActionRunner` pattern for trace |
| **Validation** | Pydantic only | Add Knowledge Base validation |

#### C3. Exception Handling Audit

```bash
# Find bare except clauses
grep -rn "except:" /home/palantir/hwpx/lib/
grep -rn "except Exception:" /home/palantir/hwpx/lib/ | grep -v "as e"
```

#### C4. Docstring Coverage

```bash
# Check functions without docstrings
python -c "
import ast
import os
for root, _, files in os.walk('/home/palantir/hwpx/lib'):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            with open(path) as fp:
                try:
                    tree = ast.parse(fp.read())
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            if not ast.get_docstring(node):
                                print(f'{path}:{node.lineno} - {node.name}()')
                except: pass
"
```

---

## Verification Plan

### Automated Tests (Existing)

```bash
# Run full test suite
cd /home/palantir/hwpx && source .venv/bin/activate
pytest tests/unit/ -v

# Specific test modules
pytest tests/unit/test_compiler_enhanced.py -v
pytest tests/unit/test_layout_detector.py -v
pytest tests/unit/test_math_detector.py -v
```

### Integration Tests

```bash
pytest tests/integration/ -v
```

### Manual Verification

1. **Syntax Check:** `python -m py_compile lib/compiler.py lib/models.py lib/ir.py`
2. **Import Check:** `python -c "from lib.compiler import Compiler; from lib.models import HwpAction; print('✅ OK')"`

---

## Module-by-Module Audit Checklist

### Phase 1: Core (Priority HIGH)

- [ ] `lib/models.py` - HwpAction classes (27 actions)
- [ ] `lib/compiler.py` - Compiler class (16 methods)
- [ ] `lib/ir.py` - Intermediate Representation
- [ ] `lib/pipeline.py` - Pipeline orchestration

### Phase 2: OWPML Engine (Priority HIGH)

- [ ] `lib/owpml/generator.py` - OWPML XML generation
- [ ] `lib/owpml/elements.py` - Element models
- [ ] `lib/owpml/template_builder.py` - Template handling
- [ ] `lib/schemas/udm_schema.json` - UDM Schema validation

### Phase 3: Ingestors (Priority MEDIUM)

- [ ] `lib/ingestors/base.py` - Base ingestor class
- [ ] `lib/ingestors/docling_ingestor.py`
- [ ] `lib/ingestors/surya_ingestor.py`
- [ ] `lib/ingestors/pymupdf_ingestor.py`
- [ ] 8 additional ingestor files

### Phase 4: Layout & Math (Priority MEDIUM)

- [ ] `lib/layout/detector.py` - Layout detection
- [ ] `lib/layout/reading_order.py` - Reading order
- [ ] `lib/math/detector.py` - Math detection
- [ ] `lib/math/recognizer.py` - LaTeX recognition

### Phase 5: Scripts & Utilities (Priority LOW)

- [ ] 23 script files in `scripts/`
- [ ] Entry points: `main.py`, `convert_pipeline.py`

---

## Expected Findings Categories

| Severity | Expected Issues |
|----------|-----------------|
| **CRITICAL** | Uncaught exceptions in production paths |
| **HIGH** | Missing type hints on public APIs |
| **MEDIUM** | Bare `except:` patterns, missing docstrings |
| **LOW** | Style inconsistencies, unused imports |

---

## Timeline Estimate

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| Stage A: Surface | 15 min | Structure map, legacy check |
| Stage B: Trace | 30 min | Call graphs, integration points |
| Stage C: Quality | 45 min | Findings report with line refs |
| **Total** | ~90 min | Full audit report |

---

> **Ready to Execute:** Pending user approval
