-- Blood Donor Connection Network (BDCN) Relational Database Schema
-- Compatible with SQLite and PostgreSQL

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    role TEXT NOT NULL DEFAULT 'donor',
    provider TEXT DEFAULT 'local',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS donors (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    name TEXT NOT NULL,
    age INTEGER,
    gender TEXT,
    blood_group TEXT NOT NULL,
    district TEXT NOT NULL,
    donation_count INTEGER DEFAULT 0,
    last_donation DATE,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS donor_hotspots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    district TEXT NOT NULL,
    coarse_latitude REAL NOT NULL,
    coarse_longitude REAL NOT NULL,
    donor_count INTEGER NOT NULL,
    primary_blood_types TEXT NOT NULL,
    distance_km REAL NOT NULL,
    urgency_level TEXT DEFAULT 'Normal'
);

CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    user_email TEXT NOT NULL,
    document_type TEXT NOT NULL,
    filename TEXT NOT NULL,
    encrypted_blob_uri TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Pending',
    district TEXT DEFAULT 'Central District',
    consent_given INTEGER DEFAULT 1,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS verifications (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Pending',
    reviewed_by TEXT,
    review_notes TEXT,
    reviewed_at TIMESTAMP,
    FOREIGN KEY(document_id) REFERENCES documents(id)
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    details TEXT NOT NULL,
    user TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notifications (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    read INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
