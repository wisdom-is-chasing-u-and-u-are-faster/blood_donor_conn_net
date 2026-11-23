"""Unit tests for database initialization and schema configuration."""
import os
import sqlite3
import pytest
from unittest.mock import patch
from db.init_db import init_database


def test_init_database_creates_tables(tmp_path):
    """Verifies that the database initialization script correctly creates all expected tables.

    test_id: db__unit__001
    target: db/init_db.py::init_database
    requirement_id: no requirement
    ac_ids: none
    """
    db_file = tmp_path / "database.db"

    # Call init_database with default and explicit parameters
    init_database(str(db_file))

    assert db_file.exists(), f"Database file '{db_file.name}' was not created."

    # Verify tables created
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()

    expected_tables = ["users", "donors", "demands", "alerts", "audit_logs", "donor_commitments"]
    for t in expected_tables:
        assert t in tables, f"Expected table '{t}' missing from database."


def test_init_database_default_creates_database_db(tmp_path, monkeypatch):
    """Verifies that init_database without parameters creates database.db in cwd."""
    monkeypatch.chdir(tmp_path)
    init_database()
    assert (tmp_path / "database.db").exists() or (tmp_path / "bdcn.db").exists()
