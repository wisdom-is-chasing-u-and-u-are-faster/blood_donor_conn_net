-- Schema for Blood Donor Connection Network
-- Defines donors, urgent requests, and transactions with composite indexes

CREATE TABLE IF NOT EXISTS donors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    blood_group VARCHAR(5) NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE,
    current_status VARCHAR(50) DEFAULT 'active',
    age INT NOT NULL,
    gender VARCHAR(20),
    weight NUMERIC(5, 2),
    email VARCHAR(255),
    phone VARCHAR(50),
    district VARCHAR(100),
    last_donation DATE,
    donation_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Composite index to satisfy CONSTRAINT-003 and REQ-N-003: (blood_group, is_verified, current_status)
CREATE INDEX IF NOT EXISTS idx_donors_matching ON donors (blood_group, is_verified, current_status);

CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(64) UNIQUE NOT NULL,
    idempotency_key VARCHAR(128) UNIQUE NOT NULL,
    user_id VARCHAR(100) NOT NULL,
    user_role VARCHAR(50) NOT NULL,
    payload JSONB,
    status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_transactions_idempotency ON transactions (idempotency_key);

CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    action VARCHAR(255) NOT NULL,
    details TEXT,
    user_identifier VARCHAR(100),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
