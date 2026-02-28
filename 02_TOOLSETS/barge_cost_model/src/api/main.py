"""
FastAPI application for Interactive Barge Dashboard.
Provides REST API for routing, cost analysis, and search.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import logging

from src.config.settings import settings
from src.config.database import verify_db_connection
from src.utils.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Interactive Barge Dashboard API...")

    # Verify database connection
    if not verify_db_connection():
        logger.error("Database connection failed on startup!")
    else:
        logger.info("Database connection verified")

    yield

    # Shutdown
    logger.info("Shutting down Interactive Barge Dashboard API...")


# Create FastAPI app
app = FastAPI(
    title=settings.DASHBOARD_TITLE,
    description="REST API for inland waterway routing and cost analysis",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOW_ORIGIN.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add X-Process-Time header to responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG_MODE else "An error occurred"
        }
    )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.DASHBOARD_TITLE,
        "version": "1.0.0",
        "status": "running",
        "docs": "/api/docs",
        "health": "/health"
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    db_healthy = verify_db_connection()

    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "database": "connected" if db_healthy else "disconnected",
        "version": "1.0.0"
    }


# Include routers
from src.api.routers import routes, costs, search, info

app.include_router(routes.router, prefix="/api", tags=["Routing"])
app.include_router(costs.router, prefix="/api", tags=["Costs"])
app.include_router(search.router, prefix="/api", tags=["Search"])
app.include_router(info.router, prefix="/api", tags=["Information"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
        log_level=settings.LOG_LEVEL.lower()
    )
