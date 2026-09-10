"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   unit
Source:  test_strategy/plans/cloned_repo__unit.json
Generated: 2024-07-25T17:04:36.511231Z
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# It's a unit test suite, so we test the service logic directly.
from services.eligibility_service import fn_validate_donor_eligibility
from services.spatial_service import spatial_cache, haversine_distance_km
from services.reservation_service import reservation_engine
from services.dispatch_service import dispatch_engine
from services.audit_service import audit_ledger

# Although we test services directly, some tests might need app context
from app import app

@pytest.fixture(autouse=True)
def clear_singletons(monkeypatch):
    """Ensure in-memory singletons are clear before each test."""
    monkeypatch.setattr(audit_ledger, '_logs', [])
    monkeypatch.setattr(spatial_cache, '_geo_index', {})
    monkeypatch.setattr(spatial_cache, '_metadata', {})
    monkeypatch.setattr(reservation_engine, '_inventory', {})
    monkeypatch.setattr(reservation_engine, '_reservations', {})
    monkeypatch.setattr(dispatch_engine, '_dispatches', {})
    monkeypatch.setattr(dispatch_engine, '_sqs_queue', [])
    monkeypatch.setattr(dispatch_engine, '_dlq_queue', [])
    monkeypatch.setattr(dispatch_engine, '_notifications', [])

def test_cloned_repo__unit__001():
    """Verify donor eligibility logic for a donor who can donate whole blood.

    test_id: cloned_repo__unit__001
    target: get_donor_eligibility
    requirement_id: REQ-002
    ac_ids: REQ-002-AC-1
    """
    mock_donor = {"username": "test_donor", "is_deferred": False}
    sixty_days_ago = datetime.utcnow() - timedelta(days=60)
    donation_history = [
        {
            "donation_type": "WHOLE_BLOOD",
            "collected_at": sixty_days_ago.strftime("%Y-%m-%dT%H:%M:%SZ")
        }
    ]

    result = fn_validate_donor_eligibility(
        donor=mock_donor,
        donation_history=donation_history,
        donation_type="WHOLE_BLOOD"
    )

    assert result["isEligible"] is True
    assert result["daysRemaining"] == 0

def test_cloned_repo__unit__002_negative_ineligible():
    """Verify donor eligibility logic for a donor who cannot donate platelets.

    test_id: cloned_repo__unit__002_negative_ineligible
    target: get_donor_eligibility
    requirement_id: REQ-002
    ac_ids: REQ-002-AC-1
    """
    mock_donor = {"username": "test_donor", "is_deferred": False}
    five_days_ago = datetime.utcnow() - timedelta(days=5)
    donation_history = [
        {
            "donation_type": "PLATELETS",
            "collected_at": five_days_ago.strftime("%Y-%m-%dT%H:%M:%SZ")
        }
    ]

    result = fn_validate_donor_eligibility(
        donor=mock_donor,
        donation_history=donation_history,
        donation_type="PLATELETS"
    )

    assert result["isEligible"] is False
    assert result["daysRemaining"] > 0
    assert result["blockReason"] == "MINIMUM_DONATION_INTERVAL_NOT_MET"

def test_cloned_repo__unit__003():
    """Verify spatial candidate matching algorithm correctly finds candidates in radius.

    test_id: cloned_repo__unit__003
    target: find_spatial_candidates
    requirement_id: BO-2
    ac_ids: BO-2-AC-1
    """
    # Add mock donor locations
    spatial_cache.geoadd("donor_inside", 37.7750, -122.4190, {"name": "Inside"})
    spatial_cache.geoadd("donor_outside", 38.0, -122.0, {"name": "Outside"})
    spatial_cache.geoadd("donor_edge", 37.7750, -122.555, {"name": "Edge"}) # Approx 12km away

    # Define search origin and radius
    origin_lat, origin_lon = 37.7749, -122.4194
    radius_km = 15.0

    # Call the spatial search function
    candidates = spatial_cache.geosearch(origin_lat, origin_lon, radius_km)

    # Assert only donors within the radius are returned
    assert len(candidates) == 2
    candidate_ids = {c['member_id'] for c in candidates}
    assert "donor_inside" in candidate_ids
    assert "donor_edge" in candidate_ids
    assert "donor_outside" not in candidate_ids

@patch('services.reservation_service.audit_ledger')
def test_cloned_repo__unit__004(mock_audit_ledger):
    """Verify inventory reservation logic correctly reserves an item.

    test_id: cloned_repo__unit__004
    target: reserve_inventory
    requirement_id: REQ-002
    ac_ids: REQ-002-AC-2
    """
    item_id = "W123456789012"
    reservation_engine.seed_item(item_id, "RED_BLOOD_CELLS", "O", "POSITIVE", "hosp-1")

    success, reservation, error = reservation_engine.create_reservation(
        hospital_id="hosp-1",
        clinical_encounter_id="enc-123",
        din_number=item_id,
        reserved_by="test_user"
    )

    assert success is True
    assert error is None
    assert reservation is not None
    assert reservation["din_number"] == item_id
    assert reservation["status"] == "ACTIVE"

    # Verify internal state change
    assert reservation_engine._inventory[item_id]["status"] == "RESERVED"
    mock_audit_ledger.record_mutation.assert_called_once()

