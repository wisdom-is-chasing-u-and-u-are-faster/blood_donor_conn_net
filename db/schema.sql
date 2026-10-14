-- Relational Schema DDL for Blood Donor Connection Network (BDCN)
-- Compliant with HIPAA § 164.514(b)(2) and FDA 21 CFR Part 11 Audit Trail

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'donor',
    provider VARCHAR(50) DEFAULT 'local',
    blood_type VARCHAR(10),
    district VARCHAR(100) DEFAULT 'Central',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS donors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    blood_type VARCHAR(10) NOT NULL,
    status VARCHAR(50) DEFAULT 'Available',
    last_donation_date DATE,
    district VARCHAR(100) DEFAULT 'Downtown',
    cluster_id VARCHAR(50),
    total_donations INTEGER DEFAULT 0,
    gamification_points INTEGER DEFAULT 100,
    current_tier VARCHAR(50) DEFAULT 'Bronze',
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS donor_clusters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cluster_id VARCHAR(50) UNIQUE NOT NULL,
    district VARCHAR(100) NOT NULL,
    centroid_lat REAL NOT NULL,
    centroid_lng REAL NOT NULL,
    donor_count INTEGER DEFAULT 1,
    density_tier VARCHAR(50) DEFAULT 'Medium',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS medical_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    document_type VARCHAR(100) DEFAULT 'Blood Compatibility Report',
    verification_status VARCHAR(50) DEFAULT 'Pending Review',
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    badge_icon VARCHAR(100) NOT NULL,
    points_reward INTEGER DEFAULT 50,
    tier VARCHAR(50) DEFAULT 'Bronze'
);

CREATE TABLE IF NOT EXISTS user_achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    achievement_id INTEGER,
    unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    shared_at TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(achievement_id) REFERENCES achievements(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS blood_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipient_name VARCHAR(150) NOT NULL,
    hospital VARCHAR(150) NOT NULL,
    blood_type VARCHAR(10) NOT NULL,
    units INTEGER NOT NULL DEFAULT 1,
    urgency VARCHAR(50) DEFAULT 'Standard',
    status VARCHAR(50) DEFAULT 'Pending',
    district VARCHAR(100) DEFAULT 'Downtown',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action VARCHAR(100) NOT NULL,
    details TEXT NOT NULL,
    user VARCHAR(150) DEFAULT 'System',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
