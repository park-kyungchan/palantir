# HWPX Deep Audit Task Checklist

## Stage A: Surface Scan
- [/] Phase 1: Core Pipeline (`models.py`, `compiler.py`, `ir.py`, `pipeline.py`)
- [ ] Phase 2: OWPML Engine (`lib/owpml/*.py`)
- [ ] Phase 3: Ingestors (`lib/ingestors/*.py`)
- [ ] Phase 4: Layout & Math (`lib/layout/`, `lib/math/`)
- [ ] Phase 5: Scripts & Utilities

## Stage B: Logic Trace
- [ ] Critical Path 1: PDF → HWPX Conversion
- [ ] Critical Path 2: OWPML Generation

## Stage C: Quality Gate
- [ ] C1: Type Safety Audit
- [ ] C2: ODA Pattern Opportunities
- [ ] C3: Exception Handling Audit
- [ ] C4: Docstring Coverage

## Final Deliverable
- [ ] Generate audit report with findings
