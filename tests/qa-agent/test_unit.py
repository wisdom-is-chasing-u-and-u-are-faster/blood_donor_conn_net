"""Generated unit tests for cloned_repo."""
from datetime import date, datetime
import pytest
from services.eligibility_service import fn_validate_donor_eligibility
from services.spatial_service import RedisGeospatialCache
from services.reservation_service import ReservationEngine
from services.telemetry_service import parse_isbt128_barcode
from services.dispatch_service import DispatchStateMachine
from services.audit_service import AuditLedger
from services.security_service import SecurityService


def test_cloned_repo_unit_001():
    """
    test_id: cloned_repo__unit__001
    target: fn_validate_donor_eligibility
    requirement_id: REQ-001
    ac_ids: REQ-001-AC-1
    """
    donor = {
        "donor_id": "D-UNIT-1",
        "is_active": True,
        "is_deferred": False,
    }
    history = [
        {"collected_at": "2025-12-31T10:00:00Z", "donation_type": "WHOLE_BLOOD"}
    ]
    res = fn_validate_donor_eligibility(
        donor, history, donation_type="WHOLE_BLOOD", target_date=date(2026, 3, 1)
    )
    assert res["isEligible"] is True
    assert res["daysRemaining"] == 0
    assert res["blockReason"] == "ELIGIBLE"


def test_cloned_repo_unit_001_negative_cooldown():
    """
    test_id: cloned_repo__unit__001_negative_cooldown
    target: fn_validate_donor_eligibility
    requirement_id: REQ-001
    ac_ids: REQ-001-AC-1
    """
    donor = {
        "donor_id": "D-UNIT-2",
        "is_active": True,
        "is_deferred": False,
    }
    history = [
        {"collected_at": "2026-02-19T10:00:00Z", "donation_type": "WHOLE_BLOOD"}
    ]
    res = fn_validate_donor_eligibility(
        donor, history, donation_type="WHOLE_BLOOD", target_date=date(2026, 3, 1)
    )
    assert res["isEligible"] is False
    assert res["daysRemaining"] == 46
    assert res["blockReason"] == "MINIMUM_DONATION_INTERVAL_NOT_MET"

    deferred_donor = {
        "donor_id": "D-UNIT-3",
        "is_deferred": True,
        "deferral_reason": "PERMANENT_DEFERRAL",
    }
    res_def = fn_validate_donor_eligibility(
        deferred_donor, [], donation_type="WHOLE_BLOOD", target_date=date(2026, 3, 1)
    )
    assert res_def["isEligible"] is False
    assert res_def["blockReason"] == "PERMANENT_DEFERRAL"


def test_cloned_repo_unit_002():
    """
    test_id: cloned_repo__unit__002
    target: RedisGeospatialCache.geosearch
    requirement_id: BO-2, BO-4
    ac_ids: BO-2-AC-1, BO-2-AC-2, BO-4-AC-1
    """
    cache = RedisGeospatialCache()
    cache.geoadd(
        "D_NEAR",
        37.7750,
        -122.4195,
        {
            "abo_type": "O",
            "rh_factor": "NEGATIVE",
            "rare_antigen_profile": {"kell": "negative", "duffy": "negative"},
        },
    )
    cache.geoadd(
        "D_MID",
        37.8044,
        -122.2712,
        {
            "abo_type": "O",
            "rh_factor": "NEGATIVE",
            "rare_antigen_profile": {"kell": "negative"},
        },
    )
    cache.geoadd(
        "D_FAR",
        34.0522,
        -118.2437,
        {
            "abo_type": "O",
            "rh_factor": "NEGATIVE",
            "rare_antigen_profile": {"kell": "negative"},
        },
    )
    results = cache.geosearch(
        center_lat=37.7749,
        center_lon=-122.4194,
        radius_km=25.0,
        abo_type="O",
        rh_factor="NEGATIVE",
        rare_antigen="kell",
    )
    assert len(results) == 2
    assert results[0]["member_id"] == "D_NEAR"
    assert results[1]["member_id"] == "D_MID"
    assert results[0]["distance_km"] < results[1]["distance_km"]


def test_cloned_repo_unit_003():
    """
    test_id: cloned_repo__unit__003
    target: ReservationEngine.create_reservation
    requirement_id: BO-3, BR-003
    ac_ids: BO-3-AC-2, BR-003-AC-1, BR-003-AC-3
    """
    engine = ReservationEngine()
    engine.seed_item("W036525999001", "RED_BLOOD_CELLS", "O", "NEGATIVE", "HOSP-001")
    t0 = datetime(2026, 3, 1, 10, 0, 0)
    ok, res, err = engine.create_reservation(
        "HOSP-001", "ENC-100", "W036525999001", reserved_at=t0
    )
    assert ok is True
    assert err is None
    assert res["status"] == "ACTIVE"
    assert res["expires_at"] == "2026-03-01T12:00:00Z"

    expired = engine.reconcile_expired_leases(current_time=datetime(2026, 3, 1, 13, 0, 0))
    assert len(expired) == 1
    assert expired[0]["status"] == "EXPIRED"
    assert engine._inventory["W036525999001"]["status"] == "AVAILABLE"

    valid_bc, parsed_bc, bc_err = parse_isbt128_barcode("=W03652500010100")
    assert valid_bc is True
    assert bc_err is None
    assert parsed_bc["din_number"] == "W036525000101"


