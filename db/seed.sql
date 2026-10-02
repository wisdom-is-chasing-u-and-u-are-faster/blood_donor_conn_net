-- ============================================================================
-- Blood Donor Connection Network (BDCN) Baseline Seed Data
-- ============================================================================

-- 1. Clinical Facilities / Hospitals
INSERT INTO clinical_facilities (facility_id, name, facility_type, district, latitude, longitude, contact_phone)
VALUES
    ('fac-001', 'Metro City Trauma Hospital', 'LEVEL_1_TRAUMA_CENTER', 'Downtown', 40.7128, -74.0060, '+1-212-555-0100'),
    ('fac-002', 'Mercy Regional Medical Center', 'COMMUNITY_HOSPITAL', 'North District', 40.7589, -73.9851, '+1-212-555-0200'),
    ('fac-003', 'St. Jude Emergency Center', 'URGENT_SURGICAL_UNIT', 'West Hills', 40.7829, -73.9654, '+1-212-555-0300')
ON CONFLICT (facility_id) DO NOTHING;

-- 2. Baseline Blood Inventory (FEFO Timers)
INSERT INTO inventory_blood_units (unit_id, din_barcode, facility_id, blood_type, component_type, volume_ml, status, expires_at)
VALUES
    ('unit-001', 'W0384-25-001001', 'fac-001', 'O_NEG', 'RED_BLOOD_CELLS', 450, 'AVAILABLE', CURRENT_TIMESTAMP + INTERVAL '24 hours'),
    ('unit-002', 'W0384-25-001002', 'fac-001', 'O_NEG', 'RED_BLOOD_CELLS', 450, 'AVAILABLE', CURRENT_TIMESTAMP + INTERVAL '48 hours'),
    ('unit-003', 'W0384-25-001003', 'fac-001', 'O_NEG', 'RED_BLOOD_CELLS', 450, 'AVAILABLE', CURRENT_TIMESTAMP + INTERVAL '72 hours'),
    ('unit-004', 'W0384-25-001004', 'fac-001', 'O_NEG', 'RED_BLOOD_CELLS', 450, 'AVAILABLE', CURRENT_TIMESTAMP + INTERVAL '96 hours'),
    ('unit-005', 'W0384-25-001005', 'fac-001', 'O_POS', 'RED_BLOOD_CELLS', 450, 'AVAILABLE', CURRENT_TIMESTAMP + INTERVAL '120 hours'),
    ('unit-006', 'W0384-25-001006', 'fac-001', 'A_POS', 'RED_BLOOD_CELLS', 450, 'AVAILABLE', CURRENT_TIMESTAMP + INTERVAL '36 hours'),
    ('unit-007', 'W0384-25-001007', 'fac-001', 'A_POS', 'RED_BLOOD_CELLS', 450, 'AVAILABLE', CURRENT_TIMESTAMP + INTERVAL '72 hours'),
    ('unit-008', 'W0384-25-001008', 'fac-001', 'B_NEG', 'PLATELETS', 300, 'AVAILABLE', CURRENT_TIMESTAMP + INTERVAL '48 hours'),
    ('unit-009', 'W0384-25-001009', 'fac-001', 'B_NEG', 'PLATELETS', 300, 'AVAILABLE', CURRENT_TIMESTAMP + INTERVAL '72 hours'),
    ('unit-010', 'W0384-25-001010', 'fac-001', 'AB_POS', 'FRESH_FROZEN_PLASMA', 250, 'AVAILABLE', CURRENT_TIMESTAMP + INTERVAL '180 days')
ON CONFLICT (din_barcode) DO NOTHING;

-- 3. Baseline Donors (Geospatial Coordinates centered in NYC region)
INSERT INTO donor_profiles (donor_id, user_account_id, full_name, blood_type, encrypted_national_id, district, latitude, longitude, eligibility_status, last_donation_date, phone_number, donation_count)
VALUES
    ('donor-001', 'usr-101', 'Johnathan Vance', 'O_NEG', 'AES256GCM:a7b8c9d0e1f2:9988776655443322', 'Downtown', 40.7150, -74.0020, 'ELIGIBLE', CURRENT_TIMESTAMP - INTERVAL '65 days', '+1-555-0199', 5),
    ('donor-002', 'usr-102', 'Elena Rostova', 'O_NEG', 'AES256GCM:b8c9d0e1f2a3:1122334455667788', 'Lower Manhattan', 40.7200, -73.9980, 'ELIGIBLE', CURRENT_TIMESTAMP - INTERVAL '90 days', '+1-555-0188', 8),
    ('donor-003', 'usr-103', 'Marcus Chen', 'O_NEG', 'AES256GCM:c9d0e1f2a3b4:5566778899001122', 'Brooklyn Heights', 40.6960, -73.9930, 'DEFERRED', CURRENT_TIMESTAMP - INTERVAL '20 days', '+1-555-0177', 2),
    ('donor-004', 'usr-104', 'Sarah Jenkins', 'A_POS', 'AES256GCM:d0e1f2a3b4c5:3344556677889900', 'Midtown', 40.7549, -73.9840, 'ELIGIBLE', CURRENT_TIMESTAMP - INTERVAL '80 days', '+1-555-0166', 4),
    ('donor-005', 'usr-105', 'David Kim', 'B_NEG', 'AES256GCM:e1f2a3b4c5d6:7788990011223344', 'Jersey City', 40.7282, -74.0776, 'ELIGIBLE', CURRENT_TIMESTAMP - INTERVAL '60 days', '+1-555-0155', 3)
ON CONFLICT (donor_id) DO NOTHING;

-- 4. Initial Genesis Block for WORM Ledger
INSERT INTO audit_hipaa_ledger (audit_id, actor_user_id, action_type, resource_type, resource_id, payload_hash_sha256, previous_hash_sha256, timestamp)
VALUES
    ('audit-000', 'system', 'GENESIS_BLOCK', 'SYSTEM', 'BDCN_CORE', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', '0000000000000000000000000000000000000000000000000000000000000000', CURRENT_TIMESTAMP)
ON CONFLICT (audit_id) DO NOTHING;
