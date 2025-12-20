
"""
Orion ODA V3 - API Application Entrypoint
========================================
Configures FastAPI with Security Middleware and Exception Handlers.

Security Features:
- HSTS (Strict-Transport-Security) enforced.
- CSP (Content-Security-Policy) default-src 'self'.
- Global Error Handling for valid JSON responses.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from scripts.ontology.storage.database import initialize_database
from scripts.api.routes import router as proposal_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Init DB
    await initialize_database()
    yield
    # Shutdown logic if needed

app = FastAPI(
    title="Orion Orchestrator V3",
    description="ODA Enterprise API",
    version="3.0.0",
    lifespan=lifespan
)

# =============================================================================
# MIDDLEWARE
# =============================================================================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        # HSTS: Enforce HTTPS for 2 years
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        # CSP: Restrict content sources
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        # Anti-Sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        # Clickjacking Protection
        response.headers["X-Frame-Options"] = "DENY"
        return response

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], # React Dev Server
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# EXCEPTION HANDLERS
# =============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": "INTERNAL_ERROR",
            "message": "An unexpected error occurred.",
            "details": str(exc) # Caution: Strip this in Prod
        }
    )

# =============================================================================
# ROUTES
# =============================================================================

app.include_router(proposal_router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "system": "Orion ODA V3"}

# =============================================================================
# FRONTEND MOUNTING (Monolithic Mode)
# =============================================================================
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

FRONTEND_DIST = "/home/palantir/orion-orchestrator-v2/frontend/dist"

if os.path.exists(FRONTEND_DIST):
    # 1. Mount Static Assets (JS/CSS)
    # Check if 'static' folder exists inside dist, otherwise mount dist root if simple
    static_dir = os.path.join(FRONTEND_DIST, "static")
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    # 2. SPA Catch-All
    # Must be the LAST route to avoid swallowing API calls
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Allow API calls to pass through 404 if not found (don't serve HTML for /api)
        if full_path.startswith("api"):
            return JSONResponse({"code": "NOT_FOUND", "message": "API Endpoint not found"}, status_code=404)
            
        index_path = os.path.join(FRONTEND_DIST, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return JSONResponse({"code": "Construction", "message": "Frontend building..."}, status_code=503)
