import sqlite3
import os

DB_PATH = os.environ.get(
    "DATABASE_PATH",
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "bdcn.db"))


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    seed_path = os.path.join(os.path.dirname(__file__), "seed.sql")

    conn = get_db_connection()
    with conn:
        if os.path.exists(schema_path):
            with open(schema_path, "r", encoding="utf-8") as f:
                conn.executescript(f.read())
        if os.path.exists(seed_path):
            with open(seed_path, "r", encoding="utf-8") as f:
                conn.executescript(f.read())
    conn.close()


if __name__ == "__main__":
    init_database()
    print("Database initialized successfully at", DB_PATH)
