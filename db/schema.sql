-- Blood Donor Connection Network (BDCN)
-- Database Migration Changelog: DB-CHANGELOG-001.sql
-- Baseline Architecture: Option B - Cloud-Native PostgreSQL 15+ with PostGIS
-- Compliance: HIPAA (ePHI separation), FDA 21 CFR Part 11 Audit Trail

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE SCHEMA IF NOT EXISTS bdcn_core;
CREATE SCHEMA IF NOT EXISTS bdcn_audit;

-- 2. ENUMS
DO $$ BEGIN
    CREATE TYPE bdcn_core.blood_abo_enum AS ENUM ('A', 'B', 'AB', 'O');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE bdcn_core.rh_factor_enum AS ENUM ('POSITIVE', 'NEGATIVE');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE bdcn_core.donation_category_enum AS ENUM ('WHOLE_BLOOD', 'DOUBLE_RED_CELLS', 'PLATELETS', 'PLASMA');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE bdcn_core.dispatch_severity_enum AS ENUM ('LEVEL_1_CATASTROPHIC', 'LEVEL_2_URGENT', 'LEVEL_3_ANTICIPATED');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE bdcn_core.dispatch_status_enum AS ENUM ('INITIATED', 'MATCHING', 'DISPATCHED', 'ACCEPTED', 'IN_TRANSIT', 'FULFILLED', 'EXPIRED', 'CANCELLED');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE bdcn_core.reservation_status_enum AS ENUM ('ACTIVE', 'CONSUMED', 'EXPIRED', 'CANCELLED');
EXCEPTION WHEN duplicate_object THEN null; END $$;

