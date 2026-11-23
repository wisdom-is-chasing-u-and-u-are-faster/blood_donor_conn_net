"""
test_donor_availability_db.py — Tests SQLite database persistence for ARCH-9522 schema and seed.
"""
import os
import sqlite3
import pytest
from db.init_db import init_database


@pytest.fixture
def test_db(tmp_path):
    db_file = str(tmp_path / "test_bdcn.db")
    init_database(db_file)
    yield db_file


def test_schema_donor_availability_columns(test_db):
    """Test donors table has availability_status and cooldown_until columns."""
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(donors)")
    columns = {row[1]: row[2] for row in cursor.fetchall()}
    assert "availability_status" in columns
    assert "cooldown_until" in columns
    conn.close()


def test_schema_donor_commitments_table(test_db):
    """Test donor_commitments table exists with uniqueness constraint."""
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(donor_commitments)")
    columns = {row[1]: row[2] for row in cursor.fetchall()}
    assert "request_id" in columns
    assert "donor_id" in columns
    assert "donor_username" in columns
    assert "anonymized_id" in columns
    assert "eta" in columns

    # Insert test commitment
    cursor.execute(
        "INSERT INTO donor_commitments (request_id, donor_id, donor_username, anonymized_id, eta) VALUES (1, 99, 'testuser', 'Donor #123456', 'Within 1 hour')"
    )
    conn.commit()

    # Attempt duplicate insert - must raise IntegrityError
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute(
            "INSERT INTO donor_commitments (request_id, donor_id, donor_username, anonymized_id, eta) VALUES (1, 99, 'testuser', 'Donor #123456', 'Within 1 hour')"
        )
        conn.commit()

    conn.close()
