"""
ProGear Hiking API

Main FastAPI application with:
- Okta authentication
- Auth0 Token Vault integration
- Salesforce MCP tools
- Inventory MCP tools
- Azure AI Foundry agent orchestration
"""

import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.routers import chat, user, salesforce, inventory

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    logger.info("Starting ProGear Hiking API", debug=settings.debug)
    yield
    logger.info("Shutting down ProGear Hiking API")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="AI-powered assistant for managing sales, customers, and inventory",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred"},
    )


# Include routers
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(user.router, prefix="/api/user", tags=["User"])
app.include_router(salesforce.router, prefix="/api/salesforce", tags=["Salesforce"])
app.include_router(inventory.router, prefix="/api/inventory", tags=["Inventory"])


# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": "1.0.0",
    }


# Root redirect to docs
@app.get("/")
async def root():
    return {
        "message": "ProGear Hiking API",
        "docs": "/docs" if settings.debug else "Documentation disabled in production",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
