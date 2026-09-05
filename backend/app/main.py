from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import ALLOWED_ORIGINS
from app.database import init_db, SessionLocal
from app.seed.seed_data import seed_database
from app.api import (
    health,
    orders,
    forecasts,
    events,
    adapters,
    experiments,
    failures,
    changes,
    audit,
    rollback,
    systems,
    validation
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables
    init_db()
    # Seed initial database
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="Integration Control Tower API",
    description="Enterprise Canonical Event Decoupling Gateway for Orders and Forecasts with Multi-Supplier Adapters.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers with /api prefix
app.include_router(health.router, prefix="/api")
app.include_router(orders.router, prefix="/api")
app.include_router(forecasts.router, prefix="/api")
app.include_router(events.router, prefix="/api")
app.include_router(adapters.router, prefix="/api")
app.include_router(experiments.router, prefix="/api")
app.include_router(failures.router, prefix="/api")
app.include_router(changes.router, prefix="/api")
app.include_router(audit.router, prefix="/api")
app.include_router(rollback.router, prefix="/api")
app.include_router(systems.router, prefix="/api")
app.include_router(validation.router, prefix="/api")


@app.get("/")
def root():
    return {
        "app": "Integration Control Tower",
        "description": "Manufacturer Exchanging Orders and Forecasts with Suppliers",
        "documentation": "/docs",
        "health": "/api/health"
    }
