"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   unit
Source:  test_strategy/plans/cloned_repo__unit.json
Generated: 2026-10-28T14:50:00Z
"""
from datetime import datetime, timedelta
import pytest
from app import app
from services.dispatch_service import DispatchStateMachine
from services.spatial_service import RedisGeospatialCache, haversine_distance_km, get_bounding_box
from services.telemetry_service import parse_isbt128_barcode
from services.reservation_service import ReservationEngine
from services.eligibility_service import fn_validate_donor_eligibility
from services.audit_service import AuditLedger
from services.security_service import SecurityService


def test_cloned_repo_unit_001():
    """DispatchStateMachine creates dispatch and sends multi-channel notification.

    test_id: cloned_repo__unit__001
    target: DispatchStateMachine.create_dispatch
    requirement_id: BO-1
    ac_ids: BO-1-AC-1
    """
    engine = DispatchStateMachine()
    disp = engine.create_dispatch(
        hospital_id="hosp-1",
        severity="LEVEL_1_CATASTROPHIC",
        required_abo="O",
        required_rh="NEGATIVE",
        units_requested=4,
        initiated_by="Dr. Sarah Lin"
    )
    assert disp["status"] == "INITIATED"
    assert disp["dispatch_id"].startswith("disp-")
    notif = engine.send_multi_channel_notification(
        recipient_id="marcus_vance",
        phone="+15550100",
        message_text="Urgent O- blood needed"
    )
    assert notif["status"] == "DELIVERED"
    assert "FCM_PUSH" in notif["channels"]
    assert "TWILIO_SMS" in notif["channels"]


def test_cloned_repo_unit_002():
    """DispatchStateMachine redrives failed SQS messages from DLQ.

    test_id: cloned_repo__unit__002
    target: DispatchStateMachine.redrive_dlq
    requirement_id: BO-1
    ac_ids: BO-1-AC-2
    """
    engine = DispatchStateMachine()
    msg_id = engine.enqueue_sqs_message({"donor_id": "d1", "text": "Alert"})
    assert msg_id.startswith("msg-")
    r1 = engine.process_sqs_worker(fail_simulation=True)
    assert r1["status"] == "RETRYING"
    r2 = engine.process_sqs_worker(fail_simulation=True)
    assert r2["status"] == "RETRYING"
    r3 = engine.process_sqs_worker(fail_simulation=True)
    assert r3["status"] == "DLQ_ROUTED"
    redriven = engine.redrive_dlq()
    assert redriven == 1
    r4 = engine.process_sqs_worker(fail_simulation=False)
    assert r4["status"] == "PROCESSED"


def test_cloned_repo_unit_003():
    """RedisGeospatialCache geoadd and geosearch match donors within 15 km radius.

    test_id: cloned_repo__unit__003
    target: RedisGeospatialCache.geosearch
    requirement_id: BO-2, BO-4
    ac_ids: BO-2-AC-1, BO-2-AC-2, BO-4-AC-2
    """
    cache = RedisGeospatialCache()
    cache.geoadd("donor_near", 37.7850, -122.4150, {
        "name": "Marcus Vance",
        "abo_type": "O",
        "rh_factor": "NEGATIVE",
        "rare_antigen_profile": {"kell": "negative"}
    })
    cache.geoadd("donor_far", 38.2000, -122.4150, {
        "name": "Far Donor",
        "abo_type": "O",
        "rh_factor": "NEGATIVE",
        "rare_antigen_profile": {"kell": "negative"}
    })
    bbox = get_bounding_box(37.7749, -122.4194, 15.0)
    assert len(bbox) == 4
    dist = haversine_distance_km(37.7749, -122.4194, 37.7850, -122.4150)
    assert dist < 15.0
    matches = cache.geosearch(37.7749, -122.4194, radius_km=15.0, abo_type="O", rh_factor="NEGATIVE", rare_antigen="kell")
    assert len(matches) == 1
    assert matches[0]["member_id"] == "donor_near"


def test_cloned_repo_unit_004():
    """parse_isbt128_barcode extracts blood product telemetry and expiration.

    test_id: cloned_repo__unit__004
    target: parse_isbt128_barcode
    requirement_id: BO-3
    ac_ids: BO-3-AC-1
    """
    ok, parsed, err = parse_isbt128_barcode("=W03652500010100")
    assert ok is True
    assert err is None
    assert parsed["din_number"] == "W036525000101"
    assert parsed["facility_code"] == "W0365"
    ok_bad, parsed_bad, err_bad = parse_isbt128_barcode("SHORT")
    assert ok_bad is False
    assert parsed_bad is None
    assert err_bad == "INVALID_ISBT128_LENGTH"


def test_cloned_repo_unit_005():
    """ReservationEngine auto-releases expired 120-minute inventory leases.

    test_id: cloned_repo__unit__005
    target: ReservationEngine.reconcile_expired_leases
    requirement_id: BO-3, UC-001
    ac_ids: BO-3-AC-2, UC-001-AC-1, UC-001-AC-2
    """
    engine = ReservationEngine()
    engine.seed_item("W036525000555", "RED_BLOOD_CELLS", "O", "NEGATIVE", "hosp-1")
    assert engine.get_available_count("hosp-1", "O", "NEGATIVE") == 1
    past_time = datetime.utcnow() - timedelta(minutes=125)
    ok, res, err = engine.create_reservation("hosp-1", "ENC-100", "W036525000555", reserved_at=past_time)
    assert ok is True
    assert err is None
    assert res["status"] == "ACTIVE"
    assert engine.get_available_count("hosp-1", "O", "NEGATIVE") == 0
    expired = engine.reconcile_expired_leases()
    assert len(expired) == 1
    assert expired[0]["status"] == "EXPIRED"
    assert engine.get_available_count("hosp-1", "O", "NEGATIVE") == 1


def test_cloned_repo_unit_006():
    """fn_validate_donor_eligibility enforces 56d, 112d, and 7d rolling intervals.

    test_id: cloned_repo__unit__006
    target: fn_validate_donor_eligibility
    requirement_id: BO-4
    ac_ids: BO-4-AC-1
    """
    donor = {"donor_id": "d-1", "is_deferred": False}
    recent_wb = [{"donation_type": "WHOLE_BLOOD", "collected_at": "2026-10-01T10:00:00Z"}]
    res_ineligible = fn_validate_donor_eligibility(donor, recent_wb, donation_type="WHOLE_BLOOD", target_date="2026-10-28T10:00:00Z")
    assert res_ineligible["isEligible"] is False
    assert res_ineligible["blockReason"] == "MINIMUM_DONATION_INTERVAL_NOT_MET"
    res_eligible = fn_validate_donor_eligibility(donor, recent_wb, donation_type="WHOLE_BLOOD", target_date="2026-12-01T10:00:00Z")
    assert res_eligible["isEligible"] is True
    recent_dr = [{"donation_type": "DOUBLE_RED_CELLS", "collected_at": "2026-09-01T10:00:00Z"}]
    res_dr = fn_validate_donor_eligibility(donor, recent_dr, donation_type="DOUBLE_RED_CELLS", target_date="2026-10-28T10:00:00Z")
    assert res_dr["isEligible"] is False
    recent_pl = [{"donation_type": "PLATELETS", "collected_at": "2026-10-25T10:00:00Z"}]
    res_pl = fn_validate_donor_eligibility(donor, recent_pl, donation_type="PLATELETS", target_date="2026-10-28T10:00:00Z")
    assert res_pl["isEligible"] is False


def test_cloned_repo_unit_007():
    """AuditLedger records tamper-evident hash-chained mutations and verifies integrity.

    test_id: cloned_repo__unit__007
    target: AuditLedger.verify_integrity
    requirement_id: BR-002
    ac_ids: BR-002-AC-1
    """
    ledger = AuditLedger()
    e1 = ledger.record_mutation("donors", "d-1", "INSERT", "admin", new_state={"status": "ACTIVE"})
    e2 = ledger.record_mutation("donors", "d-1", "UPDATE", "admin", old_state={"status": "ACTIVE"}, new_state={"status": "DEFERRED"})
    assert e2["previous_hash"] == e1["checksum_signature"]
    ok, err = ledger.verify_integrity()
    assert ok is True
    assert err is None
    ledger._logs[0]["new_state"] = {"status": "TAMPERED"}
    ok_tampered, err_tampered = ledger.verify_integrity()
    assert ok_tampered is False
    assert "Tampered record" in err_tampered


def test_cloned_repo_unit_008():
    """SecurityService encrypts ePHI fields and verifies WORM compliance exports.

    test_id: cloned_repo__unit__008
    target: SecurityService.create_worm_export
    requirement_id: BR-002
    ac_ids: BR-002-AC-2
    """
    sec = SecurityService()
    cipher = sec.encrypt_ephi_field("123-45-6789")
    assert cipher.startswith("enc::")
    assert sec.decrypt_ephi_field(cipher) == "123-45-6789"
    sanitized = sec.sanitize_log_message("Patient SSN 123-45-6789 email patient@example.com")
    assert "[REDACTED_SSN]" in sanitized
    assert "[REDACTED_EMAIL]" in sanitized
    export = sec.create_worm_export("WORM-TEST-1", [{"id": 1}], "auditor")
    assert export["is_locked"] is True
    ok, err = sec.verify_worm_export("WORM-TEST-1")
    assert ok is True
    assert err is None
