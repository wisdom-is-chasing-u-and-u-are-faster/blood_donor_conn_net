"""
Test Suite for Compliance, Audit Trail & Security Ledger (ARCH-1197, ARCH-1195, ARCH-1196, ARCH-1199)
Validates append-only ledger, SHA-256 hash chaining, tamper detection, and audit compliance.
"""
import pytest
from services.audit_service import AuditLedger


@pytest.fixture
def clean_ledger():
    return AuditLedger()


def test_audit_record_mutation_and_hash_chain(clean_ledger):
    # Record 3 events
    e1 = clean_ledger.record_mutation(
        entity_name="inventory_items",
        entity_id="b0000000-0000-0000-0000-000000000001",
        action_type="INSERT",
        performed_by="dr_lin",
        new_state={"din": "W036525000101", "units": 1}
    )
    assert e1["previous_hash"] == "0" * 64
    assert len(e1["checksum_signature"]) == 64

    e2 = clean_ledger.record_mutation(
        entity_name="inventory_reservations",
        entity_id="r0000000-0000-0000-0000-000000000001",
        action_type="INSERT",
        performed_by="dr_lin",
        new_state={"encounter": "ENC-TRAUMA-9912", "status": "ACTIVE"}
    )
    assert e2["previous_hash"] == e1["checksum_signature"]

    e3 = clean_ledger.record_mutation(
        entity_name="inventory_reservations",
        entity_id="r0000000-0000-0000-0000-000000000001",
        action_type="UPDATE",
        performed_by="system_worker",
        old_state={"status": "ACTIVE"},
        new_state={"status": "EXPIRED"}
    )
    assert e3["previous_hash"] == e2["checksum_signature"]

    # Verify intact chain
    is_valid, err = clean_ledger.verify_integrity()
    assert is_valid is True
    assert err is None


def test_tamper_detection_in_audit_chain(clean_ledger):
    clean_ledger.record_mutation("inventory_items", "item-1", "INSERT", "user-1", new_state={"status": "AVAILABLE"})
    clean_ledger.record_mutation("inventory_items", "item-1", "UPDATE", "user-2", old_state={"status": "AVAILABLE"}, new_state={"status": "RESERVED"})

    # Intact check
    assert clean_ledger.verify_integrity()[0] is True

    # Malicious modification of log entry
    clean_ledger._logs[0]["new_state"]["status"] = "TAMPERED_STATUS"

    # Integrity verification must fail
    is_valid, err = clean_ledger.verify_integrity()
    assert is_valid is False
    assert "Tampered record at log_id 1" in err
