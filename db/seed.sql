-- DML Baseline Seed Data for BDCN

INSERT OR IGNORE INTO users (id, username, name, email, role, blood_group, h3_cluster, donation_count, last_donation_date)
VALUES 
(1, 'janesmith', 'Jane Smith', 'jane@example.com', 'donor', 'O-', '872830828ffffff', 5, '2025-11-15'),
(2, 'johndoe', 'John Doe', 'john@example.com', 'donor', 'A+', '87283082bffffff', 2, '2025-08-20'),
(3, 'admin_district', 'Pat Miller (District Admin)', 'pat@bdcn.org', 'admin', 'AB+', '872830828ffffff', 0, NULL);

INSERT OR IGNORE INTO blood_requests (id, case_id, recipient_name, blood_type, donation_type, units, urgency, h3_cluster, document_name, notes, status)
VALUES
(1, 'REQ-781A', 'City General Hospital', 'A+', 'Whole Blood', 10, 'Urgent', '872830828ffffff', 'medical_req_781.pdf', 'Scheduled surgery on Friday.', 'Pending'),
(2, 'REQ-780B', 'Community Blood Center', 'O-', 'Platelets', 4, 'Standard', '87283082bffffff', 'requisition_780b.png', 'Emergency platelet reserves required.', 'Pending'),
(3, 'REQ-779C', 'Metro Clinic', 'B+', 'Whole Blood', 2, 'Standard', '872830828ffffff', 'doc_779c.pdf', 'Post-op recovery replenishment.', 'Approved');

INSERT OR IGNORE INTO audit_logs (id, action, details, user)
VALUES
(1, 'SYSTEM STARTUP', 'BDCN database initialized with ANSI SQL schema and seed data.', 'System'),
(2, 'HOSPITAL DEMAND APPROVED', 'Demand #3 (B+, 2 units) approved. Notified nearby donors in H3 cluster.', 'admin_district');
