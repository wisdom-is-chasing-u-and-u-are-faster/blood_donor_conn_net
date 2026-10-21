"""
Database Initializer for Blood Donor Connection Network.
Executes ANSI SQL schema and baseline seeds against SQLite database.
"""
import os
import sqlite3
from pathlib import Path

DB_FILE = os.environ.get("DATABASE_PATH", "app.db")
BASE_DIR = Path(__file__).resolve().parent


def init_database(db_path=None):
    if db_path is None:
        db_path = DB_FILE

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    schema_file = BASE_DIR / "schema.sql"
    seed_file = BASE_DIR / "seed.sql"

    if schema_file.exists():
        with open(schema_file, "r", encoding="utf-8") as f:
            cursor.executescript(f.read())

    if seed_file.exists():
        with open(seed_file, "r", encoding="utf-8") as f:
            cursor.executescript(f.read())

    conn.commit()
    conn.close()
    return True


if __name__ == "__main__":
    init_database()
    print("Database initialized successfully.")
