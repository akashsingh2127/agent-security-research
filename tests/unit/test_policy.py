"""Unit tests for core authorization policy logic."""

import pytest
from target_app.service import AuthorizationError, verify_record_ownership


@pytest.mark.unit
def test_ownership_check_passes_when_principal_matches_owner():
    """Verify that verify_record_ownership succeeds when principal equals owner."""
    # Should not raise any exception
    verify_record_ownership(principal_id="user_a", record_owner_id="user_a")
    verify_record_ownership(principal_id="user_b", record_owner_id="user_b")


@pytest.mark.unit
def test_ownership_check_raises_authorization_error_on_mismatch():
    """Verify that verify_record_ownership raises AuthorizationError when principal != owner."""
    with pytest.raises(AuthorizationError) as exc_info:
        verify_record_ownership(principal_id="user_a", record_owner_id="user_b")

    assert "Ownership mismatch" in str(exc_info.value)
    assert "user_a" in str(exc_info.value)
    assert "user_b" in str(exc_info.value)


@pytest.mark.unit
def test_ownership_check_raises_for_empty_or_none_principal():
    """Verify that invalid principals fail authorization checks."""
    with pytest.raises(AuthorizationError):
        verify_record_ownership(principal_id="", record_owner_id="user_a")

