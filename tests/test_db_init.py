"""
Tests for DB initialization and schema creation.
"""
from db.init_db import init_database, get_connection


def test_database_initialization():
    """Verify that schema and seed data are created properly."""
    init_database()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM emergency_requisitions")
    req_count = cursor.fetchone()[0]
    assert req_count >= 1

    cursor.execute("SELECT COUNT(*) FROM digital_check_in_passes")
    pass_count = cursor.fetchone()[0]
    assert pass_count >= 1

    conn.close()
