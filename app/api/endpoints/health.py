"""Endpoints de health check."""
from fastapi import APIRouter
from app.api.models import HealthResponse
from app.core.config import settings
from app.db.session import check_db_connection
import time

router = APIRouter()

# Timestamp de início
start_time = time.time()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check do serviço."""
    db_connected = await check_db_connection()
    uptime = time.time() - start_time
    
    # Define status
    if not db_connected:
        status = "degraded"
    else:
        status = "healthy"
    
    return HealthResponse(
        status=status,
        version=settings.app_version,
        uptime_seconds=round(uptime, 2),
        database_connected=db_connected
    )


@router.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health"
    }
