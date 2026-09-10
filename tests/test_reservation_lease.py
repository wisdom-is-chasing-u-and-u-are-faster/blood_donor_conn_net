"""
Test Suite for Hospital Blood Inventory Telemetry & 120-Minute Lease Engine (ARCH-1180, ARCH-1181, ARCH-1182)
Validates Reservation Creation, Row-Level Locking, Auto-Expiration at T0 + 121 minutes,
Stock Restitution, and ISBT 128 Barcode Ingestion.
"""
import pytest
from datetime import datetime, timedelta
from services.reservation_service import ReservationEngine
from services.telemetry_service import parse_isbt128_barcode


@pytest.fixture
def clean_engine():
    engine = ReservationEngine()
    # Seed available O-Neg RBC unit (DIN: W036525000101)
    engine.seed_item("W036525000101", "RED_BLOOD_CELLS", "O", "NEGATIVE", "hosp-1")
    return engine


def test_scenario_1_reservation_creation_and_inventory_decrement(clean_engine):
    """
    Scenario 1:
    Given an available unit of O-Negative RBC (DIN: W036525000101),
    When Dr. Sarah Lin reserves the unit for Encounter ENC-TRAUMA-9912,
    Then a reservation record is created with status ACTIVE, expires_at set to T0 + 120 minutes,
    and available inventory is decremented by 1.
    """
    t0 = datetime(2025, 3, 1, 14, 0, 0)
    initial_stock = clean_engine.get_available_count("hosp-1", "O", "NEGATIVE")
    assert initial_stock == 1

    success, res, err = clean_engine.create_reservation(
        hospital_id="hosp-1",
        clinical_encounter_id="ENC-TRAUMA-9912",
        din_number="W036525000101",
        reserved_by="Dr. Sarah Lin",
        reserved_at=t0
    )
    assert success is True
    assert res["status"] == "ACTIVE"
    assert res["expires_at"] == "2025-03-01T16:00:00Z"  # T0 + 120 min

    # Stock is decremented
    updated_stock = clean_engine.get_available_count("hosp-1", "O", "NEGATIVE")
    assert updated_stock == 0

    # Prevent double reservation
    dup_success, _, dup_err = clean_engine.create_reservation(
        hospital_id="hosp-1",
        clinical_encounter_id="ENC-OTHER-1234",
        din_number="W036525000101",
        reserved_by="Dr. Another",
        reserved_at=t0
    )
    assert dup_success is False
    assert "ITEM_NOT_AVAILABLE" in dup_err


def test_scenario_2_automated_lease_expiration_and_stock_restitution(clean_engine):
    """
    Scenario 2:
    Given an active reservation created at T0 that has not been consumed,
    When the background reconciliation worker executes at T0 + 121 minutes,
    Then the reservation status transitions to EXPIRED, the unit is returned to available inventory,
    and an audit entry is written to compliance_log.
    """
    t0 = datetime(2025, 3, 1, 14, 0, 0)
    clean_engine.create_reservation(
        hospital_id="hosp-1",
        clinical_encounter_id="ENC-TRAUMA-9912",
        din_number="W036525000101",
        reserved_by="Dr. Sarah Lin",
        reserved_at=t0
    )
    assert clean_engine.get_available_count("hosp-1", "O", "NEGATIVE") == 0

    # At T0 + 60 minutes: Still active, not expired
    expired_at_60 = clean_engine.reconcile_expired_leases(current_time=t0 + timedelta(minutes=60))
    assert len(expired_at_60) == 0
    assert clean_engine.get_available_count("hosp-1", "O", "NEGATIVE") == 0

    # At T0 + 121 minutes: Background worker expires reservation
    t_121 = t0 + timedelta(minutes=121)
    expired_at_121 = clean_engine.reconcile_expired_leases(current_time=t_121)
    assert len(expired_at_121) == 1
    assert expired_at_121[0]["status"] == "EXPIRED"

    # Unit is restored to available stock
    assert clean_engine.get_available_count("hosp-1", "O", "NEGATIVE") == 1


def test_barcode_isbt128_scanning():
    ok, parsed, err = parse_isbt128_barcode("=W03652500010100")
    assert ok is True
    assert parsed["din_number"] == "W036525000101"
    assert parsed["facility_code"] == "W0365"
    assert parsed["year"] == "2025"
    assert parsed["sequence"] == "000101"
