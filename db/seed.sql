-- db/seed.sql — Baseline seed data for BDCN Platform

INSERT OR IGNORE INTO users (id, email, full_name, role) VALUES
(1, 'donor@example.com', 'Jane Doe', 'donor'),
(2, 'admin@example.com', 'Admin Officer', 'admin'),
(3, 'recipient@example.com', 'John Smith', 'recipient');

INSERT OR IGNORE INTO donor_profiles (id, user_id, blood_type, contact_phone, location, availability_status) VALUES
(1, 1, 'O-', '+1-555-0199', 'Downtown Metro', 'Available');

INSERT OR IGNORE INTO donation_history (id, donor_id, donation_date, units, location) VALUES
(1, 1, '2025-11-15', 1, 'Memorial Blood Center'),
(2, 1, '2025-08-20', 1, 'Community Red Cross Drive');

INSERT OR IGNORE INTO blood_requests (id, recipient_name, blood_type, units, hospital_name, location, urgency, status) VALUES
(1, 'Jane Smith', 'O-', 2, 'City General Hospital', 'Downtown', 'Emergency', 'Pending Admin Review'),
(2, 'Michael Brown', 'A+', 3, 'Northside Clinic', 'North District', 'Urgent', 'Approved');

INSERT OR IGNORE INTO pledges (id, request_id, donor_id, donor_name, donor_phone, status) VALUES
(1, 2, 1, 'Jane Doe', '+1-555-0199', 'Pledged');

INSERT OR IGNORE INTO anonymized_messages (id, request_id, sender_role, content) VALUES
(1, 2, 'Recipient', 'Thank you for pledging to donate! When might you be arriving at Northside Clinic?'),
(2, 2, 'Donor', 'I am on my way and should arrive by 2:00 PM.');
