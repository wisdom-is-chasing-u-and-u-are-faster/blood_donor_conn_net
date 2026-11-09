-- Seed Data for Blood Donor Connection Network
-- ARCH-7525: Baseline and Edge Case Seed Donors

INSERT INTO donors (id, full_name, email, phone_number, blood_group, last_donation_date, is_active)
VALUES
    (1001, 'Donor Cooled Down 90d', 'donor1001@example.com', '+15550001001', 'O+', '2025-12-28', TRUE),
    (1002, 'Donor Cooled Down 56d', 'donor1002@example.com', '+15550001002', 'A+', '2026-01-31', TRUE),
    (1003, 'Donor Ineligible 55d', 'donor1003@example.com', '+15550001003', 'B+', '2026-02-01', TRUE),
    (1004, 'Donor Cooled Down 57d', 'donor1004@example.com', '+15550001004', 'AB+', '2026-01-30', TRUE),
    (1005, 'Donor Same Day 0d', 'donor1005@example.com', '+15550001005', 'O-', '2026-03-28', TRUE),
    (1006, 'Donor Mid Cooldown 14d', 'donor1006@example.com', '+15550001006', 'A-', '2026-03-14', TRUE),
    (1007, 'Donor First Time Null', 'donor1007@example.com', '+15550001007', 'O+', NULL, TRUE),
    (1010, 'Donor Leap Year 2024', 'donor1010@example.com', '+15550001010', 'B-', '2024-01-25', TRUE),
    (1011, 'Donor Century 2000', 'donor1011@example.com', '+15550001011', 'AB-', '2000-01-05', TRUE),
    (1015, 'Donor Cold Historic 5y', 'donor1015@example.com', '+15550001015', 'O+', '2021-03-28', TRUE)
ON CONFLICT (id) DO NOTHING;
