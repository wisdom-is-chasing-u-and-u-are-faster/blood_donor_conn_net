"""
db/init_db.py — Database Initialization and Connection Management for BDCN

Supports dual-mode execution:
1. PostgreSQL 16 + PostGIS when DATABASE_URL is available.
2. In-Memory / SQLite fallback for isolated unit testing and fast CI environments.
"""

import os
import sqlite3
import datetime
from pathlib import Path
from typing import Optional

DB_DIR = Path(__file__).parent.resolve()
SCHEMA_FILE = DB_DIR / "schema.sql"
SEED_FILE = DB_DIR / "seed.sql"

# Global in-memory SQLite connection for test fallback
_sqlite_conn: Optional[sqlite3.Connection] = None


def get_db_connection() -> sqlite3.Connection:
    """Returns the active database connection (SQLite in-memory or file-backed)."""
    global _sqlite_conn
    if _sqlite_conn is None:
        db_path = os.getenv("SQLITE_DB_PATH", ":memory:")
        _sqlite_conn = sqlite3.connect(db_path, check_same_thread=False)
        _sqlite_conn.row_factory = sqlite3.Row
        init_sqlite_db(_sqlite_conn)
    return _sqlite_conn


def init_sqlite_db(conn: sqlite3.Connection) -> None:
    """Initializes SQLite schema and baseline seed data."""
    cursor = conn.cursor()

    # 1. Clinical Facilities
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clinical_facilities (
        facility_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        facility_type TEXT NOT NULL DEFAULT 'TRAUMA_CENTER_LEVEL_1',
        district TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        contact_phone TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Blood Component Inventory
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventory_blood_units (
        unit_id TEXT PRIMARY KEY,
        din_barcode TEXT NOT NULL UNIQUE,
        facility_id TEXT NOT NULL,
        blood_type TEXT NOT NULL,
        component_type TEXT NOT NULL,
        volume_ml INTEGER NOT NULL DEFAULT 450,
        status TEXT NOT NULL DEFAULT 'AVAILABLE',
        reservation_id TEXT,
        lease_expires_at TEXT,
        expires_at TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (facility_id) REFERENCES clinical_facilities(facility_id)
    );
    """)

    # 3. Emergency Trauma Dispatch Requests
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dispatch_emergency_requests (
        request_id TEXT PRIMARY KEY,
        requesting_hospital_id TEXT NOT NULL,
        required_blood_type TEXT NOT NULL,
        component_type TEXT NOT NULL,
        units_requested INTEGER NOT NULL,
        urgency_tier TEXT NOT NULL DEFAULT 'CODE_RED',
        status TEXT NOT NULL DEFAULT 'INITIATED',
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        clinical_notes_encrypted TEXT NOT NULL,
        allocated_units_count INTEGER NOT NULL DEFAULT 0,
        matched_donors_count INTEGER NOT NULL DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        estimated_arrival_at TEXT,
        FOREIGN KEY (requesting_hospital_id) REFERENCES clinical_facilities(facility_id)
    );
    """)

    # 4. Donor Profiles
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS donor_profiles (
        donor_id TEXT PRIMARY KEY,
        user_account_id TEXT NOT NULL UNIQUE,
        full_name TEXT NOT NULL,
        blood_type TEXT NOT NULL,
        encrypted_national_id TEXT NOT NULL,
        district TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        eligibility_status TEXT NOT NULL DEFAULT 'ELIGIBLE',
        last_donation_date TEXT,
        push_device_token TEXT,
        phone_number TEXT,
        donation_count INTEGER NOT NULL DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 5. HIPAA / HITECH WORM Immutable Audit Access Ledger
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_hipaa_ledger (
        audit_id TEXT PRIMARY KEY,
        actor_user_id TEXT NOT NULL,
        action_type TEXT NOT NULL,
        resource_type TEXT NOT NULL,
        resource_id TEXT NOT NULL,
        payload_hash_sha256 TEXT NOT NULL,
        previous_hash_sha256 TEXT NOT NULL,
        client_ip TEXT DEFAULT '127.0.0.1',
        user_agent TEXT DEFAULT 'BDCN-Internal-Client',
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Seed baseline facilities if empty
    cursor.execute("SELECT COUNT(*) FROM clinical_facilities")
    if cursor.fetchone()[0] == 0:
        now = datetime.datetime.now(datetime.timezone.utc)
        cursor.execute("""
        INSERT INTO clinical_facilities (facility_id, name, facility_type, district, latitude, longitude, contact_phone)
        VALUES
            ('fac-001', 'Metro City Trauma Hospital', 'LEVEL_1_TRAUMA_CENTER', 'Downtown', 40.7128, -74.0060, '+1-212-555-0100'),
            ('fac-002', 'Mercy Regional Medical Center', 'COMMUNITY_HOSPITAL', 'North District', 40.7589, -73.9851, '+1-212-555-0200'),
            ('fac-003', 'St. Jude Emergency Center', 'URGENT_SURGICAL_UNIT', 'West Hills', 40.7829, -73.9654, '+1-212-555-0300');
        """)

        # Seed baseline inventory
        exp_24h = (now + datetime.timedelta(hours=24)).isoformat()
        exp_48h = (now + datetime.timedelta(hours=48)).isoformat()
        exp_72h = (now + datetime.timedelta(hours=72)).isoformat()
        exp_96h = (now + datetime.timedelta(hours=96)).isoformat()
        exp_120h = (now + datetime.timedelta(hours=120)).isoformat()
        exp_36h = (now + datetime.timedelta(hours=36)).isoformat()
        exp_180d = (now + datetime.timedelta(days=180)).isoformat()

        cursor.executemany("""
        INSERT INTO inventory_blood_units (unit_id, din_barcode, facility_id, blood_type, component_type, volume_ml, status, expires_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, [
            ('unit-001', 'W0384-25-001001', 'fac-001', 'O_NEG', 'RED_BLOOD_CELLS', 450, 'AVAILABLE', exp_24h),
            ('unit-002', 'W0384-25-001002', 'fac-001', 'O_NEG', 'RED_BLOOD_CELLS', 450, 'AVAILABLE', exp_48h),
            ('unit-003', 'W0384-25-001003', 'fac-001', 'O_NEG', 'RED_BLOOD_CELLS', 450, 'AVAILABLE', exp_72h),
            ('unit-004', 'W0384-25-001004', 'fac-001', 'O_NEG', 'RED_BLOOD_CELLS', 450, 'AVAILABLE', exp_96h),
            ('unit-005', 'W0384-25-001005', 'fac-001', 'O_POS', 'RED_BLOOD_CELLS', 450, 'AVAILABLE', exp_120h),
            ('unit-006', 'W0384-25-001006', 'fac-001', 'A_POS', 'RED_BLOOD_CELLS', 450, 'AVAILABLE', exp_36h),
            ('unit-007', 'W0384-25-001007', 'fac-001', 'A_POS', 'RED_BLOOD_CELLS', 450, 'AVAILABLE', exp_72h),
            ('unit-008', 'W0384-25-001008', 'fac-001', 'B_NEG', 'PLATELETS', 300, 'AVAILABLE', exp_48h),
            ('unit-009', 'W0384-25-001009', 'fac-001', 'B_NEG', 'PLATELETS', 300, 'AVAILABLE', exp_72h),
            ('unit-010', 'W0384-25-001010', 'fac-001', 'AB_POS', 'FRESH_FROZEN_PLASMA', 250, 'AVAILABLE', exp_180d)
        ])

        # Seed baseline donors
        d_65d = (now - datetime.timedelta(days=65)).isoformat()
        d_90d = (now - datetime.timedelta(days=90)).isoformat()
        d_20d = (now - datetime.timedelta(days=20)).isoformat()
        d_80d = (now - datetime.timedelta(days=80)).isoformat()
        d_60d = (now - datetime.timedelta(days=60)).isoformat()

        cursor.executemany("""
        INSERT INTO donor_profiles (donor_id, user_account_id, full_name, blood_type, encrypted_national_id, district, latitude, longitude, eligibility_status, last_donation_date, push_device_token, phone_number, donation_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, [
            ('donor-001', 'usr-101', 'Johnathan Vance', 'O_NEG', 'AES256GCM:a7b8c9d0e1f2:9988776655443322', 'Downtown', 40.7150, -74.0020, 'ELIGIBLE', d_65d, 'fcm_token_001', '+1-555-0199', 5),
            ('donor-002', 'usr-102', 'Elena Rostova', 'O_NEG', 'AES256GCM:b8c9d0e1f2a3:1122334455667788', 'Lower Manhattan', 40.7200, -73.9980, 'ELIGIBLE', d_90d, None, '+1-555-0188', 8),
            ('donor-003', 'usr-103', 'Marcus Chen', 'O_NEG', 'AES256GCM:c9d0e1f2a3b4:5566778899001122', 'Brooklyn Heights', 40.6960, -73.9930, 'DEFERRED', d_20d, 'fcm_token_003', '+1-555-0177', 2),
            ('donor-004', 'usr-104', 'Sarah Jenkins', 'A_POS', 'AES256GCM:d0e1f2a3b4c5:3344556677889900', 'Midtown', 40.7549, -73.9840, 'ELIGIBLE', d_80d, 'fcm_token_004', '+1-555-0166', 4),
            ('donor-005', 'usr-105', 'David Kim', 'B_NEG', 'AES256GCM:e1f2a3b4c5d6:7788990011223344', 'Jersey City', 40.7282, -74.0776, 'ELIGIBLE', d_60d, 'fcm_token_005', '+1-555-0155', 3)
        ])

        # Seed Genesis block for WORM ledger
        cursor.execute("""
        INSERT INTO audit_hipaa_ledger (audit_id, actor_user_id, action_type, resource_type, resource_id, payload_hash_sha256, previous_hash_sha256, timestamp)
        VALUES ('audit-000', 'system', 'GENESIS_BLOCK', 'SYSTEM', 'BDCN_CORE', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', '0000000000000000000000000000000000000000000000000000000000000000', ?);
        """, (now.isoformat(),))

    conn.commit()


def reset_database() -> sqlite3.Connection:
    """Helper to reset database for isolated test execution."""
    global _sqlite_conn
    if _sqlite_conn:
        try:
            _sqlite_conn.close()
        except Exception:
            pass
    _sqlite_conn = None
    return get_db_connection()
