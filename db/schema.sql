-- ANSI SQL DDL Schema for Blood Donor Connection Network (BDCN)
-- Compliant with SQLite and PostgreSQL

CREATE TABLE IF NOT EXISTS donors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    username VARCHAR(100) UNIQUE,
    age INTEGER,
    gender VARCHAR(50),
    blood_group VARCHAR(10) NOT NULL,
    district VARCHAR(100) DEFAULT 'Downtown',
    last_donation DATE,
    donation_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hospital_name VARCHAR(255) NOT NULL,
    patient_name VARCHAR(255),
    blood_type VARCHAR(10) NOT NULL,
    units INTEGER DEFAULT 1,
    urgency VARCHAR(50) DEFAULT 'Emergency',
    district VARCHAR(100) DEFAULT 'Downtown',
    filename VARCHAR(255),
    status VARCHAR(50) DEFAULT 'Pending',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS hotspots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    district VARCHAR(100) NOT NULL,
    count INTEGER DEFAULT 1,
    blood_type VARCHAR(10) NOT NULL,
    distance INTEGER DEFAULT 10,
    top INTEGER DEFAULT 50,
    left INTEGER DEFAULT 50,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action VARCHAR(100) NOT NULL,
    details TEXT,
    user VARCHAR(100) DEFAULT 'System',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    read BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
