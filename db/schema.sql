-- ============================================================================
-- Blood Donor Connection Network (BDCN) Physical Database Schema
-- Baseline: PostgreSQL 16 + PostGIS Extension
-- Option A: Modular Monolith with Relational ACID Guarantees
-- ============================================================================

-- Enable PostGIS Spatial Extension and UUID Generator (if supported)
-- CREATE EXTENSION IF NOT EXISTS postgis;
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ----------------------------------------------------------------------------
-- 1. Clinical Facilities / Hospitals
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS clinical_facilities (
    facility_id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    facility_type VARCHAR(50) NOT NULL DEFAULT 'TRAUMA_CENTER_LEVEL_1',
    district VARCHAR(100) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    contact_phone VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 2. Blood Component Inventory Tier (FEFO Indexing & Row Locks)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS inventory_blood_units (
    unit_id VARCHAR(64) PRIMARY KEY,
    din_barcode VARCHAR(50) NOT NULL UNIQUE,
    facility_id VARCHAR(64) NOT NULL,
    blood_type VARCHAR(10) NOT NULL, -- A_POS, A_NEG, B_POS, B_NEG, AB_POS, AB_NEG, O_POS, O_NEG
    component_type VARCHAR(30) NOT NULL, -- WHOLE_BLOOD, RED_BLOOD_CELLS, PLATELETS, FRESH_FROZEN_PLASMA, CRYOPRECIPITATE
    volume_ml INTEGER NOT NULL DEFAULT 450,
    status VARCHAR(20) NOT NULL DEFAULT 'AVAILABLE', -- AVAILABLE, RESERVED, TRANSFUSED, EXPIRED, QUARANTINED
    reservation_id VARCHAR(64),
    lease_expires_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (facility_id) REFERENCES clinical_facilities(facility_id)
);

CREATE INDEX IF NOT EXISTS idx_blood_units_fefo_lookup
    ON inventory_blood_units (blood_type, component_type, expires_at ASC)
    WHERE status = 'AVAILABLE';

CREATE INDEX IF NOT EXISTS idx_blood_units_facility
    ON inventory_blood_units (facility_id, status);

-- ----------------------------------------------------------------------------
-- 3. Emergency Trauma Dispatch Requests (State Machine & Fast Path)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dispatch_emergency_requests (
    request_id VARCHAR(64) PRIMARY KEY,
    requesting_hospital_id VARCHAR(64) NOT NULL,
    required_blood_type VARCHAR(10) NOT NULL,
    component_type VARCHAR(30) NOT NULL,
    units_requested INTEGER NOT NULL CHECK (units_requested > 0 AND units_requested <= 50),
    urgency_tier VARCHAR(20) NOT NULL DEFAULT 'CODE_RED', -- CODE_RED, URGENT, ROUTINE
    status VARCHAR(30) NOT NULL DEFAULT 'INITIATED', -- INITIATED, INVENTORY_ALLOCATED, DISPATCHED, TRANSIT, DELIVERED, CANCELLED
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    clinical_notes_encrypted TEXT NOT NULL, -- Base64 AES-256-GCM cipher payload
    allocated_units_count INTEGER NOT NULL DEFAULT 0,
    matched_donors_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    estimated_arrival_at TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (requesting_hospital_id) REFERENCES clinical_facilities(facility_id)
);

CREATE INDEX IF NOT EXISTS idx_dispatch_requests_status
    ON dispatch_emergency_requests (status, urgency_tier);

-- ----------------------------------------------------------------------------
-- 4. Donor Profiles & Geospatial Registry
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS donor_profiles (
    donor_id VARCHAR(64) PRIMARY KEY,
    user_account_id VARCHAR(64) NOT NULL UNIQUE,
    full_name VARCHAR(255) NOT NULL,
    blood_type VARCHAR(10) NOT NULL,
    encrypted_national_id TEXT NOT NULL, -- AES-256-GCM ciphertext
    district VARCHAR(100) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    eligibility_status VARCHAR(20) NOT NULL DEFAULT 'ELIGIBLE', -- ELIGIBLE, DEFERRED
    last_donation_date TIMESTAMP WITH TIME ZONE,
    push_device_token VARCHAR(255),
    phone_number VARCHAR(50),
    donation_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_donors_blood_eligibility
    ON donor_profiles (blood_type, eligibility_status);

-- ----------------------------------------------------------------------------
-- 5. HIPAA / HITECH WORM Immutable Audit Access Ledger
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_hipaa_ledger (
    audit_id VARCHAR(64) PRIMARY KEY,
    actor_user_id VARCHAR(64) NOT NULL,
    action_type VARCHAR(50) NOT NULL, -- READ_EPHI, WRITE_DISPATCH, RESERVATION_ALLOCATE, LEASE_EXPIRE, BROADCAST_TRIGGER
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(64) NOT NULL,
    payload_hash_sha256 VARCHAR(64) NOT NULL,
    previous_hash_sha256 VARCHAR(64) NOT NULL,
    client_ip VARCHAR(50) DEFAULT '127.0.0.1',
    user_agent VARCHAR(255) DEFAULT 'BDCN-Internal-Client',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_ledger_timestamp
    ON audit_hipaa_ledger (timestamp ASC);

CREATE INDEX IF NOT EXISTS idx_audit_ledger_resource
    ON audit_hipaa_ledger (resource_type, resource_id);
