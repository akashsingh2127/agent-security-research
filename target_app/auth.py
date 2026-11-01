"""Authentication provider for local test and research harness.

NOTICE:
This authentication mechanism is explicitly scoped to local evaluation and testing.
It uses a deterministic, pre-shared token-to-principal mapping.
It is NOT production-ready (no password hashing, JWT signing, or OAuth2 workflows).
Never trust client-supplied user IDs in bodies, queries, or arbitrary headers.
"""

import sqlite3
from typing import Optional
from fastapi import Depends, Header, HTTPException, Request, status
from target_app.audit import record_audit_event
from target_app.config import settings
from target_app.database import get_db
from target_app.models import AuditAction, AuthDecision, AuditOutcome


def get_current_principal(
    request: Request,
    authorization: Optional[str] = Header(default=None),
    conn: sqlite3.Connection = Depends(get_db),
) -> str:
    """Validate Bearer token and resolve server-side authenticated principal.

    Rejects missing or invalid credentials with HTTP 401.
    Never falls back to untrusted query params or body fields.
    Records an append-only audit event when authentication fails.
    """
    request_id = getattr(request.state, "request_id", "req_unknown")
    resource_id = request.path_params.get("record_id")
    action = AuditAction.RECORD_UPDATE if request.method in ("PUT", "PATCH") else AuditAction.RECORD_READ

    if not authorization:
        record_audit_event(
            conn,
            request_id=request_id,
            action=action,
            auth_decision=AuthDecision.DENY,
            outcome=AuditOutcome.DENIED_UNAUTHENTICATED,
            principal_id=None,
            resource_id=resource_id,
            error_detail="Missing Authorization header",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required: missing credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = authorization.strip().split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        record_audit_event(
            conn,
            request_id=request_id,
            action=action,
            auth_decision=AuthDecision.DENY,
            outcome=AuditOutcome.DENIED_UNAUTHENTICATED,
            principal_id=None,
            resource_id=resource_id,
            error_detail="Malformed Bearer token header format",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required: malformed authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]
    principal_id = settings.token_principal_map.get(token)

    if not principal_id:
        record_audit_event(
            conn,
            request_id=request_id,
            action=action,
            auth_decision=AuthDecision.DENY,
            outcome=AuditOutcome.DENIED_UNAUTHENTICATED,
            principal_id=None,
            resource_id=resource_id,
            error_detail="Unrecognized or invalid bearer token",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required: invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return principal_id

