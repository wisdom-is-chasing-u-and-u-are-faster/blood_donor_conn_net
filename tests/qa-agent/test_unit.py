"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   unit
Source:  test_strategy/plans/cloned_repo__unit.json
Generated: 2026-10-29T15:00:00Z
"""
from datetime import datetime, timedelta
import pytest
from app import app, safe_float
from services.eligibility_service import fn_validate_donor_eligibility, parse_datetime
from services.spatial_service import RedisGeospatialCache, haversine_distance_km, get_bounding_box
from services.dispatch_service import DispatchStateMachine
from services.reservation_service import ReservationEngine
from services.telemetry_service import parse_isbt128_barcode
from services.audit_service import AuditLedger
from services.security_service import SecurityService


def test_cloned_repo_unit_001():
    """Verify donor rolling eligibility intervals for whole blood, double red cells, and platelets.

    test_id: cloned_repo__unit__001
    target: fn_validate_donor_eligibility
    requirement_id: REQ-002
    ac_ids: REQ-002-AC-1
    """
    donor = {"donor_id": "D-100", "username": "d100", "is_deferred": False}
    wb_ok = fn_validate_donor_eligibility(
        donor,
        [{"donation_type": "WHOLE_BLOOD", "collected_at": "2026-07-01T10:00:00Z"}],
        donation_type="WHOLE_BLOOD",
        target_date="2026-09-01T10:00:00Z",
    )
    assert wb_ok["isEligible"] is True
    assert wb_ok["daysRemaining"] == 0

    wb_Wait = fn_validate_donor_eligibility(
        donor,
        [{"donation_type": "WHOLE_BLOOD", "collected_at": "2026-08-20T10:00:00Z"}],
        donation_type="WHOLE_BLOOD",
        target_date="2026-09-01T10:00:00Z",
    )
    assert wb_Wait["isEligible"] is False
    assert wb_Wait["blockReason"] == "MINIMUM_DONATION_INTERVAL_NOT_MET"

    dr_wait = fn_validate_donor_eligibility(
        donor,
        [{"donation_type": "DOUBLE_RED_CELLS", "collected_at": "2026-06-01T10:00:00Z"}],
        donation_type="DOUBLE_RED_CELLS",
        target_date="2026-09-01T10:00:00Z",
    )
    assert dr_wait["isEligible"] is False

    plt_ok = fn_validate_donor_eligibility(
        donor,
        [{"donation_type": "PLATELETS", "collected_at": "2026-08-20T10:00:00Z"}],
        donation_type="PLATELETS",
        target_date="2026-09-01T10:00:00Z",
    )
    assert plt_ok["isEligible"] is True


def test_cloned_repo_unit_001_negative_invalid_vitals():
    """Verify donor eligibility rejection on medical deferral, missing donor, or invalid date.

    test_id: cloned_repo__unit__001_negative_invalid_vitals
    target: fn_validate_donor_eligibility
    requirement_id: REQ-002
    ac_ids: REQ-002-AC-1
    """
    assert parse_datetime("invalid-date-format") is None
    assert safe_float("nan", 10.0) == 10.0

    missing_res = fn_validate_donor_eligibility({}, [])
    assert missing_res["isEligible"] is False
    assert missing_res["blockReason"] == "DONOR_NOT_FOUND"

    deferred_donor = {
        "donor_id": "D-200",
        "is_deferred": True,
        "deferral_end_date": "2026-12-31T00:00:00Z",
        "deferral_reason": "LOW_HEMOGLOBIN",
    }
    def_res = fn_validate_donor_eligibility(
        deferred_donor,
        [],
        donation_type="WHOLE_BLOOD",
        target_date="2026-09-01T00:00:00Z",
    )
    assert def_res["isEligible"] is False
    assert def_res["blockReason"] == "LOW_HEMOGLOBIN"


def test_cloned_repo_unit_002():
    """Verify RedisGeospatialCache GEOADD, GEOSEARCH, and Haversine proximity matching.

    test_id: cloned_repo__unit__002
    target: RedisGeospatialCache.geosearch
    requirement_id: REQ-003
    ac_ids: REQ-003-AC-1, REQ-003-AC-2
    """
    cache = RedisGeospatialCache()
    cache.geoadd(
        "donor_near",
        37.7800,
        -122.4150,
        {
            "name": "Near Donor",
            "abo_type": "O",
            "rh_factor": "NEGATIVE",
            "rare_antigen_profile": {"kell": "negative", "duffy": "negative"},
        },
    )
    cache.geoadd(
        "donor_far",
        38.5000,
        -121.5000,
        {"name": "Far Donor", "abo_type": "O", "rh_factor": "NEGATIVE"},
    )
    bbox = get_bounding_box(37.7749, -122.4194, 15.0)
    assert len(bbox) == 4
    dist = haversine_distance_km(37.7749, -122.4194, 37.7800, -122.4150)
    assert dist < 15.0

    matches = cache.geosearch(
        center_lat=37.7749,
        center_lon=-122.4194,
        radius_km=15.0,
        abo_type="O",
        rh_factor="NEGATIVE",
        rare_antigen="kell",
    )
    assert len(matches) == 1
    assert matches[0]["member_id"] == "donor_near"


def test_cloned_repo_unit_003():
    """Verify DispatchStateMachine state transitions and SQS/DLQ notification redrive.

    test_id: cloned_repo__unit__003
    target: DispatchStateMachine.transition_status
    requirement_id: REQ-004
    ac_ids: REQ-004-AC-1
    """
    dsm = DispatchStateMachine()
    disp = dsm.create_dispatch(
        hospital_id="hosp-1",
        severity="LEVEL_1_CATASTROPHIC",
        required_abo="O",
        required_rh="NEGATIVE",
        units_requested=4,
        initiated_by="dr_lin",
    )
    dispatch_id = disp["dispatch_id"]
    ok, err = dsm.transition_status(dispatch_id, "MATCHING", "dr_lin")
    assert ok is True
    assert err is None

    bad_ok, bad_err = dsm.transition_status(dispatch_id, "INITIATED", "dr_lin")
    assert bad_ok is False
    assert "INVALID_STATE_TRANSITION" in bad_err

    dsm.enqueue_sqs_message({"donor_id": "d1", "phone": "+15550101", "text": "Urgent"})
    dsm.process_sqs_worker(fail_simulation=True)
    dsm.process_sqs_worker(fail_simulation=True)
    dlq_res = dsm.process_sqs_worker(fail_simulation=True)
    assert dlq_res["status"] == "DLQ_ROUTED"

    redriven = dsm.redrive_dlq()
    assert redriven == 1
    proc_res = dsm.process_sqs_worker(fail_simulation=False)
    assert proc_res["status"] == "PROCESSED"


def test_cloned_repo_unit_004():
    """Verify ISBT-128 barcode parsing and ReservationEngine 120-minute lease expiration reconciliation.

    test_id: cloned_repo__unit__004
    target: ReservationEngine.reconcile_expired_leases
    requirement_id: REQ-005, REQ-006
    ac_ids: REQ-005-AC-1, REQ-005-AC-2, REQ-006-AC-1, REQ-006-AC-2
    """
    ok, parsed, err = parse_isbt128_barcode("=W03652500010100")
    assert ok is True
    assert err is None
    assert parsed["din_number"] == "W036525000101"

    bad_ok, _, bad_err = parse_isbt128_barcode("SHORT")
    assert bad_ok is False
    assert bad_err == "INVALID_ISBT128_LENGTH"

    engine = ReservationEngine()
    engine.seed_item("W036525000999", "RED_BLOOD_CELLS", "O", "NEGATIVE", "hosp-1")
    past_time = datetime.utcnow() - timedelta(minutes=125)
    success, res, err_msg = engine.create_reservation(
        hospital_id="hosp-1",
        clinical_encounter_id="ENC-UNIT-1",
        din_number="W036525000999",
        reserved_by="Dr. Lin",
        reserved_at=past_time,
    )
    assert success is True
    assert err_msg is None
    assert engine.get_available_count("hosp-1", "O", "NEGATIVE") == 0

    dup_ok, _, dup_err = engine.create_reservation(
        hospital_id="hosp-1",
        clinical_encounter_id="ENC-UNIT-2",
        din_number="W036525000999",
    )
    assert dup_ok is False
    assert "ITEM_NOT_AVAILABLE" in dup_err

    expired = engine.reconcile_expired_leases()
    assert len(expired) == 1
    assert expired[0]["reservation_id"] == res["reservation_id"]
    assert engine.get_available_count("hosp-1", "O", "NEGATIVE") == 1


def test_cloned_repo_unit_005():
    """Verify AuditLedger hash-chain integrity and SecurityService ePHI/WORM operations.

    test_id: cloned_repo__unit__005
    target: AuditLedger.verify_integrity
    requirement_id: REQ-001, REQ-007
    ac_ids: REQ-001-AC-1, REQ-001-AC-2, REQ-001-AC-3, REQ-007-AC-2, REQ-007-AC-3
    """
    ledger = AuditLedger()
    ledger.record_mutation("donors", "d-1", "INSERT", "system", new_state={"active": True})
    ledger.record_mutation("donors", "d-1", "UPDATE", "admin", old_state={"active": True}, new_state={"active": False})
    is_valid, err = ledger.verify_integrity()
    assert is_valid is True
    assert err is None

    sec = SecurityService()
    cipher = sec.encrypt_ephi_field("John Doe SSN 123-45-6789")
    assert cipher.startswith("enc::")
    assert sec.decrypt_ephi_field(cipher) == "John Doe SSN 123-45-6789"
    scrubbed = sec.sanitize_log_message("Contact a@b.com or 123-45-6789")
    assert "[REDACTED_EMAIL]" in scrubbed
    assert "[REDACTED_SSN]" in scrubbed

    export = sec.create_worm_export("WORM-UNIT-001", ledger.get_logs(), "auditor")
    assert export["is_locked"] is True
    worm_ok, worm_err = sec.verify_worm_export("WORM-UNIT-001")
    assert worm_ok is True
    assert worm_err is None
