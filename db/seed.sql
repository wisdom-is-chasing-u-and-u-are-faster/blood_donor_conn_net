-- Seed data for Donors and initial baseline
INSERT INTO donors (name, username, blood_group, is_verified, current_status, age, gender, weight, email, phone, district, last_donation, donation_count)
VALUES
('Elena Rodriguez', 'elena_r', 'O-', TRUE, 'active', 29, 'female', 58.5, 'elena.r@example.com', '(555) 234-5678', 'Downtown', '2025-08-01', 7),
('Marcus Chen', 'mchen', 'O+', TRUE, 'active', 35, 'male', 74.0, 'marcus.c@example.com', '(555) 345-6789', 'North District', '2025-07-15', 4),
('Sarah Jenkins', 'sjenkins', 'A+', TRUE, 'active', 26, 'female', 62.0, 'sarah.j@example.com', '(555) 456-7890', 'West Hills', '2025-06-10', 3),
('David Kim', 'dkim', 'B-', TRUE, 'active', 31, 'male', 68.5, 'david.k@example.com', '(555) 567-8901', 'Downtown', '2025-09-01', 5),
('Aaliyah Patel', 'apatel', 'AB+', TRUE, 'active', 24, 'female', 54.0, 'aaliyah.p@example.com', '(555) 678-9012', 'East Bay', '2025-05-20', 2),
('Michael Torres', 'mtorres', 'O-', FALSE, 'pending_verification', 22, 'male', 70.0, 'michael.t@example.com', '(555) 789-0123', 'South City', '2025-04-12', 1),
('Emily Watson', 'ewatson', 'A-', TRUE, 'active', 33, 'female', 59.0, 'emily.w@example.com', '(555) 890-1234', 'Central', '2025-07-28', 6);
