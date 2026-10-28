"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   unit
Source:  test_strategy/plans/cloned_repo__unit.json
Generated: 2026-10-28T06:38:00Z
"""
from datetime import datetime, timedelta
import pytest
from services.eligibility_service import fn_validate_donor_eligibility
from services.spatial_service import RedisGeospatialCache, haversine_distance_km
from services.reservation_service import ReservationEngine
from services.telemetry_service import parse_isbt128_barcode
from services.dispatch_service import DispatchStateMachine
from services.audit_service import AuditLedger
from services.security_service import SecurityService


def test_cloned_repo_unit_001():
    """Validate rolling 56-day whole blood, 112-day double red cell, and 7-day platelet intervals.

    test_id: cloned_repo__unit__001
    target: fn_validate_donor_eligibility
    requirement_id: REQ-001
    ac_ids: REQ-001-AC-1
    """
    donor = {"donor_id": "d1", "username": "d1", "is_active": True, "is_deferred": False}
    eval_dt = datetime(2026, 6, 1, 12, 0, 0)

    wb_recent = [{"donation_type": "WHOLE_BLOOD", "collected_at": "2026-05-01T10:00:00Z"}]
    res_wb_block = fn_validate_donor_eligibility(donor, wb_recent, "WHOLE_BLOOD", target_date=eval_dt)
    assert res_wb_block["isEligible"] is False
    assert res_wb_block["blockReason"] == "MINIMUM_DONATION_INTERVAL_NOT_MET"

    wb_old = [{"donation_type": "WHOLE_BLOOD", "collected_at": "2026-03-01T10:00:00Z"}]
    res_wb_ok = fn_validate_donor_eligibility(donor, wb_old, "WHOLE_BLOOD", target_date=eval_dt)
    assert res_wb_ok["isEligible"] is True

    drc_recent = [{"donation_type": "DOUBLE_RED_CELLS", "collected_at": "2026-04-01T10:00:00Z"}]
    res_drc_block = fn_validate_donor_eligibility(donor, drc_recent, "DOUBLE_RED_CELLS", target_date=eval_dt)
    assert res_drc_block["isEligible"] is False

    plt_recent = [{"donation_type": "PLATELETS", "collected_at": "2026-05-28T10:00:00Z"}]
    res_plt_block = fn_validate_donor_eligibility(donor, plt_recent, "PLATELETS", target_date=eval_dt)
    assert res_plt_block["isEligible"] is False


def test_cloned_repo_unit_001_negative_deferred_donor():
    """Reject deferred or missing donor in eligibility engine.

    test_id: cloned_repo__unit__001_negative_deferred_donor
    target: fn_validate_donor_eligibility
    requirement_id: REQ-001
    ac_ids: REQ-001-AC-1
    """
    deferred_donor = {
        "donor_id": "d2",
        "is_deferred": True,
        "deferral_end_date": "2026-12-31T00:00:00Z",
        "deferral_reason": "LOW_HEMOGLOBIN"
    }
    res = fn_validate_donor_eligibility(deferred_donor, [], "WHOLE_BLOOD", target_date="2026-06-01T00:00:00Z")
    assert res["isEligible"] is False
    assert res["blockReason"] == "LOW_HEMOGLOBIN"

    empty_res = fn_validate_donor_eligibility({}, [], "WHOLE_BLOOD")
    assert empty_res["isEligible"] is False
    assert empty_res["blockReason"] == "DONOR_NOT_FOUND"


def test_cloned_repo_unit_002():
    """Match donors within 15 km radius and rare antigen filter in RedisGeospatialCache.

    test_id: cloned_repo__unit__002
    target: RedisGeospatialCache.geosearch
    requirement_id: BO-2, BO-4
    ac_ids: BO-2-AC-1, BO-2-AC-2, BO-4-AC-1
    """
    cache = RedisGeospatialCache()
    cache.geoadd("donor_near", 37.7850, -122.4150, {
        "name": "Marcus Vance",
        "abo_type": "O",
        "rh_factor": "NEGATIVE",
        "rare_antigen_profile": {"kell": "negative", "duffy": "negative"}
    })
    cache.geoadd("donor_far", 38.5000, -122.4150, {
        "name": "Far Donor",
        "abo_type": "O",
        "rh_factor": "NEGATIVE",
        "rare_antigen_profile": {"kell": "negative"}
    })

    matches = cache.geosearch(37.7749, -122.4194, radius_km=15.0, abo_type="O", rh_factor="NEGATIVE", rare_antigen="kell")
    assert len(matches) == 1
    assert matches[0]["member_id"] == "donor_near"
    assert matches[0]["distance_km"] <= 15.0
    assert haversine_distance_km(37.7749, -122.4194, 37.7850, -122.4150) < 15.0


def test_cloned_repo_unit_003():
    """Create 120-minute inventory reservation and auto-release expired leases.

    test_id: cloned_repo__unit__003
    target: ReservationEngine.reconcile_expired_leases
    requirement_id: BO-3, BR-003, UC-001, FR-02
    ac_ids: BO-3-AC-2, BR-003-AC-1, UC-001-AC-1, FR-02-AC-1
    """
    engine = ReservationEngine()
    engine.seed_item("W036525000201", "RED_BLOOD_CELLS", "O", "NEGATIVE", "hosp-1")
    past_time = datetime.utcnow() - timedelta(minutes=125)
    ok, res, err = engine.create_reservation("hosp-1", "ENC-100", "W036525000201", reserved_at=past_time)
    assert ok is True
    assert err is None
    assert res["status"] == "ACTIVE"
    assert engine.get_available_count("hosp-1", "O", "NEGATIVE") == 0

    expired = engine.reconcile_expired_leases(current_time=datetime.utcnow())
    assert len(expired) == 1
    assert expired[0]["status"] == "EXPIRED"
    assert engine.get_available_count("hosp-1", "O", "NEGATIVE") == 1


def test_cloned_repo_unit_003_negative_duplicate_reservation():
    """Prevent duplicate active reservation on already reserved blood unit DIN.

    test_id: cloned_repo__unit__003_negative_duplicate_reservation
    target: ReservationEngine.create_reservation
    requirement_id: BR-003, FR-02
    ac_ids: BR-003-AC-1, FR-02-AC-1
    """
    engine = ReservationEngine()
    engine.seed_item("W036525000202", "RED_BLOOD_CELLS", "O", "NEGATIVE", "hosp-1")
    ok1, _, _ = engine.create_reservation("hosp-1", "ENC-101", "W036525000202")
    assert ok1 is True

    ok2, res2, err2 = engine.create_reservation("hosp-1", "ENC-102", "W036525000202")
    assert ok2 is False
    assert res2 is None
    assert "ITEM_NOT_AVAILABLE" in err2


def test_cloned_repo_unit_004():
    """Parse valid and invalid ISBT-128 blood telemetry barcodes.

    test_id: cloned_repo__unit__004
    target: parse_isbt128_barcode
    requirement_id: BO-3, UC-001
    ac_ids: BO-3-AC-1, UC-001-AC-2
    """
    ok, parsed, err = parse_isbt128_barcode("=W03652500010100")
    assert ok is True
    assert err is None
    assert parsed["din_number"] == "W036525000101"

    ok_bad, parsed_bad, err_bad = parse_isbt128_barcode("SHORT")
    assert ok_bad is False
    assert parsed_bad is None
    assert err_bad == "INVALID_ISBT128_LENGTH"


def test_cloned_repo_unit_005():
    """Create emergency dispatch, process SQS notification worker, and enforce state transitions.

    test_id: cloned_repo__unit__005
    target: DispatchStateMachine.create_dispatch
    requirement_id: BO-1, FR-02
    ac_ids: BO-1-AC-1, FR-02-AC-1
    """
    sm = DispatchStateMachine()
    disp = sm.create_dispatch("hosp-1", "LEVEL_1_CATASTROPHIC", "O", "NEGATIVE", 4, "Dr. Lin")
    disp_id = disp["dispatch_id"]
    assert disp["status"] == "INITIATED"

    sm.enqueue_sqs_message({"dispatch_id": disp_id, "donor_id": "marcus_vance", "text": "Urgent O-"})
    worker_res = sm.process_sqs_worker()
    assert worker_res["status"] == "PROCESSED"

    ok_valid, err_valid = sm.transition_status(disp_id, "MATCHING", "System")
    assert ok_valid is True
    assert err_valid is None

    ok_invalid, err_invalid = sm.transition_status(disp_id, "FULFILLED", "System")
    assert ok_invalid is False
    assert "INVALID_STATE_TRANSITION" in err_invalid


def test_cloned_repo_unit_006():
    """Verify append-only AuditLedger hash chain and WORM ePHI encryption.

    test_id: cloned_repo__unit__006
    target: AuditLedger.verify_integrity
    requirement_id: BR-002, NFR-SEC-01
    ac_ids: BR-002-AC-1, BR-002-AC-2, NFR-SEC-01-AC-1
    """
    ledger = AuditLedger()
    ledger.record_mutation("donors", "d-1", "INSERT", "admin", new_state={"status": "ACTIVE"})
    ledger.record_mutation("donors", "d-1", "UPDATE", "admin", old_state={"status": "ACTIVE"}, new_state={"status": "VERIFIED"})
    intact, err = ledger.verify_integrity()
    assert intact is True
    assert err is None

    sec = SecurityService()
    cipher = sec.encrypt_ephi_field("patient-ssn-123-45-6789")
    assert cipher.startswith("enc::")
    assert sec.decrypt_ephi_field(cipher) == "patient-ssn-123-45-6789"

    worm = sec.create_worm_export("WORM-UNIT-1", ledger.get_logs(), "auditor")
    assert worm["is_locked"] is True
    valid_worm, worm_err = sec.verify_worm_export("WORM-UNIT-1")
    assert valid_worm is True
    assert worm_err is None
