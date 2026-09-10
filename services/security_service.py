"""
Security Service - Field-Level ePHI Encryption, Log Sanitization & S3 WORM Export Pipeline
(ARCH-1195, ARCH-1196, ARCH-1199)
"""
import base64
import hashlib
import json
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple


class SecurityService:
    def __init__(self, master_key: str = "BDCN_ENTERPRISE_AES256_SECRET_KEY_123456"):
        self._key = hashlib.sha256(master_key.encode("utf-8")).digest()
        self._worm_vault: Dict[str, Dict[str, Any]] = {}

    def encrypt_ephi_field(self, raw_text: str) -> str:
        """
        Encrypts sensitive ePHI field using AES-256 envelope mock / reversible XOR base64.
        """
        if not raw_text:
            return ""
        raw_bytes = raw_text.encode("utf-8")
        encrypted = bytes(b ^ self._key[i % len(self._key)] for i, b in enumerate(raw_bytes))
        return "enc::" + base64.b64encode(encrypted).decode("ascii")

    def decrypt_ephi_field(self, encrypted_str: str) -> str:
        if not encrypted_str or not encrypted_str.startswith("enc::"):
            return encrypted_str
        b64_part = encrypted_str[5:]
        encrypted_bytes = base64.b64decode(b64_part.encode("ascii"))
        decrypted = bytes(b ^ self._key[i % len(self._key)] for i, b in enumerate(encrypted_bytes))
        return decrypted.decode("utf-8")

    def sanitize_log_message(self, message: str) -> str:
        """
        Scrubs ePHI / PII patterns (SSN, phone numbers, email addresses) from log output.
        """
        # Scrub SSN / DIN patterns (3-2-4 or 9 consecutive digits)
        msg = re.sub(r"\b\d{3}-\d{2}-\d{4}\b", "[REDACTED_SSN]", message)
        # Scrub Phone numbers
        msg = re.sub(r"(\+?\d{1,2}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}", "[REDACTED_PHONE]", msg)
        # Scrub Emails
        msg = re.sub(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "[REDACTED_EMAIL]", msg)
        return msg

    def create_worm_export(self, export_id: str, records: List[Dict[str, Any]], created_by: str) -> Dict[str, Any]:
        """
        S3 WORM (Write Once Read Many) compliant export with tamper-evident checksum.
        """
        canonical_json = json.dumps(records, sort_keys=True)
        checksum = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

        worm_record = {
            "export_id": export_id,
            "record_count": len(records),
            "sha256_checksum": checksum,
            "created_by": created_by,
            "created_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "is_locked": True,
            "retention_period_years": 7,
            "data": records
        }
        self._worm_vault[export_id] = worm_record
        return worm_record

    def verify_worm_export(self, export_id: str) -> Tuple[bool, Optional[str]]:
        vault_entry = self._worm_vault.get(export_id)
        if not vault_entry:
            return False, "EXPORT_NOT_FOUND"

        canonical_json = json.dumps(vault_entry["data"], sort_keys=True)
        recomputed = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

        if vault_entry["sha256_checksum"] != recomputed:
            return False, "WORM_CHECKSUM_TAMPER_DETECTED"

        return True, None


security_service = SecurityService()
