-- Baseline Seed Data for BDCN Platform

INSERT OR IGNORE INTO users (id, username, email, full_name, role, provider, blood_type, district) VALUES
(1, 'johndoe', 'john.doe@example.com', 'John Doe', 'donor', 'google', 'O+', 'Downtown'),
(2, 'janesmith', 'jane.smith@example.com', 'Jane Smith', 'recipient', 'apple', 'O-', 'North District'),
(3, 'admin_clara', 'clara.admin@example.com', 'Clara Barton', 'admin', 'local', 'A+', 'Central');

INSERT OR IGNORE INTO donors (id, user_id, blood_type, status, district, cluster_id, total_donations, gamification_points, current_tier) VALUES
(1, 1, 'O+', 'Available', 'Downtown', 'cluster_dt_01', 5, 250, 'Silver'),
(2, NULL, 'A+', 'Available', 'Downtown', 'cluster_dt_01', 3, 150, 'Bronze'),
(3, NULL, 'B+', 'Available', 'North District', 'cluster_nd_02', 12, 600, 'Gold'),
(4, NULL, 'AB+', 'Available', 'East District', 'cluster_ed_03', 2, 100, 'Bronze');

INSERT OR IGNORE INTO donor_clusters (id, cluster_id, district, centroid_lat, centroid_lng, donor_count, density_tier) VALUES
(1, 'cluster_dt_01', 'Downtown District', 37.77, -122.42, 18, 'High'),
(2, 'cluster_nd_02', 'North District', 37.79, -122.40, 12, 'Medium'),
(3, 'cluster_ed_03', 'East Bay Cluster', 37.80, -122.27, 24, 'High'),
(4, 'cluster_sd_04', 'South Bay Area', 37.33, -121.89, 9, 'Low');

INSERT OR IGNORE INTO achievements (id, code, title, description, badge_icon, points_reward, tier) VALUES
(1, 'FIRST_DROP', 'First Drop', 'Completed your initial whole blood donation.', '🩸', 50, 'Bronze'),
(2, 'LIFESAVER', 'Lifesaver', 'Donated 3 or more times to emergency alerts.', '⭐', 150, 'Silver'),
(3, 'CHAMPION', 'Community Champion', 'Achieved 5 donations and inspired 3 peers.', '🏆', 300, 'Gold'),
(4, 'CENTURY_CLUB', 'Century Club', 'Over 10 units donated across community drives.', '👑', 500, 'Platinum');

INSERT OR IGNORE INTO user_achievements (id, user_id, achievement_id, unlocked_at) VALUES
(1, 1, 1, '2026-08-15 10:00:00'),
(2, 1, 2, '2026-09-20 14:30:00'),
(3, 1, 3, '2026-10-10 09:15:00');

INSERT OR IGNORE INTO medical_documents (id, user_id, filename, file_path, document_type, verification_status, notes) VALUES
(1, 1, 'donor_eligibility_attestation.pdf', 'uploads/donor_eligibility_attestation.pdf', 'Eligibility Form', 'Verified', 'Pre-screened health questionnaire approved.'),
(2, 1, 'serology_clearance.pdf', 'uploads/serology_clearance.pdf', 'Lab Serology Test', 'Verified', 'Non-reactive panels on all infectious markers.');

INSERT OR IGNORE INTO blood_requests (id, recipient_name, hospital, blood_type, units, urgency, status, district) VALUES
(1, 'Jane Smith', 'General Hospital', 'O-', 2, 'Emergency', 'Pending Donor Match', 'Downtown'),
(2, 'Robert Taylor', 'Mercy Medical Center', 'A+', 4, 'Standard', 'Pending Donor Match', 'North District'),
(3, 'Sarah Connor', 'St. Jude Clinic', 'B+', 1, 'Urgent', 'Donor Matched', 'East District');

INSERT OR IGNORE INTO audit_logs (id, action, details, user) VALUES
(1, 'SYSTEM_STARTUP', 'Relational database schema and baseline clusters initialized.', 'System'),
(2, 'USER_REGISTER', 'User John Doe registered via Google Social Login.', 'GoogleAuth'),
(3, 'DOCUMENT_UPLOAD', 'Medical eligibility document uploaded by user 1.', 'John Doe');
