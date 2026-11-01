"""Application business logic, authorization policy enforcement, and record CRUD.

Enforces strict backend ownership validation for all protected resources.
Ensures internal audit logs remain decoupled from client-facing error responses.
"""

import sqlite3
from datetime import datetime, timezone
from typing import Optional
from fastapi import HTTPException, status
from target_app.audit import record_audit_event
from target_app.models import (
    AuditAction,
    AuthDecision,
    AuditOutcome,
    RecordResponse,
    RecordUpdateRequest,
)


class AuthorizationError(Exception):
    """Raised when an authenticated principal attempts an unauthorized action."""
    def __init__(self, detail: str = "Access forbidden: caller does not own the requested resource"):
        super().__init__(detail)
        self.detail = detail


def verify_record_ownership(principal_id: str, record_owner_id: str) -> None:
    """Pure authorization policy check.

    Raises AuthorizationError if principal does not strictly match owner.
    """
    if principal_id != record_owner_id:
        raise AuthorizationError(
            f"Ownership mismatch: principal '{principal_id}' is not owner '{record_owner_id}'"
        )


def get_record_by_id(conn: sqlite3.Connection, record_id: str) -> Optional[sqlite3.Row]:
    """Retrieve raw database record by ID."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM records WHERE record_id = ?", (record_id,))
    return cursor.fetchone()


def read_record_service(
    conn: sqlite3.Connection,
    *,
    principal_id: str,
    record_id: str,
    request_id: str,
) -> RecordResponse:
    """Execute a protected read operation with strict ownership validation."""
    row = get_record_by_id(conn, record_id)

    if row is None:
        # Authorization decision is ALLOW because caller is authenticated and no ownership conflict exists.
        # Execution outcome is NOT_FOUND.
        record_audit_event(
            conn,
            request_id=request_id,
            action=AuditAction.RECORD_READ,
            auth_decision=AuthDecision.ALLOW,
            outcome=AuditOutcome.NOT_FOUND,
            principal_id=principal_id,
            resource_id=record_id,
            resource_owner=None,
            error_detail="Record does not exist in database",
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record not found",
        )

    record_owner = row["owner_id"]

    try:
        verify_record_ownership(principal_id, record_owner)
    except AuthorizationError:
        # Authorization denied: caller does not own the record.
        # Response contains only sanitized message; private record content is NOT disclosed.
        record_audit_event(
            conn,
            request_id=request_id,
            action=AuditAction.RECORD_READ,
            auth_decision=AuthDecision.DENY,
            outcome=AuditOutcome.DENIED_UNAUTHORIZED,
            principal_id=principal_id,
            resource_id=record_id,
            resource_owner=record_owner,
            error_detail=f"Principal '{principal_id}' denied read access to record owned by '{record_owner}'",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: caller does not own the requested resource",
        )

    # Authorized read succeeds
    record_audit_event(
        conn,
        request_id=request_id,
        action=AuditAction.RECORD_READ,
        auth_decision=AuthDecision.ALLOW,
        outcome=AuditOutcome.SUCCESS,
        principal_id=principal_id,
        resource_id=record_id,
        resource_owner=record_owner,
    )

    return RecordResponse(
        record_id=row["record_id"],
        owner_id=row["owner_id"],
        title=row["title"],
        content=row["content"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def update_record_service(
    conn: sqlite3.Connection,
    *,
    principal_id: str,
    record_id: str,
    update_data: RecordUpdateRequest,
    request_id: str,
) -> RecordResponse:
    """Execute a protected update operation with ownership validation.

    Ensures ownership cannot be modified, and denied updates leave state unchanged.
    """
    row = get_record_by_id(conn, record_id)

    if row is None:
        record_audit_event(
            conn,
            request_id=request_id,
            action=AuditAction.RECORD_UPDATE,
            auth_decision=AuthDecision.ALLOW,
            outcome=AuditOutcome.NOT_FOUND,
            principal_id=principal_id,
            resource_id=record_id,
            resource_owner=None,
            error_detail="Record does not exist in database",
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record not found",
        )

    record_owner = row["owner_id"]

    try:
        verify_record_ownership(principal_id, record_owner)
    except AuthorizationError:
        # Authorization denied: caller does not own the record.
        # Persistent state remains completely unchanged.
        record_audit_event(
            conn,
            request_id=request_id,
            action=AuditAction.RECORD_UPDATE,
            auth_decision=AuthDecision.DENY,
            outcome=AuditOutcome.DENIED_UNAUTHORIZED,
            principal_id=principal_id,
            resource_id=record_id,
            resource_owner=record_owner,
            error_detail=f"Principal '{principal_id}' denied modification of record owned by '{record_owner}'",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: caller does not own the requested resource",
        )

    # Ownership verified: apply validated updates (owner_id cannot be changed)
    new_title = update_data.title if update_data.title is not None else row["title"]
    new_content = update_data.content if update_data.content is not None else row["content"]
    now_utc = datetime.now(timezone.utc).isoformat()

    try:
        with conn:
            conn.execute(
                """
                UPDATE records
                SET title = ?, content = ?, updated_at = ?
                WHERE record_id = ? AND owner_id = ?
                """,
                (new_title, new_content, now_utc, record_id, record_owner),
            )

        record_audit_event(
            conn,
            request_id=request_id,
            action=AuditAction.RECORD_UPDATE,
            auth_decision=AuthDecision.ALLOW,
            outcome=AuditOutcome.SUCCESS,
            principal_id=principal_id,
            resource_id=record_id,
            resource_owner=record_owner,
        )
    except Exception as exc:
        record_audit_event(
            conn,
            request_id=request_id,
            action=AuditAction.RECORD_UPDATE,
            auth_decision=AuthDecision.ALLOW,
            outcome=AuditOutcome.ERROR,
            principal_id=principal_id,
            resource_id=record_id,
            resource_owner=record_owner,
            error_detail=f"Database execution error: {type(exc).__name__}",
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from exc

    updated_row = get_record_by_id(conn, record_id)
    assert updated_row is not None

    return RecordResponse(
        record_id=updated_row["record_id"],
        owner_id=updated_row["owner_id"],
        title=updated_row["title"],
        content=updated_row["content"],
        created_at=updated_row["created_at"],
        updated_at=updated_row["updated_at"],
    )

