"""Database initialization script for BDCN local environment."""
import os
import sqlite3


def init_database(db_path: str = "bdcn.db"):
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    seed_path = os.path.join(os.path.dirname(__file__), "seed.sql")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    if os.path.exists(schema_path):
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()
            # Convert Postgres SERIAL to SQLite INTEGER PRIMARY KEY AUTOINCREMENT
            schema_sql = schema_sql.replace("SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")
            schema_sql = schema_sql.replace("TIMESTAMP DEFAULT CURRENT_TIMESTAMP", "DATETIME DEFAULT CURRENT_TIMESTAMP")
            cursor.executescript(schema_sql)

    if os.path.exists(seed_path):
        with open(seed_path, "r", encoding="utf-8") as f:
            seed_sql = f.read()
            try:
                cursor.executescript(seed_sql)
            except Exception as e:
                print(f"Seed script notice: {e}")

    conn.commit()
    conn.close()
    print("Database initialized successfully.")


if __name__ == "__main__":
    init_database()
