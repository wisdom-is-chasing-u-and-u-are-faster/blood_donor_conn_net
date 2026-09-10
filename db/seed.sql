-- Blood Donor Connection Network (BDCN) Seed Data
-- DB-SEED-001.sql

-- Insert Sample Hospitals
INSERT INTO bdcn_core.hospitals (hospital_id, license_number, facility_name, trauma_level, contact_phone, contact_email, latitude, longitude, address_line1, city, state_province, postal_code)
VALUES 
    ('a0000000-0000-0000-0000-000000000001', 'HOSP-LIC-001', 'Memorial Trauma Hospital', 'LEVEL_1_TRAUMA', '+1-555-0100', 'trauma@memorial.org', 37.7749, -122.4194, '100 Hospital Way', 'San Francisco', 'CA', '94110'),
    ('a0000000-0000-0000-0000-000000000002', 'HOSP-LIC-002', 'St. Jude General Hospital', 'LEVEL_2_URGENT', '+1-555-0200', 'bloodbank@stjude.org', 37.7833, -122.4167, '200 Health Ave', 'San Francisco', 'CA', '94115')
ON CONFLICT (license_number) DO NOTHING;

-- Insert Donors (including Marcus Vance from Acceptance Criteria)
INSERT INTO bdcn_core.donors (donor_id, auth_user_id, first_name, last_name, date_of_birth, abo_type, rh_factor, primary_phone, email_address, latitude, longitude, is_active, is_deferred)
VALUES
    ('d0000000-0000-0000-0000-000000000001', 'auth0|marcus_vance_01', 'Marcus', 'Vance', '1992-05-14', 'O', 'NEGATIVE', '+1-555-0301', 'marcus.vance@example.com', 37.7750, -122.4183, TRUE, FALSE),
    ('d0000000-0000-0000-0000-000000000002', 'auth0|jane_smith_02', 'Jane', 'Smith', '1996-11-20', 'A', 'POSITIVE', '+1-555-0302', 'jane.smith@example.com', 37.7800, -122.4100, TRUE, FALSE),
    ('d0000000-0000-0000-0000-000000000003', 'auth0|elena_rostova_03', 'Elena', 'Rostova', '1988-03-10', 'B', 'POSITIVE', '+1-555-0303', 'elena.rostova@example.com', 37.7900, -122.4000, TRUE, FALSE)
ON CONFLICT (auth_user_id) DO NOTHING;

-- Insert Historical Donation for Marcus Vance (2024-12-25 WHOLE_BLOOD)
INSERT INTO bdcn_core.donation_events (donation_id, donor_id, hospital_id, donation_type, units_collected, collected_at, phlebotomist_license_id, hemoglobin_level, blood_pressure_systolic, blood_pressure_diastolic)
VALUES
    ('e0000000-0000-0000-0000-000000000001', 'd0000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000001', 'WHOLE_BLOOD', 1.0, '2024-12-25 10:00:00+00', 'PHLEB-9981', 14.5, 120, 80)
ON CONFLICT DO NOTHING;

-- Insert Sample ISBT 128 Blood Inventory
INSERT INTO bdcn_core.inventory_items (item_id, hospital_id, din_number, component_type, abo_type, rh_factor, collection_date, expiration_date, storage_temp_celsius, status)
VALUES
    ('b0000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000001', 'W036525000101', 'RED_BLOOD_CELLS', 'O', 'NEGATIVE', CURRENT_TIMESTAMP - INTERVAL '5 days', CURRENT_TIMESTAMP + INTERVAL '30 days', 4.0, 'AVAILABLE'),
    ('b0000000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000001', 'W036525000102', 'PLATELETS', 'A', 'POSITIVE', CURRENT_TIMESTAMP - INTERVAL '1 day', CURRENT_TIMESTAMP + INTERVAL '4 days', 22.0, 'AVAILABLE')
ON CONFLICT (din_number) DO NOTHING;
