-- Database Schema for Blood Donor Connection Network
-- ARCH-7525: Donor Table with Nullable last_donation_date and B-Tree Indexes

CREATE TABLE IF NOT EXISTS donors (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone_number VARCHAR(50) NOT NULL,
    blood_group VARCHAR(10) NOT NULL,
    last_donation_date DATE NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- B-Tree indexes for low-latency indexed queries
CREATE INDEX IF NOT EXISTS idx_donors_last_donation_date ON donors (last_donation_date);
CREATE INDEX IF NOT EXISTS idx_donors_blood_group ON donors (blood_group);
