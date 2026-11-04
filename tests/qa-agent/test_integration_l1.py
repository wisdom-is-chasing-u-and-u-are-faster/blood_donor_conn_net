"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   integration
Source:  test_strategy/plans/cloned_repo__integration.json
Generated: 2026-11-04T14:18:00Z
"""
from datetime import datetime, timedelta
import pytest
from app import app
from services.dispatch_service import DispatchStateMachine
from services.reservation_service import ReservationEngine
from services.audit_service import audit_ledger
from services.security_service import SecurityService


def test_cloned_repo_integration_001():
    """Emergency dispatch state machine integrates with SQS worker and audit ledger.

    test_id: cloned_repo__integration__001
    target: services.dispatch_service.DispatchStateMachine
    requirement_id: REQ-001, REQ-006
    ac_ids: REQ-001-AC-1, REQ-006-AC-4
    """
    sm = DispatchStateMachine()
    disp = sm.create_dispatch(
        hospital_id="hosp-1",
        severity="LEVEL_1_CATASTROPHIC",
        required_abo="O",
        required_rh="NEGATIVE",
        units_requested=4,
        initiated_by="Dr. Trauma"
    )
    dispatch_id = disp["dispatch_id"]
    sm.enqueue_sqs_message({
        "dispatch_id": dispatch_id,
        "donor_id": "marcus_vance",
        "phone": "+15550199",
        "text": "Urgent O- needed"
    })
    worker_res = sm.process_sqs_worker()
    assert worker_res["status"] == "PROCESSED"
    assert len(sm._notifications) == 1
    assert sm._notifications[0]["channels"] == ["FCM_PUSH", "TWILIO_SMS"]

    ok1, err1 = sm.transition_status(dispatch_id, "MATCHING", "system")
    assert ok1 is True
    assert err1 is None

    ok2, err2 = sm.transition_status(dispatch_id, "DISPATCHED", "system")
    assert ok2 is True
    assert err2 is None
    assert sm.get_dispatch(dispatch_id)["status"] == "DISPATCHED"

    intact, audit_err = audit_ledger.verify_integrity()
    assert intact is True
    assert audit_err is None


def test_cloned_repo_integration_001_negative_invalid_transition():
    """Dispatch state machine blocks invalid transitions and routes failed SQS messages to DLQ.

    test_id: cloned_repo__integration__001_negative_invalid_transition
    target: services.dispatch_service.DispatchStateMachine
    requirement_id: REQ-001
    ac_ids: REQ-001-AC-1
    """
    sm = DispatchStateMachine()
    disp = sm.create_dispatch(
        hospital_id="hosp-1",
        severity="LEVEL_1_CATASTROPHIC",
        required_abo="O",
        required_rh="NEGATIVE",
        units_requested=2,
        initiated_by="Dr. Trauma"
    )
    ok, err = sm.transition_status(disp["dispatch_id"], "FULFILLED", "system")
    assert ok is False
    assert "INVALID_STATE_TRANSITION" in err

    sm.enqueue_sqs_message({"dispatch_id": disp["dispatch_id"], "text": "Simulated failure"})
    r1 = sm.process_sqs_worker(fail_simulation=True)
    assert r1["status"] == "RETRYING"
    assert r1["retry_count"] == 1

    r2 = sm.process_sqs_worker(fail_simulation=True)
    assert r2["status"] == "RETRYING"
    assert r2["retry_count"] == 2

    r3 = sm.process_sqs_worker(fail_simulation=True)
    assert r3["status"] == "DLQ_ROUTED"

    redriven = sm.redrive_dlq()
    assert redriven == 1


def test_cloned_repo_integration_002():
    """ReservationEngine lifecycle integrates with AuditLedger and SecurityService WORM export.

    test_id: cloned_repo__integration__002
    target: services.reservation_service.ReservationEngine
    requirement_id: REQ-003, REQ-005, REQ-006
    ac_ids: REQ-003-AC-1, REQ-005-AC-1, REQ-006-AC-4
    """
    engine = ReservationEngine()
    sec = SecurityService()
    t0 = datetime(2026, 6, 1, 10, 0, 0)

    engine.seed_item("W036525880001", "RED_BLOOD_CELLS", "O", "NEGATIVE", "hosp-1")
    engine.seed_item("W036525880002", "RED_BLOOD_CELLS", "O", "NEGATIVE", "hosp-1")

    ok1, res1, _ = engine.create_reservation("hosp-1", "ENC-201", "W036525880001", reserved_at=t0)
    ok2, res2, _ = engine.create_reservation("hosp-1", "ENC-202", "W036525880002", reserved_at=t0)
    assert ok1 is True
    assert ok2 is True

    consumed = engine.confirm_consumption(res1["reservation_id"], "Dr. Lin")
    assert consumed is True

    expired = engine.reconcile_expired_leases(current_time=t0 + timedelta(minutes=125))
    assert len(expired) == 1
    assert expired[0]["reservation_id"] == res2["reservation_id"]
    assert engine.get_available_count("hosp-1", "O", "NEGATIVE") == 1

    export = sec.create_worm_export("WORM-INT-01", audit_ledger.get_logs(), "auditor")
    assert export["is_locked"] is True
    assert sec.verify_worm_export("WORM-INT-01") == (True, None)
    assert audit_ledger.verify_integrity() == (True, None)
