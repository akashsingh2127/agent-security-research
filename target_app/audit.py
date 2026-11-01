"""Audit event persistence and retrieval.

This module provides an append-only interface for recording security-relevant events.
No update or delete operations are exposed.

Limitations:
Application-generated audit logs provide internal evidence of execution.
Because SQLite is an embedded file, host-level tamper resistance is not guaranteed.
The independent security_engine will corroborate audit evidence with persistent
state deltas in later milestones.
"""

import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Optional
from target_app.models import AuditAction, AuthDecision, AuditEvent, AuditOutcome


def record_audit_event(
    conn: sqlite3.Connection,
    *,
    request_id: str,
    action: str | AuditAction,
    auth_decision: AuthDecision,
    outcome: AuditOutcome,
    principal_id: Optional[str] = None,
    resource_id: Optional[str] = None,
    resource_owner: Optional[str] = None,
    error_detail: Optional[str] = None,
) -> AuditEvent:
    """Persist an append-only audit event to SQLite.

    Credentials, bearer tokens, and private record contents are NEVER recorded.
    """
    event_id = f"evt_{uuid.uuid4().hex}"
    now_utc = datetime.now(timezone.utc).isoformat()
    action_str = action.value if isinstance(action, AuditAction) else str(action)

    event = AuditEvent(
        event_id=event_id,
        timestamp=now_utc,
        request_id=request_id,
        principal_id=principal_id,
        action=action_str,
        resource_id=resource_id,
        resource_owner=resource_owner,
        auth_decision=auth_decision,
        outcome=outcome,
        error_detail=error_detail,
    )

    with conn:
        conn.execute(
            """
            INSERT INTO audit_events (
                event_id, timestamp, request_id, principal_id, action,
                resource_id, resource_owner, auth_decision, outcome, error_detail
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.event_id,
                event.timestamp,
                event.request_id,
                event.principal_id,
                event.action,
                event.resource_id,
                event.resource_owner,
                event.auth_decision.value,
                event.outcome.value,
                event.error_detail,
            ),
        )

    return event


def list_audit_events(
    conn: sqlite3.Connection,
    *,
    resource_id: Optional[str] = None,
    principal_id: Optional[str] = None,
) -> list[AuditEvent]:
    """Retrieve audit events for test verification and harness auditing.

    Read-only: No mutative or destructive methods are exposed.
    """
    query = "SELECT * FROM audit_events WHERE 1=1"
    params: list[str] = []

    if resource_id:
        query += " AND resource_id = ?"
        params.append(resource_id)
    if principal_id:
        query += " AND principal_id = ?"
        params.append(principal_id)

    query += " ORDER BY timestamp ASC"

    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()

    return [
        AuditEvent(
            event_id=row["event_id"],
            timestamp=row["timestamp"],
            request_id=row["request_id"],
            principal_id=row["principal_id"],
            action=row["action"],
            resource_id=row["resource_id"],
            resource_owner=row["resource_owner"],
            auth_decision=AuthDecision(row["auth_decision"]),
            outcome=AuditOutcome(row["outcome"]),
            error_detail=row["error_detail"],
        )
        for row in rows
    ]
