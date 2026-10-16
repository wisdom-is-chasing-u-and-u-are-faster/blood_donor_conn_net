"""
Database initialization module for BDCN platform.
Executes schema.sql and seed.sql using SQLite (or configured DATABASE_URL).
"""
import sqlite3
from pathlib import Path


def get_db_path():
    db_dir = Path(__file__).resolve().parent
    db_file = db_dir / "bdcn.db"
    return str(db_file)


def get_connection():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Initializes the database schema and default seeds."""
    db_dir = Path(__file__).resolve().parent
    schema_file = db_dir / "schema.sql"
    seed_file = db_dir / "seed.sql"

    conn = get_connection()
    try:
        with conn:
            if schema_file.exists():
                conn.executescript(schema_file.read_text(encoding="utf-8"))
            if seed_file.exists():
                conn.executescript(seed_file.read_text(encoding="utf-8"))
    finally:
        conn.close()


if __name__ == "__main__":
    init_database()
    print("Database initialized successfully at", get_db_path())
