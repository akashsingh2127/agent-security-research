"""Deterministic synthetic dataset seeder for the target application.

Creates initial synthetic users and private records. Idempotent across multiple runs.
"""

import sqlite3
from datetime import datetime, timezone


SYNTHETIC_USERS = [
    {
        "user_id": "user_a",
        "username": "alice_tenant_a",
        "created_at": "2026-01-01T00:00:00Z",
    },
    {
        "user_id": "user_b",
        "username": "bob_tenant_b",
        "created_at": "2026-01-01T00:00:00Z",
    },
    {
        "user_id": "user_c",
        "username": "carol_tenant_c",
        "created_at": "2026-01-01T00:00:00Z",
    },
]

SYNTHETIC_RECORDS = [
    {
        "record_id": "rec_a_001",
        "owner_id": "user_a",
        "title": "Project Alpha Architecture",
        "content": "Confidential architecture draft for User A.",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
    },
    {
        "record_id": "rec_b_001",
        "owner_id": "user_b",
        "title": "Quarterly Financial Ledger",
        "content": "CONFIDENTIAL_CANARY_USER_B_DATA_42",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
    },
    {
        "record_id": "rec_c_001",
        "owner_id": "user_c",
        "title": "System Baseline Inventory",
        "content": "Baseline system configurations for User C.",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
    },
]


def seed_database(conn: sqlite3.Connection) -> None:
    """Seed the database with deterministic synthetic data.

    Idempotent: Re-running does not duplicate users or records.
    """
    with conn:
        for user in SYNTHETIC_USERS:
            conn.execute(
                """
                INSERT OR IGNORE INTO users (user_id, username, created_at)
                VALUES (?, ?, ?)
                """,
                (user["user_id"], user["username"], user["created_at"]),
            )

        for record in SYNTHETIC_RECORDS:
            conn.execute(
                """
                INSERT OR IGNORE INTO records (record_id, owner_id, title, content, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    record["record_id"],
                    record["owner_id"],
                    record["title"],
                    record["content"],
                    record["created_at"],
                    record["updated_at"],
                ),
            )

