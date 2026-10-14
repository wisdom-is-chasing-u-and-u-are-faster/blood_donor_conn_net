-- BDCN Core Platform DML Seed Data

INSERT INTO users (username, role, name, email) VALUES
('janesmith', 'donor', 'Jane Smith', 'jane.smith@example.org'),
('johndoe', 'donor', 'John Doe', 'john.doe@example.org'),
('Mercy Hospital', 'hospital', 'Mercy General Hospital', 'contact@mercyhospital.org'),
('admin_district', 'admin', 'District Health Admin', 'admin@bdcn.health')
ON CONFLICT (username) DO NOTHING;

INSERT INTO donors (username, name, age, gender, blood_group, last_donation, donation_count, total_points, lives_impacted) VALUES
('janesmith', 'Jane Smith', 28, 'Female', 'O-', '2025-11-15', 5, 1250, 5),
('johndoe', 'John Doe', 34, 'Male', 'A+', '2025-08-20', 2, 450, 2)
ON CONFLICT (username) DO NOTHING;

INSERT INTO blood_requests (hospital, blood_type, units, filename, status, urgency, district, notes) VALUES
('General Hospital', 'A+', 10, 'compliance_doc_A.pdf', 'Approved', 'Critical', 'Downtown', 'Emergency surgery requisition'),
('General Hospital', 'O-', 4, 'compliance_doc_B.pdf', 'Pending', 'High', 'North District', 'ICU blood requirement'),
('St. Jude Clinic', 'B+', 2, 'compliance_doc_C.pdf', 'Pending', 'Medium', 'East Valley', 'Planned transfusion');

INSERT INTO hotspots (district, count, blood_type, distance, latitude_coarse, longitude_coarse) VALUES
('Downtown', 24, 'O-', 8, 37.77, -122.42),
('North District', 15, 'A+', 12, 37.80, -122.40),
('East Valley', 8, 'B+', 22, 37.75, -122.35),
('South Coast', 19, 'O+', 15, 37.70, -122.45),
('West Hills', 11, 'AB-', 35, 37.82, -122.50);

INSERT INTO badges (username, badge_name, description, earned) VALUES
('janesmith', 'Gold Guardian', 'Awarded for completing at least 5 voluntary donations.', TRUE),
('janesmith', 'Silver Savior', 'Awarded for completing at least 3 voluntary donations.', TRUE),
('janesmith', 'Bronze Savior', 'Awarded for completing at least 1 voluntary donation.', TRUE),
('johndoe', 'Bronze Savior', 'Awarded for completing at least 1 voluntary donation.', TRUE);

INSERT INTO audit_logs (action, details, username) VALUES
('SYSTEM STARTUP', 'BDCN Core Platform service initialized with 12-factor configuration.', 'System'),
('DEMAND APPROVED', 'Emergency demand #1 (A+, 10 units) approved by admin.', 'admin_district');
