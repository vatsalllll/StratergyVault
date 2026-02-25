"""
StrategyVault - AI-Powered Strategy Marketplace
Main FastAPI Application

Combines:
- Moon Dev RBI Agent: Strategy generation
- AgentQuant: Validation & regime detection
- Moon Dev Swarm: Multi-AI consensus rating
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.core.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    init_db()
    print("🚀 StrategyVault backend started")
    yield
    # Shutdown
    print("👋 StrategyVault backend stopped")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Powered Trading Strategy Marketplace",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint - health check."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "features": {
            "strategy_generation": "Moon Dev RBI Agent",
            "validation": "AgentQuant Walk-Forward",
            "rating": "Moon Dev Swarm Consensus",
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Import and include routers
from src.api.strategies import router as strategies_router
from src.api.marketplace import router as marketplace_router
from src.api.data import router as data_router

app.include_router(strategies_router, prefix="/api/v1/strategies", tags=["strategies"])
app.include_router(marketplace_router, prefix="/api/v1/marketplace", tags=["marketplace"])
app.include_router(data_router, prefix="/api/v1/data", tags=["data"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

