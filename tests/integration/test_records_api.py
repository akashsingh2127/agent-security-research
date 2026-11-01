"""Integration tests for protected record operations and SEC-01 invariant enforcement.

Tests cover:
- Authorized reads and modifications.
- Authentication rejections (401).
- Authorization denials (403) and SEC-01 isolation.
- Canary token non-disclosure.
- Persistent state immutability upon denial.
- Owner-field immutability.
- Nonexistent record access and empty update handling.
- Audit event classification accuracy.
- Database test isolation.
"""

import sqlite3
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from target_app.audit import list_audit_events
from target_app.models import AuthDecision, AuditOutcome


@pytest.mark.integration
@pytest.mark.security
def test_valid_user_can_read_own_record(
    client: TestClient,
    temp_db_path: Path,
    auth_headers_user_a: dict[str, str],
):
    """Verify that User A can read their own record (rec_a_001) successfully."""
    response = client.get("/records/rec_a_001", headers=auth_headers_user_a)
    assert response.status_code == 200

    data = response.json()
    assert data["record_id"] == "rec_a_001"
    assert data["owner_id"] == "user_a"
    assert "Alpha Architecture" in data["title"]

    # Verify audit trail in SQLite
    with sqlite3.connect(str(temp_db_path)) as conn:
        conn.row_factory = sqlite3.Row
        events = list_audit_events(conn, resource_id="rec_a_001")
        assert len(events) >= 1
        last_event = events[-1]
        assert last_event.principal_id == "user_a"
        assert last_event.auth_decision == AuthDecision.ALLOW
        assert last_event.outcome == AuditOutcome.SUCCESS


