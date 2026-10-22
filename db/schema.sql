-- db/schema.sql — Relational schema for BDCN Platform

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT DEFAULT 'donor',
    password_hash TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS donor_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    blood_type TEXT NOT NULL,
    contact_phone TEXT,
    location TEXT,
    availability_status TEXT DEFAULT 'Available',
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS donation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    donor_id INTEGER,
    donation_date DATE,
    units INTEGER DEFAULT 1,
    location TEXT,
    notes TEXT,
    FOREIGN KEY(donor_id) REFERENCES donor_profiles(id)
);

CREATE TABLE IF NOT EXISTS blood_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipient_name TEXT NOT NULL,
    blood_type TEXT NOT NULL,
    units INTEGER NOT NULL,
    hospital_name TEXT,
    location TEXT NOT NULL,
    urgency TEXT DEFAULT 'Urgent',
    contact_phone TEXT,
    status TEXT DEFAULT 'Pending Admin Review',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pledges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER,
    donor_id INTEGER,
    donor_name TEXT,
    donor_phone TEXT,
    pledge_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'Pledged',
    FOREIGN KEY(request_id) REFERENCES blood_requests(id)
);

CREATE TABLE IF NOT EXISTS anonymized_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER,
    sender_role TEXT,
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(request_id) REFERENCES blood_requests(id)
);
