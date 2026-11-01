"""Protected record management routes.

Enforces server-side authentication and backend record ownership.
"""

import sqlite3
from fastapi import APIRouter, Depends, Request
from target_app.auth import get_current_principal
from target_app.database import get_db
from target_app.models import RecordResponse, RecordUpdateRequest
from target_app.service import read_record_service, update_record_service


router = APIRouter(prefix="/records", tags=["Records"])


@router.get("/{record_id}", response_model=RecordResponse)
def read_record(
    record_id: str,
    request: Request,
    principal_id: str = Depends(get_current_principal),
    conn: sqlite3.Connection = Depends(get_db),
) -> RecordResponse:
    """Read a private record owned by the authenticated caller.

    Returns 401 if unauthenticated, 403 if unauthorized, 404 if record not found.
    """
    request_id = getattr(request.state, "request_id", "req_unknown")
    return read_record_service(
        conn,
        principal_id=principal_id,
        record_id=record_id,
        request_id=request_id,
    )


@router.put("/{record_id}", response_model=RecordResponse)
def update_record(
    record_id: str,
    update_data: RecordUpdateRequest,
    request: Request,
    principal_id: str = Depends(get_current_principal),
    conn: sqlite3.Connection = Depends(get_db),
) -> RecordResponse:
    """Modify a private record owned by the authenticated caller.

    Ownership cannot be altered. Empty update requests and extra fields are rejected.
    Returns 401 if unauthenticated, 403 if unauthorized, 404 if record not found.
    """
    request_id = getattr(request.state, "request_id", "req_unknown")
    return update_record_service(
        conn,
        principal_id=principal_id,
        record_id=record_id,
        update_data=update_data,
        request_id=request_id,
    )