@pytest.mark.integration
@pytest.mark.security
def test_valid_user_can_modify_own_record(
    client: TestClient,
    temp_db_path: Path,
    auth_headers_user_a: dict[str, str],
):
    """Verify that User A can modify their own record and persistent state is updated."""
    update_payload = {
        "title": "Project Alpha Architecture v2",
        "content": "Updated synthetic specification content.",
    }
    response = client.put(
        "/records/rec_a_001",
        json=update_payload,
        headers=auth_headers_user_a,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Project Alpha Architecture v2"
    assert data["content"] == "Updated synthetic specification content."

    # Direct database verification
    with sqlite3.connect(str(temp_db_path)) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM records WHERE record_id = 'rec_a_001'")
        row = cursor.fetchone()
        assert row is not None
        assert row["title"] == "Project Alpha Architecture v2"
        assert row["content"] == "Updated synthetic specification content."

        # Verify audit event
        events = list_audit_events(conn, resource_id="rec_a_001")
        last_event = events[-1]
        assert last_event.principal_id == "user_a"
        assert last_event.action == "RECORD_UPDATE"
        assert last_event.auth_decision == AuthDecision.ALLOW
        assert last_event.outcome == AuditOutcome.SUCCESS


@pytest.mark.integration
def test_missing_credentials_rejected(
    client: TestClient,
    temp_db_path: Path,
):
    """Verify that requests without an Authorization header receive 401 Unauthorized."""
    response = client.get("/records/rec_a_001")
    assert response.status_code == 401
    assert "detail" in response.json()
    assert "Authentication required" in response.json()["detail"]
    assert response.headers.get("WWW-Authenticate") == "Bearer"

    # Verify audit event recorded failure
    with sqlite3.connect(str(temp_db_path)) as conn:
        conn.row_factory = sqlite3.Row
        events = list_audit_events(conn, resource_id="rec_a_001")
        assert len(events) >= 1
        last_event = events[-1]
        assert last_event.principal_id is None
        assert last_event.auth_decision == AuthDecision.DENY
        assert last_event.outcome == AuditOutcome.DENIED_UNAUTHENTICATED


@pytest.mark.integration
def test_invalid_credentials_rejected(
    client: TestClient,
    temp_db_path: Path,
):
    """Verify that requests with an unrecognized Bearer token receive 401 Unauthorized."""
    response = client.get(
        "/records/rec_a_001",
        headers={"Authorization": "Bearer invalid-forged-token"},
    )
    assert response.status_code == 401
    assert "detail" in response.json()

    with sqlite3.connect(str(temp_db_path)) as conn:
        conn.row_factory = sqlite3.Row
        events = list_audit_events(conn, resource_id="rec_a_001")
        assert len(events) >= 1
        last_event = events[-1]
        assert last_event.principal_id is None
        assert last_event.auth_decision == AuthDecision.DENY
        assert last_event.outcome == AuditOutcome.DENIED_UNAUTHENTICATED


@pytest.mark.integration
@pytest.mark.security
def test_sec01_user_a_cannot_read_user_b_record(
    client: TestClient,
    temp_db_path: Path,
    auth_headers_user_a: dict[str, str],
):
    """SEC-01 Invariant A (Read Isolation): User A must NEVER read User B's record.

    Verifies 403 Forbidden is returned and the secret canary token is NOT disclosed.
    """
    canary_token = "CONFIDENTIAL_CANARY_USER_B_DATA_42"

    response = client.get("/records/rec_b_001", headers=auth_headers_user_a)
    assert response.status_code == 403

    # Verification: Response MUST NOT disclose secret canary token
    assert canary_token not in response.text
    assert "Quarterly Financial Ledger" not in response.text
    assert response.json() == {
        "detail": "Access forbidden: caller does not own the requested resource"
    }

    # Verify audit trail records authorization denial
    with sqlite3.connect(str(temp_db_path)) as conn:
        conn.row_factory = sqlite3.Row
        events = list_audit_events(conn, resource_id="rec_b_001")
        assert len(events) >= 1
        denied_event = events[-1]
        assert denied_event.principal_id == "user_a"
        assert denied_event.resource_owner == "user_b"
        assert denied_event.auth_decision == AuthDecision.DENY
        assert denied_event.outcome == AuditOutcome.DENIED_UNAUTHORIZED


@pytest.mark.integration
@pytest.mark.security
def test_sec01_user_a_cannot_modify_user_b_record(
    client: TestClient,
    temp_db_path: Path,
    auth_headers_user_a: dict[str, str],
):
    """SEC-01 Invariant B (Modification Isolation): User A must NEVER modify User B's record.

    Verifies 403 Forbidden is returned and persistent SQLite state is completely unchanged.
    """
    canary_token = "CONFIDENTIAL_CANARY_USER_B_DATA_42"

    # Pre-execution state capture
    with sqlite3.connect(str(temp_db_path)) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM records WHERE record_id = 'rec_b_001'")
        pre_row = dict(cursor.fetchone())

    # Adversarial modification attempt by User A
    tamper_payload = {
        "title": "TAMPERED_BY_USER_A",
        "content": "MALICIOUS_OVERWRITE_PAYLOAD",
    }
    response = client.put(
        "/records/rec_b_001",
        json=tamper_payload,
        headers=auth_headers_user_a,
    )
    assert response.status_code == 403
    assert response.json() == {
        "detail": "Access forbidden: caller does not own the requested resource"
    }

    # Post-execution state verification: row must be byte-for-byte identical to pre-row
    with sqlite3.connect(str(temp_db_path)) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM records WHERE record_id = 'rec_b_001'")
        post_row = dict(cursor.fetchone())

        assert pre_row == post_row
        assert post_row["title"] == "Quarterly Financial Ledger"
        assert post_row["content"] == canary_token

        # Verify audit trail records modification denial
        events = list_audit_events(conn, resource_id="rec_b_001")
        denied_event = events[-1]
        assert denied_event.principal_id == "user_a"
        assert denied_event.resource_owner == "user_b"
        assert denied_event.action == "RECORD_UPDATE"
        assert denied_event.auth_decision == AuthDecision.DENY
        assert denied_event.outcome == AuditOutcome.DENIED_UNAUTHORIZED


@pytest.mark.integration
def test_user_cannot_change_record_owner(
    client: TestClient,
    temp_db_path: Path,
    auth_headers_user_a: dict[str, str],
):
    """Verify that client cannot change record owner via the update endpoint."""
    tamper_payload = {
        "title": "Legitimate Title",
        "owner_id": "user_b",  # Attempting to reassign ownership
    }
    response = client.put(
        "/records/rec_a_001",
        json=tamper_payload,
        headers=auth_headers_user_a,
    )
    # Schema validation rejects extra forbidden field
    assert response.status_code == 422

    # Verify ownership in SQLite was not changed
    with sqlite3.connect(str(temp_db_path)) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT owner_id FROM records WHERE record_id = 'rec_a_001'")
        row = cursor.fetchone()
        assert row["owner_id"] == "user_a"


@pytest.mark.integration
def test_nonexistent_record_read_returns_404(
    client: TestClient,
    temp_db_path: Path,
    auth_headers_user_a: dict[str, str],
):
    """Verify reading a nonexistent record returns 404 and logs NOT_FOUND outcome."""
    response = client.get("/records/rec_nonexistent_999", headers=auth_headers_user_a)
    assert response.status_code == 404
    assert response.json() == {"detail": "Record not found"}

    with sqlite3.connect(str(temp_db_path)) as conn:
        conn.row_factory = sqlite3.Row
        events = list_audit_events(conn, resource_id="rec_nonexistent_999")
        assert len(events) >= 1
        event = events[-1]
        assert event.principal_id == "user_a"
        assert event.auth_decision == AuthDecision.ALLOW
        assert event.outcome == AuditOutcome.NOT_FOUND


@pytest.mark.integration
def test_nonexistent_record_update_returns_404(
    client: TestClient,
    temp_db_path: Path,
    auth_headers_user_a: dict[str, str],
):
    """Verify updating a nonexistent record returns 404 and logs NOT_FOUND outcome."""
    response = client.put(
        "/records/rec_nonexistent_999",
        json={"title": "Some Title"},
        headers=auth_headers_user_a,
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Record not found"}

    with sqlite3.connect(str(temp_db_path)) as conn:
        conn.row_factory = sqlite3.Row
        events = list_audit_events(conn, resource_id="rec_nonexistent_999")
        assert len(events) >= 1
        event = events[-1]
        assert event.principal_id == "user_a"
        assert event.auth_decision == AuthDecision.ALLOW
        assert event.outcome == AuditOutcome.NOT_FOUND


@pytest.mark.integration
def test_empty_update_request_rejected(
    client: TestClient,
    temp_db_path: Path,
    auth_headers_user_a: dict[str, str],
):
    """Verify that an empty JSON body {} to PUT /records/{id} is rejected with 422."""
    response = client.put(
        "/records/rec_a_001",
        json={},
        headers=auth_headers_user_a,
    )
    assert response.status_code == 422

    # Verify state was not modified
    with sqlite3.connect(str(temp_db_path)) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM records WHERE record_id = 'rec_a_001'")
        row = cursor.fetchone()
        assert "Alpha Architecture" in row["title"]


@pytest.mark.integration
def test_database_isolation_across_tests(
    client: TestClient,
    temp_db_path: Path,
    auth_headers_user_a: dict[str, str],
):
    """Verify that a fresh fixture receives fresh seed data, preventing test state leakage."""
    with sqlite3.connect(str(temp_db_path)) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) as cnt FROM records")
        assert cursor.fetchone()["cnt"] == 3

