-- Blood Donor Connection Network (BDCN) Schema
-- Supports Cloud SQL PostgreSQL with PostGIS extensions & SQLite local fallback

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'donor',
    email VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS donors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    age INTEGER NOT NULL,
    gender VARCHAR(20) NOT NULL,
    blood_group VARCHAR(10) NOT NULL,
    last_donation DATE,
    donation_count INTEGER DEFAULT 0,
    district VARCHAR(100) DEFAULT 'Downtown',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS demands (
    id SERIAL PRIMARY KEY,
    hospital VARCHAR(150) NOT NULL,
    blood_type VARCHAR(10) NOT NULL,
    units INTEGER NOT NULL,
    filename VARCHAR(255),
    status VARCHAR(50) DEFAULT 'Pending',
    urgency VARCHAR(50) DEFAULT 'Emergency',
    district VARCHAR(100) DEFAULT 'Downtown',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    hospital VARCHAR(150) NOT NULL,
    blood_type VARCHAR(10) NOT NULL,
    status VARCHAR(50) DEFAULT 'Active',
    district VARCHAR(100) DEFAULT 'Downtown',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    action VARCHAR(100) NOT NULL,
    details TEXT NOT NULL,
    user_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