@patch('services.dispatch_service.audit_ledger')
def test_cloned_repo__unit__005(mock_audit_ledger):
    """Verify emergency dispatch creation logic creates a dispatch and audits it.

    test_id: cloned_repo__unit__005
    target: create_emergency_dispatch
    requirement_id: BO-4
    ac_ids: BO-4-AC-1
    """
    dispatch_data = {
        "hospital_id": "hosp-emergency",
        "severity": "CRITICAL",
        "required_abo": "O",
        "required_rh": "NEGATIVE",
        "units_requested": 5,
        "initiated_by": "er_doctor"
    }

    dispatch = dispatch_engine.create_dispatch(**dispatch_data)

    assert dispatch is not None
    assert dispatch["status"] == "INITIATED"
    assert dispatch["hospital_id"] == "hosp-emergency"
    assert dispatch["units_requested"] == 5

    # Verify downstream service call (audit)
    mock_audit_ledger.record_mutation.assert_called_once()
    call_args = mock_audit_ledger.record_mutation.call_args[1]
    assert call_args['entity_name'] == 'emergency_dispatches'
    assert call_args['action_type'] == 'INSERT'

def test_cloned_repo__unit__006(monkeypatch):
    """Verify audit trail verification logic detects tampering.

    test_id: cloned_repo__unit__006
    target: verify_audit_trail
    requirement_id: REQ-004
    ac_ids: REQ-004-AC-2
    """
    # 1. Create a valid log chain
    audit_ledger.record_mutation("donors", "d1", "INSERT", "system", new_state={"name": "A"})
    audit_ledger.record_mutation("donors", "d1", "UPDATE", "user1", old_state={"name": "A"}, new_state={"name": "B"})
    audit_ledger.record_mutation("donors", "d2", "INSERT", "system", new_state={"name": "C"})

    # 2. Verify the valid log
    is_valid, error = audit_ledger.verify_integrity()
    assert is_valid is True
    assert error is None

    # 3. Tamper with the log
    # Directly modifying the internal list for testing purposes
    original_signature = audit_ledger._logs[1]["checksum_signature"]
    audit_ledger._logs[1]["checksum_signature"] = "tampered_hash_value"

    # 4. Verify the invalid log
    is_valid_tampered, error_tampered = audit_ledger.verify_integrity()
    assert is_valid_tampered is False
    assert error_tampered is not None
    assert "Broken chain" in error_tampered

    # Reset and test tampering with content
    audit_ledger._logs[1]["checksum_signature"] = original_signature
    audit_ledger._logs[1]['performed_by'] = 'malicious_actor'
    is_valid_tampered_content, error_tampered_content = audit_ledger.verify_integrity()
    assert is_valid_tampered_content is False
    assert "Tampered record" in error_tampered_content

@patch('services.reservation_service.audit_ledger')
def test_cloned_repo__unit__007(mock_audit_ledger):
    """Verify inventory reconciliation logic correctly flags expired items.

    test_id: cloned_repo__unit__007
    target: reconcile_inventory
    requirement_id: BO-3
    ac_ids: BO-3-AC-1
    """
    item_id = "W_EXPIRED_123"
    reservation_engine.seed_item(item_id, "PLATELETS", "A", "POSITIVE", "hosp-2")

    # Create a reservation that is already expired
    past_time = datetime.utcnow() - timedelta(minutes=121)
    success, res, _ = reservation_engine.create_reservation(
        hospital_id="hosp-2",
        clinical_encounter_id="enc-exp",
        din_number=item_id,
        reserved_by="test_user",
        reserved_at=past_time
    )
    assert success is True
    assert reservation_engine._inventory[item_id]['status'] == 'RESERVED'

    # Run reconciliation
    expired_list = reservation_engine.reconcile_expired_leases()

    # Assert the item was reconciled
    assert len(expired_list) == 1
    assert expired_list[0]["reservation_id"] == res["reservation_id"]
    assert expired_list[0]["status"] == "EXPIRED"

    # Assert inventory is restored
    assert reservation_engine._inventory[item_id]['status'] == 'AVAILABLE'

    # Assert audit log was called
    mock_audit_ledger.record_mutation.assert_called_with(
        entity_name='compliance_log',
        entity_id=res['reservation_id'],
        action_type='AUTO_LEASE_EXPIRED',
        performed_by='system_reconciliation_worker',
        old_state={'status': 'ACTIVE', 'din': item_id},
        new_state={'status': 'EXPIRED', 'returned_to_stock': True}
    )
