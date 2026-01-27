"""
Mini Payments API - Main Application

A production-style Mini Payments API for learning and portfolio purposes.
This is NOT a real payment gateway and should NOT be used for actual payments.

Features:
- User management (create, retrieve)
- Transaction management with FX conversion
- Static exchange rates for demo purposes
- Idempotent transaction creation
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader

from app.core.config import settings
from app.db.session import create_tables
from app.api.routes_users import router as users_router
from app.api.routes_transactions import router as transactions_router
from app.api.routes_transactions import user_transactions_router


# API Key security (simple auth for demo)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Depends(api_key_header)) -> str:
    """
    Verify the API key from the X-API-Key header.
    For demo purposes, uses a simple static key comparison.
    """
    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return api_key


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan handler.
    Creates database tables on startup.
    """
    # Startup: create tables
    create_tables()
    yield
    # Shutdown: cleanup if needed


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="""
## Mini Payments API

A demonstration backend API for payment transactions with FX conversion.

### Features
- **User Management**: Create and retrieve users
- **Transaction Management**: Create transactions with automatic currency conversion
- **FX Conversion**: Static exchange rates for USD, EUR, INR, GBP
- **Idempotency**: Prevent duplicate transactions with idempotency keys

### ⚠️ Disclaimer
This is a **learning/portfolio project** and does NOT process real payments.
Not compliant with PCI-DSS or any banking regulations.

### Authentication
Use the API key `demo-api-key-12345` in the `X-API-Key` header.
    """,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with API key authentication
app.include_router(
    users_router,
    dependencies=[Depends(verify_api_key)]
)
app.include_router(
    transactions_router,
    dependencies=[Depends(verify_api_key)]
)
app.include_router(
    user_transactions_router,
    dependencies=[Depends(verify_api_key)]
)


@app.get("/", tags=["Health"])
async def root() -> dict[str, str]:
    """Root endpoint - API health check."""
    return {
        "message": "Mini Payments API is running",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint for monitoring."""
    return {"status": "healthy"}