def test_cloned_repo_unit_003_negative_insufficient_stock():
    """
    test_id: cloned_repo__unit__003_negative_insufficient_stock
    target: ReservationEngine.create_reservation
    requirement_id: BR-003
    ac_ids: BR-003-AC-2
    """
    engine = ReservationEngine()
    engine.seed_item("W036525999002", "RED_BLOOD_CELLS", "O", "NEGATIVE", "HOSP-001")
    t0 = datetime(2026, 3, 1, 10, 0, 0)
    ok1, res1, err1 = engine.create_reservation(
        "HOSP-001", "ENC-201", "W036525999002", reserved_at=t0
    )
    assert ok1 is True

    ok2, res2, err2 = engine.create_reservation(
        "HOSP-001", "ENC-202", "W036525999002", reserved_at=t0
    )
    assert ok2 is False
    assert res2 is None
    assert "ITEM_NOT_AVAILABLE" in err2

    ok3, res3, err3 = engine.create_reservation(
        "HOSP-001", "ENC-203", "W000000000000", reserved_at=t0
    )
    assert ok3 is False
    assert res3 is None
    assert err3 == "ITEM_NOT_FOUND"


def test_cloned_repo_unit_004():
    """
    test_id: cloned_repo__unit__004
    target: DispatchStateMachine.transition_status
    requirement_id: BO-1
    ac_ids: BO-1-AC-1
    """
    dsm = DispatchStateMachine()
    dispatch = dsm.create_dispatch(
        "HOSP-001", "LIFE_THREATENING", "O", "NEGATIVE", 2, "Dr. Sarah Lin"
    )
    did = dispatch["dispatch_id"]
    assert dispatch["status"] == "INITIATED"

    for next_state in ("MATCHING", "DISPATCHED", "ACCEPTED", "IN_TRANSIT", "FULFILLED"):
        ok, err = dsm.transition_status(did, next_state, "System")
        assert ok is True
        assert err is None

    ok_invalid, err_invalid = dsm.transition_status(did, "INITIATED", "System")
    assert ok_invalid is False
    assert err_invalid is not None

    notif = dsm.send_multi_channel_notification("D-1001", "+15550101", "Emergency O- request")
    assert notif["status"] == "DELIVERED"


def test_cloned_repo_unit_005():
    """
    test_id: cloned_repo__unit__005
    target: AuditLedger.verify_integrity
    requirement_id: BR-002
    ac_ids: BR-002-AC-1
    """
    ledger = AuditLedger()
    r1 = ledger.record_mutation("Inventory", "DIN-1", "CREATE", "System", None, {"status": "AVAILABLE"})
    r2 = ledger.record_mutation("Inventory", "DIN-1", "RESERVE", "Dr. Lin", {"status": "AVAILABLE"}, {"status": "RESERVED"})
    assert r2["previous_hash"] == r1["checksum_signature"]

    is_intact, err = ledger.verify_integrity()
    assert is_intact is True
    assert err is None

    ledger._logs[0]["action_type"] = "TAMPERED"
    is_intact_after, err_after = ledger.verify_integrity()
    assert is_intact_after is False
    assert err_after is not None


def test_cloned_repo_unit_006():
    """
    test_id: cloned_repo__unit__006
    target: SecurityService.verify_worm_export
    requirement_id: BO-3
    ac_ids: BO-3-AC-1
    """
    sec = SecurityService()
    export = sec.create_worm_export("EXP-UNIT-1", [{"id": 1, "action": "CREATE"}], "ComplianceOfficer")
    assert export["export_id"] == "EXP-UNIT-1"

    is_valid, err = sec.verify_worm_export("EXP-UNIT-1")
    assert is_valid is True
    assert err is None

    is_valid_missing, err_missing = sec.verify_worm_export("NON-EXISTENT")
    assert is_valid_missing is False
    assert err_missing == "EXPORT_NOT_FOUND"

    ct = sec.encrypt_ephi_field("sensitive-donor-pii")
    assert sec.decrypt_ephi_field(ct) == "sensitive-donor-pii"
    scrubbed = sec.sanitize_log_message("Donor SSN 123-45-6789 email test@example.com")
    assert "[REDACTED_SSN]" in scrubbed
    assert "[REDACTED_EMAIL]" in scrubbed
