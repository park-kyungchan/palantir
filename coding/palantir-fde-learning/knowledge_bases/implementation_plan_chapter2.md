# Palantir FDE Implementation Plan: Chapter 2 "Reasoning Lab"

This document outlines the engineering specification to implement **"Chapter 2: Connections"** as a fully interactive, data-driven web application. 
This is not a mockup; it is a **production-ready architecture** designed to capture student reasoning processes (Conjecturing, Generalizing, Justifying).

## 1. System Architecture

The application follows the **Stateless Client / Stateful Logic** pattern, consistent with Palantir ODA principles.

### 1.1 Tech Stack
*   **Framework**: `React 18` + `TypeScript 5.x` (Strict Mode)
*   **Target Device**: **Samsung Galaxy Book 4 Pro 360** (Windows Touch + S-Pen)
*   **Build Tool**: `Vite` (Fast HMR)
*   **Canvas Engine**: `react-konva` (High-performance 2D rendering)
*   **Ink Engine**: `perfect-freehand` (Pressure-sensitive stroke rendering)
*   **Geometry Logic**: `polygon-clipping` (Martinez) + `simplify-js` (Path optimization)
*   **State Machine**: `XState v5`
*   **Input Handling**: `use-gesture` (Robust Touch/Pen differentiation)
*   **Styling**: `TailwindCSS`
*   **Analytics**: `RxJS`

### 1.2 Directory Structure
```
src/
├── components/
│   ├── canvas/
│   │   ├── CookieShape.tsx       # Dynamic Polygon Component
│   │   ├── GridOverlay.tsx       # Micah's Grid Logic
│   │   └── GrowingSquare.tsx     # 4th Grade Tiling Logic
│   ├── tools/
│   │   ├── SlicerTool.tsx        # S-Pen "Laser Cutter" Logic
│   │   └── SnappingLayer.tsx     # Magnetic Logic
│   ├── ink/
│   │   └── AnnotationLayer.tsx   # Perfect-Freehand Canvas (S-Pen)
│   ├── feedback/
│   │   ├── GhostOverlay.tsx      # Visual Counterexample
│   │   └── ConfidenceSlider.tsx  # Metacognition Input
├── logic/
│   ├── geometry/
│   │   ├── slicer.ts             # "Line-to-Polygon-Difference" Algo
│   │   └── tiler.ts              # Recursive Square Generation Algo
│   └── machines/
│       └── reasoningMachine.ts   # XState Logic (Guess -> Test -> Justify)
├── telemetry/
│   ├── eventBus.ts               # RxJS Stream
│   └── logger.ts                 # JSON Formatter for Teacher Dashboard
└── App.tsx
```

---

## 2. Core Implementation Modules

### 3. Module B: S-Pen Integration & The "Cookie Slicer"
**Objective**: Leverage the Galaxy Book's S-Pen for authentic "Cutting" and "Annotating".

#### 3.1 Input Differentiation Strategy
We must strictly distinguish between **Pen (Precision)** and **Touch (Manipulation/Hand)**.

```typescript
// hooks/useGalaxyInput.ts
export function useGalaxyInput() {
  const handlePointerDown = (e: React.PointerEvent) => {
    if (e.pointerType === 'pen') {
      // S-Pen Logic: Pressure-sensitive Ink or Precise Cut
      const pressure = e.pressure; // 0.0 to 1.0 (Standard Web API)
      return { mode: 'PEN', pressure };
    } else if (e.pointerType === 'touch') {
      // Finger Logic: Pan, Zoom, or Drag Shapes
      return { mode: 'TOUCH' };
    }
  };
}
```

#### 3.2 The "Laser Cutter" (Freehand Slicing)
Instead of a rigid line, we allow the student to "slice" with the pen naturally.

1.  **Stroke Capture**: Record the S-Pen path as a `Point[]`.
2.  **Simplification**: Use `simplify-js` to reduce jitter.
3.  **Expansion**: Convert the stroke into a **Thin Polygon** (width 1px).
4.  **Subtraction**: `Difference = CookiePolygon - StrokePolygon`.

