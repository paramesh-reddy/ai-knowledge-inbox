"""Main FastAPI application entrypoint."""
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings
from app.core.logging import logger
from app.db.session import init_db
from app.api.routes import health, dashboard, documents, jobs, chat


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for application startup and shutdown."""
    logger.info("Initializing application resources...")
    # Ensure upload directory exists
    _ = settings.absolute_upload_dir
    # Initialize database tables
    try:
        await init_db()
    except Exception as e:
        logger.error(f"Failed to initialize database on startup: {e}")

    yield

    logger.info("Application shutting down.")


app = FastAPI(
    title="AI Knowledge Inbox API",
    description=(
        "Production-ready backend API for AI Knowledge Inbox. "
        "Provides asynchronous document ingestion, PostgreSQL/pgvector RAG retrieval, "
        "and grounded Gemini answers with validated citations."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS configuration
origins = [
    settings.frontend_origin,
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "*",  # Allow dev proxy and iFrame access
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Centralized exception handling
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    clean_errors = []
    for err in errors:
        clean_errors.append({
            "field": " -> ".join(str(loc) for loc in err.get("loc", [])),
            "message": err.get("msg"),
            "type": err.get("type"),
        })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Request validation failed", "errors": clean_errors},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log internally with trace, but do not leak secrets or tracebacks to clients
    logger.error(f"Unhandled server exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred. Please try again or check the system logs.",
            "error_type": exc.__class__.__name__,
        },
    )


# Register API Routers
app.include_router(health.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")
app.include_router(chat.router, prefix="/api")


@app.get("/", include_in_schema=False)
async def root():
    return {
        "app": settings.app_name,
        "status": "running",
        "docs": "/docs",
        "health": "/api/health",
    }
