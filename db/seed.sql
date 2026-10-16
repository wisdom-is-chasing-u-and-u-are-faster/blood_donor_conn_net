-- Baseline seed data for Emergency Blood Requisitions and Digital Passes

INSERT OR IGNORE INTO emergency_requisitions (
    request_id, hospital_id, hospital_name, blood_type, units, urgency, latitude, longitude, radius_km, status, notes
) VALUES (
    'REQ-EMERG-2026-001',
    'HOSP-001',
    'City General Hospital',
    'O-',
    4,
    'Emergency',
    37.7749,
    -122.4194,
    15.0,
    'broadcast',
    'Trauma resuscitation encounter - Code Red'
);

INSERT OR IGNORE INTO donor_responses (
    response_id, request_id, donor_id, donor_username, action
) VALUES (
    'RESP-2026-001',
    'REQ-EMERG-2026-001',
    'DN-A8C4-E02B',
    'janesmith',
    'confirmed'
);

INSERT OR IGNORE INTO digital_check_in_passes (
    pass_id, response_id, request_id, donor_id, hospital_name, hospital_address, blood_type, appointment_time, qr_code_data, status
) VALUES (
    'PASS-2026-A8C4',
    'RESP-2026-001',
    'REQ-EMERG-2026-001',
    'DN-A8C4-E02B',
    'City General Hospital (123 Health St.)',
    '123 Health St., Trauma Transfusion Center, Bay 4',
    'O-',
    'October 26, 2024 at 3:45 PM',
    'BDCN:PASS:PASS-2026-A8C4:DN-A8C4-E02B:O-:EXP-45M',
    'ACTIVE'
);
