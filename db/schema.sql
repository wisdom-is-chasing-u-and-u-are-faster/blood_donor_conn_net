-- ANSI SQL DDL Schema for BDCN (Blood Donor Connection Network)

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(150) NOT NULL,
    email VARCHAR(150),
    role VARCHAR(50) DEFAULT 'donor',
    blood_group VARCHAR(10),
    h3_cluster VARCHAR(50),
    donation_count INTEGER DEFAULT 0,
    last_donation_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS blood_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id VARCHAR(50) UNIQUE NOT NULL,
    recipient_name VARCHAR(150),
    blood_type VARCHAR(10) NOT NULL,
    donation_type VARCHAR(50) DEFAULT 'Whole Blood',
    units INTEGER DEFAULT 1,
    urgency VARCHAR(50) DEFAULT 'Standard',
    h3_cluster VARCHAR(50) NOT NULL,
    document_name VARCHAR(255),
    notes TEXT,
    status VARCHAR(50) DEFAULT 'Pending',
    adjudicated_by VARCHAR(100),
    adjudicated_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS donation_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    donor_id VARCHAR(100) NOT NULL,
    donation_type VARCHAR(50) NOT NULL,
    donation_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action VARCHAR(100) NOT NULL,
    details TEXT,
    user VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipient_id VARCHAR(100),
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    h3_cluster VARCHAR(50),
    is_read BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