-- 3. HOSPITALS & CLINICAL SITES
CREATE TABLE IF NOT EXISTS bdcn_core.hospitals (
    hospital_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    license_number VARCHAR(64) UNIQUE NOT NULL,
    facility_name VARCHAR(255) NOT NULL,
    trauma_level VARCHAR(32) NOT NULL,
    contact_phone VARCHAR(32) NOT NULL,
    contact_email VARCHAR(255) NOT NULL,
    facility_location GEOMETRY(Point, 4326),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    address_line1 VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state_province VARCHAR(100) NOT NULL,
    postal_code VARCHAR(32) NOT NULL,
    country_code VARCHAR(3) NOT NULL DEFAULT 'USA',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_hospitals_spatial ON bdcn_core.hospitals USING GIST (facility_location);

-- 4. DONORS (PII & Medical Phenotypes)
CREATE TABLE IF NOT EXISTS bdcn_core.donors (
    donor_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    auth_user_id VARCHAR(128) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    abo_type VARCHAR(10) NOT NULL,
    rh_factor VARCHAR(10) NOT NULL,
    rare_antigen_profile JSONB DEFAULT '{}'::jsonb,
    primary_phone VARCHAR(32) NOT NULL,
    email_address VARCHAR(255) NOT NULL,
    notification_preference VARCHAR(32) NOT NULL DEFAULT 'PUSH_AND_SMS',
    current_location GEOMETRY(Point, 4326),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    location_updated_at TIMESTAMPTZ,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_deferred BOOLEAN NOT NULL DEFAULT FALSE,
    deferral_reason VARCHAR(255),
    deferral_end_date DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_donors_spatial ON bdcn_core.donors USING GIST (current_location);
CREATE INDEX IF NOT EXISTS idx_donors_blood_lookup ON bdcn_core.donors (abo_type, rh_factor) WHERE is_active = TRUE AND is_deferred = FALSE;
CREATE INDEX IF NOT EXISTS idx_donors_auth ON bdcn_core.donors (auth_user_id);

-- 5. DONATION HISTORY & ELIGIBILITY ENFORCEMENT
CREATE TABLE IF NOT EXISTS bdcn_core.donation_events (
    donation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    donor_id UUID NOT NULL REFERENCES bdcn_core.donors(donor_id) ON DELETE RESTRICT,
    hospital_id UUID NOT NULL REFERENCES bdcn_core.hospitals(hospital_id) ON DELETE RESTRICT,
    donation_type VARCHAR(32) NOT NULL,
    units_collected DECIMAL(4, 2) NOT NULL DEFAULT 1.0,
    collected_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    phlebotomist_license_id VARCHAR(64) NOT NULL,
    hemoglobin_level DECIMAL(4, 1) NOT NULL,
    blood_pressure_systolic INT NOT NULL,
    blood_pressure_diastolic INT NOT NULL,
    adverse_reaction_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_donation_events_donor_date ON bdcn_core.donation_events (donor_id, collected_at DESC);

-- 6. INVENTORY TELEMETRY & PRODUCT STOCKS
CREATE TABLE IF NOT EXISTS bdcn_core.inventory_items (
    item_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hospital_id UUID NOT NULL REFERENCES bdcn_core.hospitals(hospital_id) ON DELETE RESTRICT,
    din_number VARCHAR(64) UNIQUE NOT NULL,
    component_type VARCHAR(64) NOT NULL,
    abo_type VARCHAR(10) NOT NULL,
    rh_factor VARCHAR(10) NOT NULL,
    collection_date TIMESTAMPTZ NOT NULL,
    expiration_date TIMESTAMPTZ NOT NULL,
    storage_temp_celsius DECIMAL(4, 2) NOT NULL,
    is_quarantined BOOLEAN NOT NULL DEFAULT FALSE,
    status VARCHAR(32) NOT NULL DEFAULT 'AVAILABLE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_inventory_lookup ON bdcn_core.inventory_items (hospital_id, component_type, abo_type, rh_factor, expiration_date);

-- 7. INVENTORY RESERVATION LEASES (120-min Auto Release)
CREATE TABLE IF NOT EXISTS bdcn_core.inventory_reservations (
    reservation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hospital_id UUID NOT NULL REFERENCES bdcn_core.hospitals(hospital_id),
    clinical_encounter_id VARCHAR(64) NOT NULL,
    item_id UUID NOT NULL REFERENCES bdcn_core.inventory_items(item_id),
    status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
    reserved_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ NOT NULL DEFAULT (CURRENT_TIMESTAMP + INTERVAL '120 minutes'),
    released_at TIMESTAMPTZ,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_reservations_active_lease ON bdcn_core.inventory_reservations (status, expires_at) WHERE status = 'ACTIVE';

-- 8. EMERGENCY DISPATCH STATE MACHINE
CREATE TABLE IF NOT EXISTS bdcn_core.emergency_dispatches (
    dispatch_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hospital_id UUID NOT NULL REFERENCES bdcn_core.hospitals(hospital_id),
    severity VARCHAR(32) NOT NULL,
    required_abo VARCHAR(10) NOT NULL,
    required_rh VARCHAR(10) NOT NULL,
    units_requested INT NOT NULL CHECK (units_requested > 0),
    units_confirmed INT NOT NULL DEFAULT 0,
    search_radius_meters DOUBLE PRECISION NOT NULL DEFAULT 15000.0,
    target_location GEOMETRY(Point, 4326),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    status VARCHAR(32) NOT NULL DEFAULT 'INITIATED',
    initiated_by_user VARCHAR(128) NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL DEFAULT (CURRENT_TIMESTAMP + INTERVAL '180 minutes'),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_dispatches_status ON bdcn_core.emergency_dispatches (status, created_at DESC);

-- 9. DISPATCH CANDIDATES & AUDITABLE RESPONSES
CREATE TABLE IF NOT EXISTS bdcn_core.dispatch_candidates (
    candidate_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dispatch_id UUID NOT NULL REFERENCES bdcn_core.emergency_dispatches(dispatch_id) ON DELETE CASCADE,
    donor_id UUID NOT NULL REFERENCES bdcn_core.donors(donor_id),
    distance_meters DOUBLE PRECISION NOT NULL,
    notification_dispatched_at TIMESTAMPTZ,
    response_status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    responded_at TIMESTAMPTZ,
    estimated_arrival_minutes INT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_dispatch_donor ON bdcn_core.dispatch_candidates (dispatch_id, donor_id);

-- 10. FDA 21 CFR PART 11 & HIPAA AUDIT LEDGER (Append-Only)
CREATE TABLE IF NOT EXISTS bdcn_audit.compliance_log (
    log_id BIGSERIAL PRIMARY KEY,
    entity_name VARCHAR(64) NOT NULL,
    entity_id UUID NOT NULL,
    action_type VARCHAR(16) NOT NULL,
    performed_by VARCHAR(128) NOT NULL,
    performed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    old_state JSONB,
    new_state JSONB,
    client_ip VARCHAR(64),
    previous_hash TEXT,
    checksum_signature TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_entity ON bdcn_audit.compliance_log (entity_name, entity_id, performed_at DESC);

-- 11. STORED PROCEDURE: ROLLING ELIGIBILITY VALIDATOR
CREATE OR REPLACE FUNCTION bdcn_core.fn_validate_donor_eligibility(
    p_donor_id UUID,
    p_donation_type VARCHAR(32) DEFAULT 'WHOLE_BLOOD',
    p_target_date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
)
RETURNS TABLE (
    is_eligible BOOLEAN,
    days_remaining INT,
    next_eligible_date TIMESTAMPTZ,
    block_reason TEXT
) AS $$
DECLARE
    v_last_donation RECORD;
    v_required_interval INTERVAL;
    v_donor RECORD;
    v_target TIMESTAMPTZ;
BEGIN
    v_target := COALESCE(p_target_date, CURRENT_TIMESTAMP);

    -- Check basic deferral flags
    SELECT * INTO v_donor FROM bdcn_core.donors WHERE donor_id = p_donor_id;
    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, -1, NULL::TIMESTAMPTZ, 'DONOR_NOT_FOUND'::TEXT;
        RETURN;
    END IF;

    IF v_donor.is_deferred THEN
        IF v_donor.deferral_end_date IS NOT NULL AND v_target::date >= v_donor.deferral_end_date THEN
            -- Deferral has elapsed
            NULL;
        ELSE
            RETURN QUERY SELECT FALSE, 
                CASE 
                    WHEN v_donor.deferral_end_date IS NOT NULL THEN (v_donor.deferral_end_date - v_target::date)::INT 
                    ELSE 9999 
                END,
                v_donor.deferral_end_date::TIMESTAMPTZ, 
                COALESCE(v_donor.deferral_reason, 'ACTIVE_MEDICAL_DEFERRAL')::TEXT;
            RETURN;
        END IF;
    END IF;

    -- Interval determination per BRD rules: Whole Blood (56 days), Double Red (112 days), Platelets (7 days)
    IF p_donation_type = 'WHOLE_BLOOD' THEN
        v_required_interval := INTERVAL '56 days';
    ELSIF p_donation_type = 'DOUBLE_RED_CELLS' THEN
        v_required_interval := INTERVAL '112 days';
    ELSIF p_donation_type = 'PLATELETS' THEN
        v_required_interval := INTERVAL '7 days';
    ELSE
        v_required_interval := INTERVAL '28 days';
    END IF;

    -- Query latest collection date
    SELECT collected_at INTO v_last_donation
    FROM bdcn_core.donation_events
    WHERE donor_id = p_donor_id AND donation_type = p_donation_type
    ORDER BY collected_at DESC
    LIMIT 1;

    IF v_last_donation.collected_at IS NULL THEN
        -- First-time donor
        RETURN QUERY SELECT TRUE, 0, v_target, 'ELIGIBLE_FIRST_TIME'::TEXT;
        RETURN;
    END IF;

    IF (v_target - v_last_donation.collected_at) >= v_required_interval THEN
        RETURN QUERY SELECT TRUE, 0, (v_last_donation.collected_at + v_required_interval), 'ELIGIBLE'::TEXT;
    ELSE
        RETURN QUERY SELECT 
            FALSE, 
            EXTRACT(DAY FROM ((v_last_donation.collected_at + v_required_interval) - v_target))::INT,
            (v_last_donation.collected_at + v_required_interval),
            'MINIMUM_DONATION_INTERVAL_NOT_MET'::TEXT;
    END IF;
END;
$$ LANGUAGE plpgsql STABLE;
