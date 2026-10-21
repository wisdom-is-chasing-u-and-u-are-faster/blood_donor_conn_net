import sqlite3
from db.init_db import init_database


def test_database_initialization(tmp_path):
    test_db = tmp_path / "test.db"
    assert init_database(str(test_db)) is True

    conn = sqlite3.connect(str(test_db))
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM donors")
    donor_count = cursor.fetchone()[0]
    assert donor_count >= 4

    cursor.execute("SELECT COUNT(*) FROM connection_requests")
    request_count = cursor.fetchone()[0]
    assert request_count >= 3

    cursor.execute("SELECT COUNT(*) FROM hotspots")
    hotspot_count = cursor.fetchone()[0]
    assert hotspot_count >= 3

    conn.close()
