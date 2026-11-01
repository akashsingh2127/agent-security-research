"""Unit tests for Pydantic models, request validation, and field protection."""

import pytest
from pydantic import ValidationError
from target_app.models import RecordResponse, RecordUpdateRequest


@pytest.mark.unit
def test_record_update_valid_payload():
    """Verify that a valid update payload with title and content succeeds."""
    req = RecordUpdateRequest(title="Updated Title", content="Updated Content")
    assert req.title == "Updated Title"
    assert req.content == "Updated Content"


@pytest.mark.unit
def test_record_update_partial_payload():
    """Verify partial updates with only title or only content succeed."""
    req_title_only = RecordUpdateRequest(title="New Title")
    assert req_title_only.title == "New Title"
    assert req_title_only.content is None

    req_content_only = RecordUpdateRequest(content="New Content")
    assert req_content_only.title is None
    assert req_content_only.content == "New Content"


@pytest.mark.unit
def test_record_update_rejects_empty_payload():
    """Verify that empty update requests are rejected by schema validation."""
    with pytest.raises(ValidationError) as exc_info:
        RecordUpdateRequest()

    assert "Empty update request" in str(exc_info.value)


@pytest.mark.unit
def test_record_update_forbids_owner_id_tampering():
    """Verify that client attempts to modify owner_id are rejected by extra='forbid'."""
    with pytest.raises(ValidationError) as exc_info:
        RecordUpdateRequest.model_validate({"title": "Test", "owner_id": "user_b"})

    assert "extra_forbidden" in str(exc_info.value)


@pytest.mark.unit
def test_record_update_forbids_arbitrary_extra_fields():
    """Verify that extra unknown fields are rejected."""
    with pytest.raises(ValidationError) as exc_info:
        RecordUpdateRequest.model_validate({"title": "Test", "malicious_injection": "value"})

    assert "extra_forbidden" in str(exc_info.value)


@pytest.mark.unit
def test_record_response_model_validation():
    """Verify RecordResponse serializes valid database attributes."""
    data = {
        "record_id": "rec_001",
        "owner_id": "user_a",
        "title": "Secret Notes",
        "content": "Secret Content",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
    }
    resp = RecordResponse.model_validate(data)
    assert resp.record_id == "rec_001"
    assert resp.owner_id == "user_a"

