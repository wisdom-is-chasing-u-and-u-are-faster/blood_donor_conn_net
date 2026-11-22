-- Blood Donor Connection Network (BDCN) Seed Data
-- Compatible with SQLite and PostgreSQL

INSERT OR IGNORE INTO users (id, username, role, email) VALUES
(1, 'donor_john', 'donor', 'john@example.com'),
(2, 'donor_jane', 'donor', 'jane@example.com'),
(3, 'hospital_admin', 'hospital', 'admin@generalhospital.com'),
(4, 'district_admin', 'admin', 'district.admin@bdcn.org');

INSERT OR IGNORE INTO donors (id, name, username, age, gender, blood_group, last_donation, donation_count, district, availability_status) VALUES
(1, 'John Doe', 'donor_john', 28, 'Male', 'A+', '2026-08-15', 3, 'Downtown', 'Available'),
(2, 'Jane Smith', 'donor_jane', 32, 'Female', 'O-', '2026-10-01', 5, 'North District', 'Available');

INSERT OR IGNORE INTO demands (id, hospital, blood_type, units, filename, status, urgency, district, notes) VALUES
(1, 'General Hospital', 'A+', 10, 'compliance_doc_A.pdf', 'Approved', 'Emergency', 'Downtown', 'Immediate trauma response needed'),
(2, 'General Hospital', 'O-', 4, 'compliance_doc_B.pdf', 'Pending', 'Urgent', 'North District', 'Routine surgical backup units'),
(3, 'City Medical Center', 'B+', 6, 'compliance_doc_C.pdf', 'Approved', 'Emergency', 'East District', 'NICU blood replacement unit');

INSERT OR IGNORE INTO alerts (id, hospital, blood_type, status, district) VALUES
(1, 'General Hospital', 'A+', 'Active', 'Downtown'),
(2, 'City Medical Center', 'O-', 'Active', 'North District');
