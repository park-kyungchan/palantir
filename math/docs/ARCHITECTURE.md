# System Architecture

## Overview
The Math Visualizer is designed as a modular, scalable system that separates business logic from infrastructure and UI.

## 1. Backend Architecture (DDD Lite)

The backend is structured to isolate the "Domain" (Math Logic) from the "Framework" (FastAPI).

```mermaid
graph TD
    API[Interface Layer (API)] --> App[Application Layer (Use Cases)]
    App --> Domain[Domain Layer (Models & Services)]
    App --> Infra[Infrastructure Layer (Observability)]
    Infra -.-> Domain
```

### Layers
- **Domain**: Pure Python code. No dependencies on FastAPI or DB. Contains `MathService` and `NumberAnalysis` model.
- **Application**: Orchestrates the domain. `AnalyzeNumberUseCase` handles the flow.
- **Infrastructure**: External tools. `ObservabilityMiddleware` lives here.
- **Interface**: The entry point. `endpoints.py` defines the HTTP routes.

## 2. Frontend Architecture (Feature-based)

The frontend uses a "Feature-based" folder structure to keep related code together.

```text
src/
├── components/ui/       # Atomic Design Components (GlassCard, GlassButton)
├── features/
│   └── analysis/        # The Core Feature
│       ├── api/         # API Calls
│       ├── components/  # Feature-specific UI
│       └── hooks/       # State Logic
└── lib/                 # Shared Utilities (Observability, API Client)
```

### Design System: "Neural Glass"
- **Visuals**: Dark mode, translucency, and neon accents.
- **Tech**: Tailwind CSS + Framer Motion.
- **Philosophy**: "Make math feel like magic."

## 3. Observability Pipeline

Data is collected from both ends and structured as `WSEvent` for future ingestion.

- **Backend**: Captures Request Duration, Status, and Trace ID.
- **Frontend**: Captures Web Vitals (CLS, LCP, TTFB).
