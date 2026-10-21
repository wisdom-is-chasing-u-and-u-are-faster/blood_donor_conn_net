-- ANSI SQL DML Seeds for Blood Donor Connection Network (BDCN)

INSERT INTO donors (name, username, age, gender, blood_group, district, last_donation, donation_count)
VALUES
    ('Jane Smith', 'janesmith', 28, 'Female', 'O-', 'Downtown', '2025-11-15', 5),
    ('John Doe', 'johndoe', 34, 'Male', 'A+', 'North District', '2025-08-20', 2),
    ('Alice Johnson', 'alicejohnson', 30, 'Female', 'B+', 'East Valley', '2026-01-10', 4),
    ('Bob Lee', 'boblee', 42, 'Male', 'AB-', 'West Hills', '2025-12-05', 1);

INSERT INTO requests (hospital_name, patient_name, blood_type, units, urgency, district, filename, status, notes)
VALUES
    ('General Hospital', 'Sarah Connor', 'A+', 10, 'Emergency', 'Downtown', 'compliance_doc_A.pdf', 'Approved', 'Trauma ward requirement'),
    ('General Hospital', 'Marcus Wright', 'O-', 4, 'Urgent', 'North District', 'compliance_doc_B.pdf', 'Pending', 'Pediatric surgery necessity'),
    ('St. Jude Medical Center', 'Elena Fisher', 'B+', 2, 'Routine', 'East Valley', 'medical_report_C.pdf', 'Pending', 'Scheduled orthopedic transfusion');

INSERT INTO hotspots (district, count, blood_type, distance, top, left)
VALUES
    ('Downtown', 24, 'O-', 8, 30, 40),
    ('North District', 15, 'A+', 12, 55, 65),
    ('East Valley', 8, 'B+', 22, 70, 30),
    ('South Coast', 19, 'O+', 15, 45, 20),
    ('West Hills', 11, 'AB-', 35, 20, 80);

INSERT INTO notifications (title, message, read)
VALUES
    ('Emergency Blood Request Approved', 'Demand #1 for A+ blood at General Hospital is approved and dispatched.', 0),
    ('Welcome to BDCN', 'Thank you for joining the Blood Donor Connection Network.', 1);
