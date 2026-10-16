-- Emergency Blood Donor Connection & Real-Time Dispatch Network Schema

CREATE TABLE IF NOT EXISTS emergency_requisitions (
    request_id TEXT PRIMARY KEY,
    hospital_id TEXT NOT NULL,
    hospital_name TEXT NOT NULL,
    blood_type TEXT NOT NULL,
    units INTEGER NOT NULL,
    urgency TEXT NOT NULL DEFAULT 'Emergency',
    latitude REAL,
    longitude REAL,
    radius_km REAL DEFAULT 15.0,
    status TEXT NOT NULL DEFAULT 'broadcast',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS donor_responses (
    response_id TEXT PRIMARY KEY,
    request_id TEXT NOT NULL,
    donor_id TEXT NOT NULL,
    donor_username TEXT,
    action TEXT NOT NULL, -- 'confirmed' or 'declined'
    responded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (request_id) REFERENCES emergency_requisitions(request_id)
);

CREATE TABLE IF NOT EXISTS digital_check_in_passes (
    pass_id TEXT PRIMARY KEY,
    response_id TEXT NOT NULL,
    request_id TEXT NOT NULL,
    donor_id TEXT NOT NULL,
    hospital_name TEXT NOT NULL,
    hospital_address TEXT NOT NULL,
    blood_type TEXT NOT NULL,
    appointment_time TEXT NOT NULL,
    qr_code_data TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (response_id) REFERENCES donor_responses(response_id),
    FOREIGN KEY (request_id) REFERENCES emergency_requisitions(request_id)
);

CREATE INDEX IF NOT EXISTS idx_requisitions_blood_type ON emergency_requisitions(blood_type);
CREATE INDEX IF NOT EXISTS idx_requisitions_status ON emergency_requisitions(status);
CREATE INDEX IF NOT EXISTS idx_passes_donor ON digital_check_in_passes(donor_id);
