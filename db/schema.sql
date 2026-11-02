-- DDL Schema for BloodConnect BDCN Platform
CREATE TABLE IF NOT EXISTS donor_prescreenings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    donor_id TEXT,
    age INTEGER NOT NULL,
    weight REAL NOT NULL,
    last_donation_days INTEGER NOT NULL,
    chronic_conditions BOOLEAN NOT NULL DEFAULT 0,
    recent_travel BOOLEAN NOT NULL DEFAULT 0,
    status TEXT NOT NULL,
    reasons TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS verified_donors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    donor_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    blood_group TEXT NOT NULL,
    verified BOOLEAN NOT NULL DEFAULT 1,
    contact_phone TEXT NOT NULL,
    location TEXT NOT NULL,
    last_donation_date TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
