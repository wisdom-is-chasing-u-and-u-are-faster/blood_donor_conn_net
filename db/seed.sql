-- DML Baseline Seed Data for Blood Donor Connection Network (BDCN)

INSERT OR IGNORE INTO donors (id, name, email, blood_type, location, latitude, longitude, available, last_donation_date)
VALUES
(1, 'John Doe', 'john.doe@example.com', 'O-', 'San Francisco, CA', 37.7749, -122.4194, 1, '2024-05-15'),
(2, 'Jane Smith', 'jane.smith@example.com', 'A+', 'Oakland, CA', 37.8044, -122.2712, 1, '2024-06-20'),
(3, 'Alex Johnson', 'alex.j@example.com', 'B+', 'San Jose, CA', 37.3382, -121.8863, 0, '2024-07-01'),
(4, 'Maria Garcia', 'maria.g@example.com', 'AB+', 'Berkeley, CA', 37.8715, -122.2730, 1, '2024-06-10');

INSERT OR IGNORE INTO hotspots (id, district, latitude, longitude, donor_count, blood_types)
VALUES
(1, 'Downtown San Francisco', 37.77, -122.42, 14, 'O-, A+, B+'),
(2, 'East Bay Metro', 37.80, -122.27, 8, 'A+, AB+, O-'),
(3, 'Silicon Valley South', 37.34, -121.89, 12, 'B+, O-, A+');

INSERT OR IGNORE INTO connection_requests (id, request_code, recipient_id, blood_type, location, message, document_name, status, submitted_at, reminder_sent)
VALUES
(1, 'REQ-10234', 'REC-9876', 'O-', 'San Francisco, CA', 'Urgent need for scheduled surgery patient letter enclosed.', 'hospital_letter.pdf', 'Pending', datetime('now', '-3 hours'), 1),
(2, 'REQ-10233', 'REC-9875', 'A+', 'Oakland, CA', 'Platelet and whole blood requirement.', 'clinic_requisition.pdf', 'Pending', datetime('now', '-30 minutes'), 0),
(3, 'REQ-10232', 'REC-9870', 'B+', 'San Jose, CA', 'Regular transfusion support.', 'medical_necessity_cert.pdf', 'Approved', datetime('now', '-1 day'), 0);

INSERT OR IGNORE INTO notifications (id, user_id, title, message, read_status)
VALUES
(1, 'admin', 'Urgent Reminder: Pending Request REQ-10234', 'Request REQ-10234 has been pending review for over 2 hours.', 0),
(2, 'REC-9876', 'Request Received', 'Your connection request REQ-10234 was submitted and is pending administrator review.', 1);
