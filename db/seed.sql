-- Blood Donor Connection Network (BDCN) Seed Data

INSERT INTO users (username, role, email) VALUES
('Mercy Hospital', 'hospital', 'coordinator@mercyhospital.org'),
('admin_district', 'admin', 'admin.central@bdcn-health.gov'),
('johndoe', 'donor', 'johndoe@example.com'),
('janedoe', 'donor', 'janedoe@example.com'),
('cooldonor', 'donor', 'cooldonor@example.com')
ON CONFLICT (username) DO NOTHING;

INSERT INTO donors (name, username, age, gender, blood_group, last_donation, donation_count, district, availability_status, cooldown_until) VALUES
('John Doe', 'johndoe', 29, 'Male', 'A+', '2025-11-15', 3, 'Downtown', 'Available', NULL),
('Jane Smith', 'janesmith', 34, 'Female', 'O-', '2025-08-20', 5, 'North District', 'Available', NULL),
('Alice Brown', 'aliceb', 22, 'Female', 'B+', '2026-01-10', 1, 'West Hills', 'Unavailable', NULL),
('Liam Lifesaver', 'cooldonor', 26, 'Male', 'O+', '2026-11-10', 4, 'Downtown', 'In Recovery Cooldown', '2027-01-05 00:00:00')
ON CONFLICT (username) DO NOTHING;

INSERT INTO demands (hospital, blood_type, units, filename, status, urgency, district, notes) VALUES
('General Hospital', 'A+', 10, 'compliance_doc_A.pdf', 'Approved', 'Emergency', 'Downtown', 'Acute trauma unit requirement'),
('General Hospital', 'O-', 4, 'compliance_doc_B.pdf', 'Pending', 'Urgent', 'North District', 'Scheduled pediatric surgery');

INSERT INTO alerts (hospital, blood_type, status, district) VALUES
('General Hospital', 'A+', 'Active', 'Downtown');

INSERT INTO donor_commitments (request_id, donor_id, donor_username, anonymized_id, eta, status) VALUES
(1, 2, 'janesmith', 'Donor #A1B2C3', 'Within 1 hour', 'Committed');
