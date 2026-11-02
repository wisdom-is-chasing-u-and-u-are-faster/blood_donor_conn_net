-- Seed Data for BDCN
INSERT OR IGNORE INTO users (id, username, role) VALUES (1, 'admin_district', 'District Administrator');
INSERT OR IGNORE INTO users (id, username, role) VALUES (2, 'john_donor', 'Donor');
INSERT OR IGNORE INTO users (id, username, role) VALUES (3, 'jane_recipient', 'Recipient');

INSERT OR IGNORE INTO donor_hotspots (id, city, district, centroid_lat, centroid_lng, donor_count, blood_types) VALUES 
(1, 'Springfield', 'District North', 39.78, -89.65, 14, 'O+, A+, B+'),
(2, 'Metropolis', 'Downtown Metro', 37.15, -88.73, 22, 'O-, AB+, B-'),
(3, 'Gotham', 'Gotham Harbor', 40.71, -74.00, 8, 'A-, O+, AB-');
