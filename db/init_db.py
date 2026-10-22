import sqlite3
import os

DB_PATH = os.environ.get("DATABASE_PATH", "blood_donor_network.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")
SEED_PATH = os.path.join(os.path.dirname(__file__), "seed.sql")


def init_database(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    if os.path.exists(SCHEMA_PATH):
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            cursor.executescript(f.read())
    if os.path.exists(SEED_PATH):
        with open(SEED_PATH, "r", encoding="utf-8") as f:
            cursor.executescript(f.read())
    conn.commit()
    conn.close()
    return True


if __name__ == "__main__":
    init_database()
    print("Database initialized successfully.")
