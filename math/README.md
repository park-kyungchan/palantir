# Math Visualizer & Analyzer

A modern, full-stack application for visualizing mathematical concepts, built with **FastAPI (DDD)** and **React (Neural Glass)**.

## 🏗 Architecture

This project follows a strict **Domain-Driven Design (DDD) Lite** architecture for the backend and a **Feature-based** architecture for the frontend.

### Backend (`/backend`)
- **Framework**: FastAPI + Uvicorn
- **Pattern**: DDD Lite (`domain`, `application`, `infrastructure`, `interface`)
- **Type Safety**: strict `mypy` compliance
- **Package Manager**: `uv`

### Frontend (`/frontend`)
- **Framework**: React + Vite
- **Design System**: "Neural Glass" (Tailwind v4 + Framer Motion)
- **State**: React Hooks
- **Package Manager**: `pnpm`

### Observability (`/observability`)
- **Protocol**: `WSEvent` (WebSocket-ready structure)
- **Metrics**: Web Vitals (CLS, LCP, TTFB) + API Latency

## 🚀 Getting Started

### Prerequisites
- Docker & Docker Compose
- Node.js 20+ (for local dev)
- Python 3.12+ (for local dev)

### Quick Start (Docker)
The easiest way to run the entire stack:

```bash
docker compose up --build
```

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000/docs
- **Observability**: (Logs in console)

### Local Development

#### Backend
```bash
cd backend
uv sync
uv run uvicorn main:app --reload
```

#### Frontend
```bash
cd frontend
pnpm install
pnpm dev
```

## 🧪 Testing

### Backend
```bash
cd backend
uv run pytest
```

### Frontend
```bash
cd frontend
pnpm test      # Unit Tests
pnpm e2e       # Playwright Tests
```

## 📚 Documentation
See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed design decisions.
