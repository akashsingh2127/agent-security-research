"""Integration tests for the health check endpoint."""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_health_endpoint(client: TestClient):
    """Verify that GET /health returns 200 and database connected status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"
    assert "X-Request-ID" in response.headers

