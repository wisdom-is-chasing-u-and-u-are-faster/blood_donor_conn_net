"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   unit
Source:  test_strategy/plans/cloned_repo__unit.json
Generated: 2026-11-04T14:18:00Z
"""
from datetime import datetime, timedelta
import pytest
from app import app
from services.eligibility_service import fn_validate_donor_eligibility
from services.spatial_service import RedisGeospatialCache, haversine_distance_km
from services.reservation_service import ReservationEngine
from services.telemetry_service import parse_isbt128_barcode
from services.audit_service import AuditLedger
from services.security_service import SecurityService


def test_cloned_repo_unit_001():
    """Validate rolling donor eligibility intervals across blood component types.

    test_id: cloned_repo__unit__001
    target: services.eligibility_service.fn_validate_donor_eligibility
    requirement_id: REQ-002
    ac_ids: REQ-002-AC-1
    """
    donor = {"donor_id": "d-1", "username": "d-1", "is_deferred": False}
    wb_history = [{"donation_type": "WHOLE_BLOOD", "collected_at": "2026-01-01T10:00:00Z"}]
    res_wb = fn_validate_donor_eligibility(
        donor, wb_history, donation_type="WHOLE_BLOOD", target_date="2026-03-05T10:00:00Z"
    )
    assert res_wb["isEligible"] is True
    assert res_wb["daysRemaining"] == 0
    assert res_wb["blockReason"] == "ELIGIBLE"

    dr_history = [{"donation_type": "DOUBLE_RED_CELLS", "collected_at": "2026-01-01T10:00:00Z"}]
    res_dr = fn_validate_donor_eligibility(
        donor, dr_history, donation_type="DOUBLE_RED_CELLS", target_date="2026-05-01T10:00:00Z"
    )
    assert res_dr["isEligible"] is True
    assert res_dr["daysRemaining"] == 0
    assert res_dr["blockReason"] == "ELIGIBLE"

    plt_history = [{"donation_type": "PLATELETS", "collected_at": "2026-05-01T10:00:00Z"}]
    res_plt = fn_validate_donor_eligibility(
        donor, plt_history, donation_type="PLATELETS", target_date="2026-05-10T10:00:00Z"
    )
    assert res_plt["isEligible"] is True
    assert res_plt["daysRemaining"] == 0
    assert res_plt["blockReason"] == "ELIGIBLE"


def test_cloned_repo_unit_001_negative_interval_not_met():
    """Reject donor eligibility when minimum interval or deferral is active.

    test_id: cloned_repo__unit__001_negative_interval_not_met
    target: services.eligibility_service.fn_validate_donor_eligibility
    requirement_id: REQ-002
    ac_ids: REQ-002-AC-1
    """
    donor = {"donor_id": "d-2", "username": "d-2", "is_deferred": False}
    recent_history = [{"donation_type": "WHOLE_BLOOD", "collected_at": "2026-05-25T10:00:00Z"}]
    res_recent = fn_validate_donor_eligibility(
        donor, recent_history, donation_type="WHOLE_BLOOD", target_date="2026-06-01T10:00:00Z"
    )
    assert res_recent["isEligible"] is False
    assert res_recent["daysRemaining"] == 49
    assert res_recent["blockReason"] == "MINIMUM_DONATION_INTERVAL_NOT_MET"

    deferred_donor = {
        "donor_id": "d-3",
        "username": "d-3",
        "is_deferred": True,
        "deferral_end_date": "2026-12-31T00:00:00Z",
        "deferral_reason": "LOW_HEMOGLOBIN"
    }
    res_def = fn_validate_donor_eligibility(
        deferred_donor, [], donation_type="WHOLE_BLOOD", target_date="2026-06-01T10:00:00Z"
    )
    assert res_def["isEligible"] is False
    assert res_def["daysRemaining"] > 0
    assert res_def["blockReason"] == "LOW_HEMOGLOBIN"


def test_cloned_repo_unit_002():
    """Geosearch matches donors within 15 km radius and filters rare phenotypes.

    test_id: cloned_repo__unit__002
    target: services.spatial_service.RedisGeospatialCache.geosearch
    requirement_id: REQ-001
    ac_ids: REQ-001-AC-2, REQ-001-AC-3
    """
    cache = RedisGeospatialCache()
    cache.geoadd("donor_kell_neg", 37.7850, -122.4150, {
        "name": "Marcus Vance",
        "abo_type": "O",
        "rh_factor": "NEGATIVE",
        "rare_antigen_profile": {"kell": "negative", "duffy": "negative"}
    })
    cache.geoadd("donor_closest", 37.7760, -122.4180, {
        "name": "Jane Smith",
        "abo_type": "O",
        "rh_factor": "NEGATIVE"
    })
    cache.geoadd("donor_outside", 38.5000, -122.4100, {
        "name": "Far Donor",
        "abo_type": "O",
        "rh_factor": "NEGATIVE"
    })

    matches = cache.geosearch(
        center_lat=37.7749,
        center_lon=-122.4194,
        radius_km=15.0,
        abo_type="O",
        rh_factor="NEGATIVE"
    )
    assert len(matches) == 2
    assert matches[0]["member_id"] == "donor_closest"
    assert matches[1]["member_id"] == "donor_kell_neg"
    assert all(m["distance_km"] <= 15.0 for m in matches)

    rare_matches = cache.geosearch(
        center_lat=37.7749,
        center_lon=-122.4194,
        radius_km=15.0,
        rare_antigen="kell"
    )
    assert len(rare_matches) == 1
    assert rare_matches[0]["member_id"] == "donor_kell_neg"
    assert haversine_distance_km(37.7749, -122.4194, 37.7850, -122.4150) < 15.0


def test_cloned_repo_unit_003():
    """Create 120-minute inventory reservation and auto-release expired leases.

    test_id: cloned_repo__unit__003
    target: services.reservation_service.ReservationEngine
    requirement_id: REQ-003, REQ-005
    ac_ids: REQ-003-AC-1, REQ-005-AC-1
    """
    engine = ReservationEngine()
    engine.seed_item("W036525990001", "RED_BLOOD_CELLS", "O", "NEGATIVE", "hosp-1")
    base_time = datetime(2026, 6, 1, 12, 0, 0)

    ok, res, err = engine.create_reservation(
        hospital_id="hosp-1",
        clinical_encounter_id="ENC-100",
        din_number="W036525990001",
        reserved_by="Dr. Test",
        reserved_at=base_time
    )
    assert ok is True
    assert err is None
    assert res["status"] == "ACTIVE"
    assert engine.get_available_count("hosp-1", "O", "NEGATIVE") == 0

    expired = engine.reconcile_expired_leases(current_time=base_time + timedelta(minutes=121))
    assert len(expired) == 1
    assert expired[0]["status"] == "EXPIRED"
    assert engine.get_available_count("hosp-1", "O", "NEGATIVE") == 1


def test_cloned_repo_unit_003_negative_unavailable_unit():
    """Reject reservation for missing or already reserved blood unit.

    test_id: cloned_repo__unit__003_negative_unavailable_unit
    target: services.reservation_service.ReservationEngine.create_reservation
    requirement_id: REQ-005
    ac_ids: REQ-005-AC-2
    """
    engine = ReservationEngine()
    ok_missing, res_missing, err_missing = engine.create_reservation(
        hospital_id="hosp-1",
        clinical_encounter_id="ENC-101",
        din_number="NON_EXISTENT_DIN"
    )
    assert ok_missing is False
    assert res_missing is None
    assert err_missing == "ITEM_NOT_FOUND"

    engine.seed_item("W036525990002", "RED_BLOOD_CELLS", "O", "NEGATIVE", "hosp-1")
    ok1, _, _ = engine.create_reservation("hosp-1", "ENC-101", "W036525990002")
    ok2, res2, err2 = engine.create_reservation("hosp-1", "ENC-102", "W036525990002")
    assert ok1 is True
    assert ok2 is False
    assert res2 is None
    assert "ITEM_NOT_AVAILABLE" in err2


def test_cloned_repo_unit_004():
    """Parse valid ISBT-128 barcode and reject malformed barcodes.

    test_id: cloned_repo__unit__004
    target: services.telemetry_service.parse_isbt128_barcode
    requirement_id: REQ-003
    ac_ids: REQ-003-AC-2
    """
    ok, parsed, err = parse_isbt128_barcode("=W03652500010100")
    assert ok is True
    assert err is None
    assert parsed["din_number"] == "W036525000101"
    assert parsed["facility_code"] == "W0365"
    assert parsed["year"] == "2025"
    assert parsed["sequence"] == "000101"

    ok_bad, parsed_bad, err_bad = parse_isbt128_barcode("SHORT")
    assert ok_bad is False
    assert parsed_bad is None
    assert err_bad == "INVALID_ISBT128_LENGTH"


def test_cloned_repo_unit_005():
    """Verify cryptographic hash chain in AuditLedger and ePHI encryption in SecurityService.

    test_id: cloned_repo__unit__005
    target: services.audit_service.AuditLedger
    requirement_id: REQ-006
    ac_ids: REQ-006-AC-4
    """
    ledger = AuditLedger()
    sec = SecurityService()

    ledger.record_mutation("inventory", "item-1", "INSERT", "tester", new_state={"status": "AVAILABLE"})
    ledger.record_mutation(
        "inventory", "item-1", "UPDATE", "tester",
        old_state={"status": "AVAILABLE"},
        new_state={"status": "RESERVED"}
    )
    intact, err = ledger.verify_integrity()
    assert intact is True
    assert err is None

    ledger._logs[0]["new_state"] = {"status": "TAMPERED"}
    intact_tampered, err_tampered = ledger.verify_integrity()
    assert intact_tampered is False
    assert "Tampered record" in err_tampered
    ledger._logs[0]["new_state"] = {"status": "AVAILABLE"}

    cipher = sec.encrypt_ephi_field("SSN-123-45-6789")
    assert cipher.startswith("enc::")
    assert sec.decrypt_ephi_field(cipher) == "SSN-123-45-6789"

    worm = sec.create_worm_export("WORM-UNIT-01", ledger.get_logs(), "auditor")
    assert worm["is_locked"] is True
    assert sec.verify_worm_export("WORM-UNIT-01") == (True, None)
