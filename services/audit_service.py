"""
Audit Service - FDA 21 CFR Part 11 & HIPAA Tamper-Evident Ledger
Implements cryptographic SHA-256 hash chaining, append-only constraints,
and ledger verification.
"""
import hashlib
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple


class AuditLedger:
    def __init__(self):
        self._logs: List[Dict[str, Any]] = []
        self._genesis_hash: str = "0" * 64

    def record_mutation(
        self,
        entity_name: str,
        entity_id: str,
        action_type: str,
        performed_by: str,
        old_state: Optional[Dict[str, Any]] = None,
        new_state: Optional[Dict[str, Any]] = None,
        client_ip: Optional[str] = "127.0.0.1",
        timestamp: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Appends an immutable audit record to the ledger with cryptographic hash chaining.
        """
        performed_at = timestamp or datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        log_id = len(self._logs) + 1

        previous_hash = self._logs[-1]["checksum_signature"] if self._logs else self._genesis_hash

        # Canonicalize payload for deterministic hashing
        old_str = json.dumps(old_state, sort_keys=True) if old_state else ""
        new_str = json.dumps(new_state, sort_keys=True) if new_state else ""
        
        raw_payload = f"{previous_hash}|{log_id}|{entity_name}|{entity_id}|{action_type}|{performed_by}|{performed_at}|{old_str}|{new_str}"
        checksum_signature = hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()

        entry = {
            "log_id": log_id,
            "entity_name": entity_name,
            "entity_id": str(entity_id),
            "action_type": action_type.upper(),
            "performed_by": performed_by,
            "performed_at": performed_at,
            "old_state": old_state,
            "new_state": new_state,
            "client_ip": client_ip,
            "previous_hash": previous_hash,
            "checksum_signature": checksum_signature
        }

        self._logs.append(entry)
        return entry

    def verify_integrity(self) -> Tuple[bool, Optional[str]]:
        """
        Validates the entire chain from genesis to head.
        Returns (True, None) if intact, or (False, error_details) if tampered.
        """
        expected_prev = self._genesis_hash

        for i, log in enumerate(self._logs):
            if log["previous_hash"] != expected_prev:
                return False, f"Broken chain at log_id {log['log_id']}: expected prev {expected_prev}, got {log['previous_hash']}"

            old_str = json.dumps(log["old_state"], sort_keys=True) if log["old_state"] else ""
            new_str = json.dumps(log["new_state"], sort_keys=True) if log["new_state"] else ""
            raw_payload = f"{log['previous_hash']}|{log['log_id']}|{log['entity_name']}|{log['entity_id']}|{log['action_type']}|{log['performed_by']}|{log['performed_at']}|{old_str}|{new_str}"
            recomputed = hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()

            if log["checksum_signature"] != recomputed:
                return False, f"Tampered record at log_id {log['log_id']}: signature mismatch"

            expected_prev = log["checksum_signature"]

        return True, None

    def get_logs(self, entity_name: Optional[str] = None, entity_id: Optional[str] = None) -> List[Dict[str, Any]]:
        filtered = self._logs
        if entity_name:
            filtered = [l for l in filtered if l["entity_name"] == entity_name]
        if entity_id:
            filtered = [l for l in filtered if str(l["entity_id"]) == str(entity_id)]
        return list(filtered)


# Global singleton instance
audit_ledger = AuditLedger()
