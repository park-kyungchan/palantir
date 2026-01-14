
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

from lib.oda.ontology.storage.database import initialize_database
from lib.oda.api.routes import router as proposal_router

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
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Use relative path for portability (Smell #2 fix)
FRONTEND_DIST = Path(__file__).parent.parent.parent / "frontend" / "dist"

# Mount static assets if they exist
static_dir = FRONTEND_DIST / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# SPA Catch-All - ALWAYS registered (Smell #3 fix)
# Must be the LAST route to avoid swallowing API calls
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """
    Serve SPA frontend or return appropriate error responses.
    
    - /api/* paths: Return 404 with {"code": "NOT_FOUND"}
    - Other paths: Serve index.html or 503 if frontend not built
    """
    # API paths should NOT be served by SPA (Smell #4 fix: "api/" not "api")
    if full_path.startswith("api/") or full_path == "api":
        return JSONResponse(
            {"code": "NOT_FOUND", "message": "API Endpoint not found"},
            status_code=404
        )
    
    # Serve frontend
    index_path = FRONTEND_DIST / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    
    # Frontend not built - return 503 Service Unavailable
    return JSONResponse(
        {"code": "CONSTRUCTION", "message": "Frontend not built. Run npm build."},
        status_code=503
    )

