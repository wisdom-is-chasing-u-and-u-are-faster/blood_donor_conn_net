import pytest
import sqlite3
from db.init_db import get_db_connection, reset_database


@pytest.fixture(autouse=True)
def setup_db():
    conn = reset_database()
    yield conn


def test_database_tables_exist(setup_db):
    """Test that all core BDCN relational tables exist."""
    conn = setup_db
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r[0] for r in cursor.fetchall()]

    assert "clinical_facilities" in tables
    assert "inventory_blood_units" in tables
    assert "dispatch_emergency_requests" in tables
    assert "donor_profiles" in tables
    assert "audit_hipaa_ledger" in tables


def test_seed_data_populated(setup_db):
    """Test that initial baseline seed data is loaded."""
    conn = setup_db
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM clinical_facilities;")
    assert cursor.fetchone()[0] >= 3

    cursor.execute("SELECT COUNT(*) FROM inventory_blood_units;")
    assert cursor.fetchone()[0] >= 10

    cursor.execute("SELECT COUNT(*) FROM donor_profiles;")
    assert cursor.fetchone()[0] >= 5

    cursor.execute("SELECT COUNT(*) FROM audit_hipaa_ledger;")
    assert cursor.fetchone()[0] >= 1
