-- BDCN Core Platform Relational Database Schema
-- Compatible with PostgreSQL (Cloud SQL) and SQLite

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    role VARCHAR(50) NOT NULL, -- donor, recipient, hospital, admin
    name VARCHAR(150),
    email VARCHAR(150),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS donors (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(150) NOT NULL,
    age INTEGER,
    gender VARCHAR(20),
    blood_group VARCHAR(10) NOT NULL,
    last_donation DATE,
    donation_count INTEGER DEFAULT 0,
    total_points INTEGER DEFAULT 0,
    lives_impacted INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS blood_requests (
    id SERIAL PRIMARY KEY,
    hospital VARCHAR(150) NOT NULL,
    blood_type VARCHAR(10) NOT NULL,
    units INTEGER NOT NULL,
    filename VARCHAR(255),
    status VARCHAR(50) DEFAULT 'Pending', -- Pending, Approved, Rejected, Fulfilled
    urgency VARCHAR(50) DEFAULT 'Emergency', -- Critical, High, Medium, Low, Emergency, Routine
    district VARCHAR(100) DEFAULT 'Downtown',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS hotspots (
    id SERIAL PRIMARY KEY,
    district VARCHAR(100) NOT NULL,
    count INTEGER NOT NULL,
    blood_type VARCHAR(10) NOT NULL,
    distance INTEGER NOT NULL,
    latitude_coarse DOUBLE PRECISION,
    longitude_coarse DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS badges (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    badge_name VARCHAR(100) NOT NULL,
    description TEXT,
    earned BOOLEAN DEFAULT FALSE,
    earned_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    action VARCHAR(100) NOT NULL,
    details TEXT,
    username VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
