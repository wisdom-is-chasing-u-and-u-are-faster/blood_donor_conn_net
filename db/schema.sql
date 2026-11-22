-- Blood Donor Connection Network (BDCN) Schema
-- Compatible with SQLite and PostgreSQL

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(100) UNIQUE NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'donor',
    email VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS donors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(150) NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    age INTEGER NOT NULL,
    gender VARCHAR(20) NOT NULL,
    blood_group VARCHAR(10) NOT NULL,
    last_donation DATE,
    donation_count INTEGER DEFAULT 0,
    district VARCHAR(100) DEFAULT 'Downtown',
    availability_status VARCHAR(50) DEFAULT 'Available',
    cooldown_until DATE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS demands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hospital VARCHAR(150) NOT NULL,
    blood_type VARCHAR(10) NOT NULL,
    units INTEGER NOT NULL,
    filename VARCHAR(255),
    status VARCHAR(50) DEFAULT 'Pending',
    urgency VARCHAR(50) DEFAULT 'Emergency',
    district VARCHAR(100) DEFAULT 'Downtown',
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hospital VARCHAR(150) NOT NULL,
    blood_type VARCHAR(10) NOT NULL,
    status VARCHAR(50) DEFAULT 'Active',
    district VARCHAR(100) DEFAULT 'Downtown',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action VARCHAR(100) NOT NULL,
    details TEXT NOT NULL,
    user_name VARCHAR(100) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS donor_commitments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER NOT NULL,
    donor_id INTEGER NOT NULL,
    donor_username VARCHAR(100) NOT NULL,
    donor_name VARCHAR(150) NOT NULL,
    anonymous_name VARCHAR(100) NOT NULL,
    eta VARCHAR(50) DEFAULT 'unspecified',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(request_id, donor_id)
);
