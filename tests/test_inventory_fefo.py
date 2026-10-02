import pytest
import datetime
from services.inventory_service import inventory_service
from db.init_db import reset_database, get_db_connection


@pytest.fixture(autouse=True)
def setup_env():
    reset_database()
    yield


def test_fefo_allocation_order():
    """[ARCH-2102-AC1] [ARCH-2115-AC1] Test FEFO allocation strictly selects nearest expiration dates first."""
    # Reserve 2 units of O_NEG
    success, res_id, lease_exp, reserved_ids, err = inventory_service.reserve_units(
        request_id="req-test-fefo",
        facility_id="fac-001",
        required_blood_type="O_NEG",
        component_type="RED_BLOOD_CELLS",
        units_requested=2,
        lease_seconds=120
    )

    assert success is True
    assert len(reserved_ids) == 2
    # Baseline units unit-001 expires at T+24h, unit-002 expires at T+48h
    assert reserved_ids == ["unit-001", "unit-002"]


def test_automatic_lease_expiration_sweeper():
    """[ARCH-2102-AC2] [ARCH-2114-AC1] Test background sweeper reverts expired reservations to AVAILABLE."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Manually insert an expired reservation (expired 10 seconds ago)
    past_iso = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=10)).isoformat()
    cursor.execute("""
    UPDATE inventory_blood_units
    SET status = 'RESERVED', reservation_id = 'res-expired', lease_expires_at = ?
    WHERE unit_id = 'unit-003';
    """, (past_iso,))
    conn.commit()

    # Run sweeper
    reverted_count = inventory_service.sweep_expired_leases()
    assert reverted_count >= 1

    # Verify unit-003 is AVAILABLE again
    cursor.execute("SELECT status, reservation_id FROM inventory_blood_units WHERE unit_id = 'unit-003';")
    row = cursor.fetchone()
    assert row["status"] == "AVAILABLE"
    assert row["reservation_id"] is None
