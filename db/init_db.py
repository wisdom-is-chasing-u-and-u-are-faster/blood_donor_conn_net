#!/usr/bin/env python3
"""
Initializes SQLite database with schema.sql and seed.sql for local development.
"""
import os
import sqlite3
from pathlib import Path


def init_database(db_path: str = "app.db"):
    current_dir = Path(__file__).parent
    schema_file = current_dir / "schema.sql"
    seed_file = current_dir / "seed.sql"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    if schema_file.exists():
        cursor.executescript(schema_file.read_text(encoding="utf-8"))

    if seed_file.exists():
        # Check if table already has rows before seeding to prevent duplicate key errors
        cursor.execute("SELECT count(*) FROM donors")
        count = cursor.fetchone()[0]
        if count == 0:
            cursor.executescript(seed_file.read_text(encoding="utf-8"))

    conn.commit()
    conn.close()
    print("Database initialized successfully.")


if __name__ == "__main__":
    db_file = os.environ.get("DATABASE_URL", "app.db").replace("sqlite:///", "")
    init_database(db_file)
