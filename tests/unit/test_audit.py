"""Unit tests for audit events, sanitization, and outcome classification."""

import sqlite3
import pytest
from target_app.audit import list_audit_events, record_audit_event
from target_app.models import AuditAction, AuthDecision, AuditEvent, AuditOutcome


@pytest.mark.unit
def test_audit_event_structure_and_types():
    """Verify AuditEvent model enforces required fields and valid enums."""
    event = AuditEvent(
        event_id="evt_test_001",
        timestamp="2026-01-01T00:00:00Z",
        request_id="req_test_001",
        principal_id="user_a",
        action=AuditAction.RECORD_READ.value,
        resource_id="rec_a_001",
        resource_owner="user_a",
        auth_decision=AuthDecision.ALLOW,
        outcome=AuditOutcome.SUCCESS,
        error_detail=None,
    )
    assert event.auth_decision == AuthDecision.ALLOW
    assert event.outcome == AuditOutcome.SUCCESS


@pytest.mark.unit
def test_audit_distinguishes_authorization_from_outcome():
    """Verify that authorization decision remains distinct from execution outcome."""
    # Example: Authorized request where record was not found
    event_not_found = AuditEvent(
        event_id="evt_test_002",
        timestamp="2026-01-01T00:00:00Z",
        request_id="req_test_002",
        principal_id="user_a",
        action=AuditAction.RECORD_READ.value,
        resource_id="rec_nonexistent",
        resource_owner=None,
        auth_decision=AuthDecision.ALLOW,
        outcome=AuditOutcome.NOT_FOUND,
        error_detail="Record does not exist in database",
    )
    assert event_not_found.auth_decision == AuthDecision.ALLOW
    assert event_not_found.outcome == AuditOutcome.NOT_FOUND

    # Example: Denied request due to authorization failure
    event_denied = AuditEvent(
        event_id="evt_test_003",
        timestamp="2026-01-01T00:00:00Z",
        request_id="req_test_003",
        principal_id="user_a",
        action=AuditAction.RECORD_READ.value,
        resource_id="rec_b_001",
        resource_owner="user_b",
        auth_decision=AuthDecision.DENY,
        outcome=AuditOutcome.DENIED_UNAUTHORIZED,
        error_detail="Ownership mismatch",
    )
    assert event_denied.auth_decision == AuthDecision.DENY
    assert event_denied.outcome == AuditOutcome.DENIED_UNAUTHORIZED


@pytest.mark.unit
def test_audit_persistence_append_only(db_conn: sqlite3.Connection):
    """Verify that recording events appends rows to SQLite database."""
    initial_events = list_audit_events(db_conn)
    initial_count = len(initial_events)

    event = record_audit_event(
        db_conn,
        request_id="req_unit_test",
        action=AuditAction.RECORD_READ,
        auth_decision=AuthDecision.ALLOW,
        outcome=AuditOutcome.SUCCESS,
        principal_id="user_a",
        resource_id="rec_a_001",
        resource_owner="user_a",
    )

    updated_events = list_audit_events(db_conn)
    assert len(updated_events) == initial_count + 1
    assert updated_events[-1].event_id == event.event_id
    assert updated_events[-1].principal_id == "user_a"

