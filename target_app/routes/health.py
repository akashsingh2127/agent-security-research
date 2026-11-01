"""Health check endpoint."""

import sqlite3
from fastapi import APIRouter, Depends, HTTPException, status
from target_app.database import get_db
from target_app.models import HealthResponse


router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def health_check(conn: sqlite3.Connection = Depends(get_db)) -> HealthResponse:
    """Verify application health and database connectivity."""
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        return HealthResponse(status="ok", database="connected")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failure",
        ) from exc

