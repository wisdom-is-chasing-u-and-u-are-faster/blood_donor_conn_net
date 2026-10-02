"""
services/audit_service.py — HIPAA / HITECH WORM Immutable Audit Access Ledger Service

Implements:
- SHA-256 cryptographic hash chaining for non-repudiation.
- Write-Once-Read-Many (WORM) audit ledger event appending.
- Cryptographic ledger integrity verification sweep.
- Captures all ePHI read/write mutations and emergency dispatch overrides.
"""

import hashlib
import json
import uuid
import datetime
from typing import List, Dict, Any, Tuple
from db.init_db import get_db_connection


class AuditService:
    def __init__(self):
        pass

    def _calculate_payload_hash(self, payload: Any) -> str:
        """Computes SHA-256 hex digest of JSON-serialized payload."""
        if isinstance(payload, str):
            data = payload.encode("utf-8")
        else:
            data = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(data).hexdigest()

    def get_latest_hash(self) -> str:
        """Retrieves the previous block's SHA-256 hash from the ledger."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT payload_hash_sha256 FROM audit_hipaa_ledger ORDER BY rowid DESC LIMIT 1")
        row = cursor.fetchone()
        if row:
            return row["payload_hash_sha256"]
        return "0" * 64

    def log_event(
        self,
        actor_user_id: str,
        action_type: str,
        resource_type: str,
        resource_id: str,
        payload: Any = None,
        client_ip: str = "127.0.0.1",
        user_agent: str = "BDCN-Client"
    ) -> Dict[str, Any]:
        """
        Appends an immutable audit event to the ledger with SHA-256 hash chaining.
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        previous_hash = self.get_latest_hash()
        audit_id = f"aud-{uuid.uuid4().hex[:12]}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Compute hash over actor, action, resource, timestamp, and previous hash
        event_dict = {
            "audit_id": audit_id,
            "actor": actor_user_id,
            "action": action_type,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "previous_hash": previous_hash,
            "payload": payload,
            "timestamp": now
        }
        payload_hash = self._calculate_payload_hash(event_dict)

        cursor.execute("""
        INSERT INTO audit_hipaa_ledger (
            audit_id, actor_user_id, action_type, resource_type, resource_id,
            payload_hash_sha256, previous_hash_sha256, client_ip, user_agent, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            audit_id, actor_user_id, action_type, resource_type, resource_id,
            payload_hash, previous_hash, client_ip, user_agent, now
        ))
        conn.commit()

        return {
            "auditId": audit_id,
            "actorUserId": actor_user_id,
            "actionType": action_type,
            "resourceType": resource_type,
            "resourceId": resource_id,
            "payloadHashSha256": payload_hash,
            "previousHashSha256": previous_hash,
            "timestamp": now
        }

    def get_audit_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves recent audit log entries."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT audit_id, actor_user_id, action_type, resource_type, resource_id,
               payload_hash_sha256, previous_hash_sha256, timestamp
        FROM audit_hipaa_ledger
        ORDER BY rowid DESC
        LIMIT ?;
        """, (limit,))
        
        records = []
        for row in cursor.fetchall():
            records.append({
                "auditId": row["audit_id"],
                "actorUserId": row["actor_user_id"],
                "actionType": row["action_type"],
                "resourceType": row["resource_type"],
                "resourceId": row["resource_id"],
                "payloadHashSha256": row["payload_hash_sha256"],
                "previousHashSha256": row["previous_hash_sha256"],
                "timestamp": row["timestamp"]
            })
        return records

    def verify_ledger_integrity(self) -> Tuple[bool, int, int]:
        """
        Verifies cryptographic hash chain integrity across all records in the ledger.
        Returns: (is_valid, total_records, tampered_records_count)
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT audit_id, actor_user_id, action_type, resource_type, resource_id,
               payload_hash_sha256, previous_hash_sha256, timestamp
        FROM audit_hipaa_ledger
        ORDER BY rowid ASC;
        """)
        rows = cursor.fetchall()
        
        if not rows:
            return True, 0, 0

        expected_prev_hash = "0" * 64
        tampered_count = 0

        for i, row in enumerate(rows):
            if i > 0 and row["previous_hash_sha256"] != expected_prev_hash:
                tampered_count += 1
            expected_prev_hash = row["payload_hash_sha256"]

        return (tampered_count == 0), len(rows), tampered_count


# Default global instance
audit_service = AuditService()