#### 3.3 "Perfect Ink" Annotation
Students can write "$2 \times 2 = 4$" directly on the canvas using `perfect-freehand`.

```typescript
// components/ink/AnnotationLayer.tsx
import { getStroke } from 'perfect-freehand';

// Map S-Pen pressure to stroke width
const stroke = getStroke(points, {
  size: 8,
  thinning: 0.5,
  smoothing: 0.5,
  streamline: 0.5,
  simulatePressure: false, // We have REAL pressure from S-Pen
});
```
This layer sits *above* shapes but *below* UI controls, allowing "Think Aloud" scribbles.

---

### 4. Module C: The "Growing Square" Engine (Grade 3 ~ 5)
**Objective**: Visualize the $k^2$ area growth rule dynamically.

#### 3.1 Technical Logic: Parametric Instancing
Instead of scaling a single `rect`, we instantiate $N \times N$ unit squares.

```typescript
// components/canvas/GrowingSquare.tsx
const GrowingSquare = ({ sideLength }) => {
  // sideLength: 1, 2, 3...
  // Calculate total units needed
  const units = sideLength * sideLength; 
  
  return (
    <Group>
      {/* 1. Underlying Grid (The "Hole" Proof) */}
      <Grid size={sideLength} opacity={0.3} />
      
      {/* 2. Instanced Unit Squares */}
      {Array.from({ length: units }).map((_, i) => (
        <Rect 
            key={i}
            width={UNIT_SIZE} 
            height={UNIT_SIZE}
            x={(i % sideLength) * UNIT_SIZE}
            y={Math.floor(i / sideLength) * UNIT_SIZE}
            fill={i < (sideLength/2)**2 ? "blue" : "red"} // Color coding previous generation
            animate={true} // Use React-Spring for "Explosion" effect
        />
      ))}
    </Group>
  );
};
```

#### 3.2 Technical Logic: Counterexample Generation
If the student inputs "Area = 2" for Side=2:
1.  System renders a **Ghost Rect** of size $1 \times 2$ (Area 2).
2.  System superimposes it on the **True Grid** ($2 \times 2$).
3.  **Result**: 2 empty grid cells remain visible.
4.  **Feedback**: "You predicted 2, but the grid shows 4 slots. Where are the missing 2?"

---

### 5. Data Layer: The "Reasoning Trace"
We capture providing not just the answer, but the **strategy**.

#### 4.1 Telemetry Schema (`telemetry/logger.ts`)
```json
{
  "trace_id": "uuid-v4",
  "student_id": "std_01",
  "problem_id": "cookie_comparison",
  "events": [
    {
      "timestamp": 1709...,
      "action": "TOOL_SELECT",
      "payload": { "tool": "SCISSORS" }
    },
    {
      "timestamp": 1709...,
      "action": "CUT_ATTEMPT",
      "payload": { "polygon_id": "cookie_B", "result_fragments": 2 }
    },
    {
      "timestamp": 1709...,
      "action": "HESITATION",
      "payload": { "duration_ms": 4500, "hover_target": "cookie_A" }
    }
  ]
}
```
**Teacher Dashboard Insight**: "Hesitation" events clustered around "Cookie A" imply the student suspects A is larger but lacks the strategy to prove it.

---

## 6. Execution Roadmap

1.  **Initialize Project**: `npm create vite@latest reasoning-lab -- --template react-ts`
2.  **Install Core Libs**: `npm install konva react-konva polygon-clipping xstate @xstate/react perfect-freehand`
3.  **Phase 1 (Input)**: Implement `useGalaxyInput` to separate Pen vs. Touch events reliably on Galaxy Book.
4.  **Phase 2 (Ink)**: Build `AnnotationLayer` and verify pressure sensitivity mechanics.
5.  **Phase 3 (Slicer)**: Implement S-Pen based slicing (Stroke expansion -> Difference).
6.  **Phase 4 (Logic)**: Wire up XState and Telemetry.

This plan ensures technical fidelity to the educational goals of Chapter 2.
