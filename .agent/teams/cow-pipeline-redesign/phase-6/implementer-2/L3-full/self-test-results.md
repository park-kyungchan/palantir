# Self-Test Results — Implementer-2

## Import Verification
```
OCR imports: OK (cache, separator, client)
Vision imports: OK (gemini)
Model imports: OK (BBox, RegionSource, OcrResult, OcrRegion, MathElement, Diagram,
                   DiagramInternals, DiagramElement, LayoutAnalysis, SpatialRelation,
                   CombinedRegion, VisionResult)
```

## COND-1: cnt_to_bbox() Semantics Preservation (5 tests)
```
1. Normal contour [[10,20],[100,20],[100,80],[10,80]] → BBox(x=10,y=20,w=90,h=60) ✓
2. Empty contour [] → None ✓
3. Single point [[5,5]] → None ✓
4. Negative coords [[-10,-5],[50,50]] → BBox(x=0,y=0,w=60,h=55) ✓ (clamped)
5. Zero dimension [[5,5],[5,5]] → BBox(x=5,y=5,w=1,h=1) ✓ (min dimension)
```

## COND-4: merge_regions() IoU Algorithm (3 tests)
```
Input:
  Mathpix: m1 (0,0,100,100) "Hello" conf=0.9, m2 (200,200,50,50) "x^2" conf=0.8
  Gemini:  g1 (10,10,95,95) conf=0.7, g2 (500,500,80,80) conf=0.6

IoU(m1,g1) = 0.7414 → MERGE (>0.5 threshold)
IoU(m1,g2) = 0 → no match
IoU(m2,g1) = 0 → no match
IoU(m2,g2) = 0 → no match

Results:
  merged-0: source=MERGED, type=text, bbox=(0,0,105,105), conf=0.9, content="Hello" ✓
  m2:       source=MATHPIX, type=math, bbox=(200,200,50,50), conf=0.8, content="x^2" ✓
  g2:       source=GEMINI, type=figure, bbox=(500,500,80,80), conf=0.6, content=None ✓

Verified: Mathpix text preferred ✓, confidence=max(0.9,0.7)=0.9 ✓, bbox=union ✓
```

## Server Startup
```
python -m cow_mcp.ocr    → starts cleanly (stdio wait, no errors) ✓
python -m cow_mcp.vision → starts cleanly (stdio wait, no errors) ✓
```

## All Tests: PASS (8/8)
