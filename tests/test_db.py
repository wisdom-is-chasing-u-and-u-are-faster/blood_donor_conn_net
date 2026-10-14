import sqlite3
from pathlib import Path


def test_db_schema_and_seed():
    db_path = ":memory:"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    schema_file = Path("db/schema.sql")
    assert schema_file.exists(), "db/schema.sql does not exist"
    cursor.executescript(schema_file.read_text(encoding="utf-8"))

    seed_file = Path("db/seed.sql")
    assert seed_file.exists(), "db/seed.sql does not exist"
    cursor.executescript(seed_file.read_text(encoding="utf-8"))

    # Verify tables
    cursor.execute("SELECT COUNT(*) FROM users")
    assert cursor.fetchone()[0] >= 3

    cursor.execute("SELECT COUNT(*) FROM donor_clusters")
    assert cursor.fetchone()[0] >= 4

    cursor.execute("SELECT COUNT(*) FROM achievements")
    assert cursor.fetchone()[0] >= 4

    cursor.execute("SELECT COUNT(*) FROM medical_documents")
    assert cursor.fetchone()[0] >= 2

    cursor.execute("SELECT COUNT(*) FROM blood_requests")
    assert cursor.fetchone()[0] >= 3

    cursor.execute("SELECT COUNT(*) FROM audit_logs")
    assert cursor.fetchone()[0] >= 3

    conn.close()
