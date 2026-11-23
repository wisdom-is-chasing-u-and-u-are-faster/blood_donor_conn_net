"""Database initialization script for BDCN local environment."""
import os
import sqlite3


def find_schema_path():
    """Locate schema.sql across various execution environments and working directories."""
    candidates = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "schema.sql"),
        os.path.join(os.getcwd(), "db", "schema.sql"),
        os.path.join(os.getcwd(), "schema.sql"),
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")


def find_seed_path():
    """Locate seed.sql across various execution environments and working directories."""
    candidates = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "seed.sql"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "seed.sql"),
        os.path.join(os.getcwd(), "db", "seed.sql"),
        os.path.join(os.getcwd(), "seed.sql"),
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "seed.sql")


def init_database(db_path: str = None):
    """Initializes the database.

    Defaults to database.db (or DATABASE_PATH env var) to support QA and local testing environments.
    """
    if db_path is None:
        db_path = os.environ.get("DATABASE_PATH") or "database.db"

    schema_path = find_schema_path()
    seed_path = find_seed_path()

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

    # If initializing database.db, create a bdcn.db symlink/copy as well for compatibility
    try:
        dirname = os.path.dirname(db_path)
        base = os.path.basename(db_path)
        if base == "database.db":
            alt_path = os.path.join(dirname, "bdcn.db") if dirname else "bdcn.db"
            if not os.path.exists(alt_path):
                import shutil
                shutil.copyfile(db_path, alt_path)
        elif base == "bdcn.db":
            alt_path = os.path.join(dirname, "database.db") if dirname else "database.db"
            if not os.path.exists(alt_path):
                import shutil
                shutil.copyfile(db_path, alt_path)
    except Exception:
        pass

    print("Database initialized successfully.")


if __name__ == "__main__":
    init_database()
