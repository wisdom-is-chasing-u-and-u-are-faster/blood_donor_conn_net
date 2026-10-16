import os
import sqlite3
from pathlib import Path

DB_FILE = os.environ.get("DATABASE_URL", "sqlite:///quantum_leap.db").replace("sqlite:///", "")


def get_db_connection():
    conn = sqlite3.connect(DB_FILE, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def init_database(reset=False):
    schema_path = Path(__file__).parent / "schema.sql"
    seed_path = Path(__file__).parent / "seed.sql"

    conn = get_db_connection()
    cursor = conn.cursor()

    if reset:
        cursor.executescript("""
            DROP TABLE IF EXISTS contact_messages;
            DROP TABLE IF EXISTS transfers;
            DROP TABLE IF EXISTS transactions;
            DROP TABLE IF EXISTS accounts;
            DROP TABLE IF EXISTS users;
        """)

    if schema_path.exists():
        with open(schema_path, "r", encoding="utf-8") as f:
            cursor.executescript(f.read())

    if seed_path.exists():
        with open(seed_path, "r", encoding="utf-8") as f:
            cursor.executescript(f.read())

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_database()
    print("Database initialized successfully at", DB_FILE)
