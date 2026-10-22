-- BDCN Seed Data for Development and Unit Verification

INSERT OR IGNORE INTO users (id, username, email, role, provider) VALUES
('usr-001', 'admin_district', 'admin@bdcn.org', 'admin', 'local'),
('usr-002', 'user-id-12345', 'user_a@email.com', 'donor', 'google'),
('usr-003', 'user-id-67890', 'user_b@email.com', 'donor', 'apple'),
('usr-004', 'user-id-abcde', 'user_c@email.com', 'donor', 'facebook');

INSERT OR IGNORE INTO donors (id, user_id, name, age, gender, blood_group, district, donation_count, last_donation) VALUES
('dnr-001', 'usr-002', 'Jane Smith', 28, 'Female', 'O-', 'Downtown', 5, '2025-11-15'),
('dnr-002', 'usr-003', 'John Doe', 34, 'Male', 'A+', 'North District', 2, '2025-08-20'),
('dnr-003', 'usr-004', 'Alex Rivera', 29, 'Non-Binary', 'B+', 'East Valley', 4, '2026-01-10');

INSERT OR IGNORE INTO donor_hotspots (id, district, coarse_latitude, coarse_longitude, donor_count, primary_blood_types, distance_km, urgency_level) VALUES
(1, 'Downtown District', 37.77, -122.41, 24, 'O-, A+', 8.0, 'High'),
(2, 'North District', 37.80, -122.43, 15, 'A+, B+', 12.0, 'Moderate'),
(3, 'East Valley', 37.75, -122.39, 8, 'B+, AB-', 22.0, 'Normal'),
(4, 'South Coast', 37.71, -122.45, 19, 'O+, A-', 15.0, 'High'),
(5, 'West Hills', 37.76, -122.49, 11, 'AB-, O-', 35.0, 'Normal');

INSERT OR IGNORE INTO documents (id, user_id, user_email, document_type, filename, encrypted_blob_uri, status, district, consent_given, uploaded_at, expires_at) VALUES
('doc-101', 'usr-002', 'user_a@email.com', 'Donor ID Card', 'donor_id_card_scan.pdf', 'gs://bdcn-encrypted-docs-vault/documents/doc-101.enc', 'Pending', 'Downtown', 1, '2023-10-26 10:30:00', datetime('now', '+30 days')),
('doc-102', 'usr-003', 'user_b@email.com', 'Medical Clearance Form', 'clearance_med.pdf', 'gs://bdcn-encrypted-docs-vault/documents/doc-102.enc', 'Pending', 'North District', 1, '2023-10-26 09:15:00', datetime('now', '+30 days')),
('doc-103', 'usr-004', 'user_c@email.com', 'Other Identification', 'govt_id_verification.pdf', 'gs://bdcn-encrypted-docs-vault/documents/doc-103.enc', 'Pending', 'East Valley', 1, '2023-10-27 09:00:00', datetime('now', '+30 days'));

INSERT OR IGNORE INTO verifications (id, document_id, status) VALUES
('ver-001', 'doc-101', 'Pending'),
('ver-002', 'doc-102', 'Pending'),
('ver-003', 'doc-103', 'Pending');

INSERT OR IGNORE INTO audit_logs (id, action, details, user, timestamp) VALUES
(1, 'SYSTEM STARTUP', 'BDCN Relational Database and Core Services initialized.', 'System', '2026-10-22 08:00:00'),
(2, 'DOCUMENT UPLOAD', 'Uploaded Donor ID Card for user_a@email.com. Encrypted at rest.', 'user_a@email.com', '2023-10-26 10:30:00'),
(3, 'DOCUMENT UPLOAD', 'Uploaded Medical Clearance Form for user_b@email.com. Encrypted at rest.', 'user_b@email.com', '2023-10-26 09:15:00');
