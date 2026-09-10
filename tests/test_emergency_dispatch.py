"""
Test Suite for Emergency Dispatch, SQS Worker, Notifications & Security Encryption
(ARCH-1192, ARCH-1193, ARCH-1194, ARCH-1195, ARCH-1196)
"""
import pytest
from services.dispatch_service import DispatchStateMachine
from services.security_service import SecurityService


@pytest.fixture
def dispatch_system():
    return DispatchStateMachine()


@pytest.fixture
def sec_system():
    return SecurityService()


def test_emergency_dispatch_state_machine_lifecycle(dispatch_system):
    # 1. Create dispatch
    disp = dispatch_system.create_dispatch(
        hospital_id="hosp-1",
        severity="LEVEL_1_CATASTROPHIC",
        required_abo="O",
        required_rh="NEGATIVE",
        units_requested=4,
        initiated_by="Dr. Sarah Lin"
    )
    disp_id = disp["dispatch_id"]
    assert disp["status"] == "INITIATED"

    # 2. Transition to MATCHING
    ok, err = dispatch_system.transition_status(disp_id, "MATCHING", "Dr. Sarah Lin")
    assert ok is True

    # 3. Transition to DISPATCHED
    ok, err = dispatch_system.transition_status(disp_id, "DISPATCHED", "System")
    assert ok is True

    # 4. Invalid transition attempt (e.g. back to INITIATED)
    invalid_ok, invalid_err = dispatch_system.transition_status(disp_id, "INITIATED", "User")
    assert invalid_ok is False
    assert "INVALID_STATE_TRANSITION" in invalid_err

    # 5. Transition to ACCEPTED -> IN_TRANSIT -> FULFILLED
    dispatch_system.transition_status(disp_id, "ACCEPTED", "Donor Marcus")
    dispatch_system.transition_status(disp_id, "IN_TRANSIT", "Courier")
    dispatch_system.transition_status(disp_id, "FULFILLED", "Hospital Staff")

    final_disp = dispatch_system.get_dispatch(disp_id)
    assert final_disp["status"] == "FULFILLED"


def test_sqs_worker_and_dlq_redrive(dispatch_system):
    msg_id = dispatch_system.enqueue_sqs_message({
        "donor_id": "donor-1",
        "phone": "+15550100",
        "text": "Emergency O-Neg Blood Alert for Memorial Trauma!"
    })

    # Simulate 2 failures -> retrying
    r1 = dispatch_system.process_sqs_worker(fail_simulation=True)
    assert r1["status"] == "RETRYING"

    r2 = dispatch_system.process_sqs_worker(fail_simulation=True)
    assert r2["status"] == "RETRYING"

    # 3rd failure -> routed to DLQ
    r3 = dispatch_system.process_sqs_worker(fail_simulation=True)
    assert r3["status"] == "DLQ_ROUTED"
    assert len(dispatch_system._dlq_queue) == 1

    # Redrive DLQ back into main queue
    redriven = dispatch_system.redrive_dlq()
    assert redriven == 1
    assert len(dispatch_system._dlq_queue) == 0

    # Successful processing & multi-channel notification
    success_proc = dispatch_system.process_sqs_worker(fail_simulation=False)
    assert success_proc["status"] == "PROCESSED"
    assert len(dispatch_system._notifications) == 1
    assert "FCM_PUSH" in dispatch_system._notifications[0]["channels"]


def test_field_level_ephi_encryption_and_log_sanitization(sec_system):
    sensitive_medical_note = "Donor Marcus Vance, SSN: 123-45-6789, Phone: 555-123-4567, HIV/HepB Negative"
    
    # Encrypt & Decrypt
    encrypted = sec_system.encrypt_ephi_field(sensitive_medical_note)
    assert encrypted.startswith("enc::")
    assert "123-45-6789" not in encrypted

    decrypted = sec_system.decrypt_ephi_field(encrypted)
    assert decrypted == sensitive_medical_note

    # Log Sanitization
    log_line = "Failed donor check for email: marcus@example.com, phone: 555-123-4567, ssn: 123-45-6789"
    sanitized = sec_system.sanitize_log_message(log_line)
    assert "[REDACTED_SSN]" in sanitized
    assert "[REDACTED_PHONE]" in sanitized
    assert "[REDACTED_EMAIL]" in sanitized


def test_s3_worm_compliance_export_and_integrity_verifier(sec_system):
    records = [
        {"donation_id": "don-1", "units": 1, "status": "COMPLETED"},
        {"donation_id": "don-2", "units": 2, "status": "COMPLETED"}
    ]
    export = sec_system.create_worm_export("EXPORT-2025-001", records, "compliance_officer")
    assert export["record_count"] == 2
    assert export["is_locked"] is True

    # Verify integrity
    is_valid, err = sec_system.verify_worm_export("EXPORT-2025-001")
    assert is_valid is True
    assert err is None
