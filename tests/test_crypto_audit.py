import pytest
from services.crypto_service import CryptoService, crypto_service
from services.audit_service import AuditService, audit_service
from db.init_db import reset_database


@pytest.fixture(autouse=True)
def setup_env():
    reset_database()
    yield


def test_aes_256_gcm_encryption_and_decryption():
    """[ARCH-2103-AC1] [ARCH-2120-AC1] Test AES-256-GCM encryption with 96-bit IV and accurate decryption."""
    national_id = "SSN-998-22-1144"
    encrypted = crypto_service.encrypt_ephi(national_id)

    assert encrypted.startswith("AES256GCM:")
    assert national_id not in encrypted  # Zero plaintext leakage

    decrypted = crypto_service.decrypt_ephi(encrypted)
    assert decrypted == national_id


def test_unique_iv_per_encryption():
    """Verify that multiple encryptions of the same plaintext produce different ciphertexts (unique IV)."""
    text = "Secret Clinical Encounter Notes"
    enc1 = crypto_service.encrypt_ephi(text)
    enc2 = crypto_service.encrypt_ephi(text)

    assert enc1 != enc2
    assert crypto_service.decrypt_ephi(enc1) == text
    assert crypto_service.decrypt_ephi(enc2) == text


def test_worm_audit_ledger_hash_chaining():
    """[ARCH-2103-AC2] Test SHA-256 cryptographic hash chaining in WORM audit ledger."""
    event1 = audit_service.log_event(
        actor_user_id="dr_house",
        action_type="EMERGENCY_ACCESS",
        resource_type="PATIENT_RECORD",
        resource_id="rec-001",
        payload={"reason": "Acute trauma hemorrhage"}
    )

    event2 = audit_service.log_event(
        actor_user_id="nurse_jackie",
        action_type="INVENTORY_ALLOCATE",
        resource_type="BLOOD_UNIT",
        resource_id="unit-001",
        payload={"blood_type": "O_NEG"}
    )

    assert event2["previousHashSha256"] == event1["payloadHashSha256"]

    # Verify integrity
    is_valid, total, tampered = audit_service.verify_ledger_integrity()
    assert is_valid is True
    assert total >= 3
    assert tampered == 0
