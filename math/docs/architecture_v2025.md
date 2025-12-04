# Architecture Blueprint v2025 (Dec 1, 2025)

## 1. System Overview
**Project:** Math/AI Hybrid Platform
**Goal:** High-performance, visually immersive mathematical visualization and computation engine.
**Core Philosophy:** "Living Math" - Real-time, interactive, and aesthetically profound.

## 2. Technology Stack (The 2025 Standard)

### 2.1 Frontend: React 19 Native
*   **Framework:** React 19 (via Vite).
*   **Component Model:** **RSC (React Server Components)** first.
    *   *Rule:* Components are Server Components by default.
    *   *Exception:* Use `"use client"` only for interactive leaves (e.g., Graphs, Inputs).
*   **Routing:** React Router v7 (with Future Flags enabled).
*   **State Management:** TanStack Query v6 (Async State) + React Context (Global UI State).
*   **Styling:** Tailwind CSS v4 (Zero-runtime) + Framer Motion (Animation).
*   **Visualization:** Three.js / React Three Fiber (R3F) for 3D rendering.

### 2.2 Backend: Modern Python
*   **Framework:** FastAPI (Python 3.12+).
*   **Architecture:** Modular Monolith (Service-based).
*   **Database:** PostgreSQL.
*   **ORM:** **SQLModel** (Pydantic v2 Native).
    *   *Why:* Single definition for DB schema and API validation.
*   **Math Engine:** SymPy (Symbolic) + NumPy (Numerical).

## 3. Architectural Patterns (Hybrid Agile-X)

### 3.1 Data Flow
1.  **Input:** User interacts with Client Component (e.g., slider).
2.  **Request:** TanStack Query fetches data from FastAPI.
    *   *Or:* Server Action triggers computation (if applicable).
3.  **Processing:**
    *   **Input Sanitization:** Pydantic models validate math expressions.
    *   **Computation:** SymPy parses/solves; NumPy generates data points.
4.  **Response:** Optimized JSON vectors returned to frontend.
5.  **Render:** R3F renders the 3D graph efficiently using Web Workers.

### 3.2 Security & Stability (Cipher's Mandate)
*   **Input Throttling:** Debounce all math inputs (prevent DOS).
*   **Expression Sandboxing:** Strict parsing of math strings (no `eval`).
*   **Fail-Fast:** Circuit breakers on heavy computation endpoints.

### 3.3 Developer Experience (Forge's Workflow)
*   **Testing:** Vitest (Frontend) + Pytest (Backend).
*   **Linting:** Biome (JS/TS) + Ruff (Python).
*   **Strict Typing:** TypeScript 5.x + Python Type Hints (mypy strict).

## 4. Directory Structure (Proposed)

```
/
├── frontend/ (React 19)
│   ├── src/
│   │   ├── app/ (Routes)
│   │   ├── components/
│   │   │   ├── ui/ (Client - Interactive)
│   │   │   └── rsc/ (Server - Static/Layouts)
│   │   ├── lib/ (Math Utilities)
│   │   └── hooks/
├── backend/ (FastAPI)
│   ├── app/
│   │   ├── api/
│   │   ├── core/ (Config, Security)
│   │   ├── models/ (SQLModel)
│   │   └── services/ (Math Logic)
└── docs/
```
