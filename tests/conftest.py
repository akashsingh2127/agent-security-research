"""Pytest fixtures providing isolated temporary databases and test clients."""

import sqlite3
from collections.abc import Generator
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from target_app.app import create_app
from target_app.database import get_connection, get_db, init_db
from target_app.seed import seed_database


@pytest.fixture
def temp_db_path(tmp_path: Path) -> Path:
    """Provide a path to a unique temporary SQLite database file for test isolation."""
    db_file = tmp_path / "test_target.db"
    return db_file


@pytest.fixture
def db_conn(temp_db_path: Path) -> Generator[sqlite3.Connection, None, None]:
    """Provide an active connection to an initialized and seeded temporary database."""
    init_db(temp_db_path)
    conn = get_connection(temp_db_path)
    seed_database(conn)
    try:
        yield conn
    finally:
        conn.close()


@pytest.fixture
def client(temp_db_path: Path) -> Generator[TestClient, None, None]:
    """Provide a FastAPI TestClient bound to an isolated temporary database."""
    init_db(temp_db_path)
    with get_connection(temp_db_path) as init_conn:
        seed_database(init_conn)

    app = create_app(db_path=str(temp_db_path))

    def override_get_db() -> Generator[sqlite3.Connection, None, None]:
        conn = get_connection(temp_db_path)
        try:
            yield conn
        finally:
            conn.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers_user_a() -> dict[str, str]:
    """Valid Bearer authorization header for User A."""
    return {"Authorization": "Bearer test-token-user-a"}


@pytest.fixture
def auth_headers_user_b() -> dict[str, str]:
    """Valid Bearer authorization header for User B."""
    return {"Authorization": "Bearer test-token-user-b"}


@pytest.fixture
def auth_headers_user_c() -> dict[str, str]:
    """Valid Bearer authorization header for User C."""
    return {"Authorization": "Bearer test-token-user-c"}

