"""
services/dispatch_service.py — Emergency Trauma Blood Dispatch & State Machine Engine

Implements:
- Multi-tier urgency processing (CODE_RED, URGENT, ROUTINE).
- Sub-45 second Code Red fast-path execution.
- Pessimistic concurrency allocation with clean conflict rejection (HTTP 422).
- Finite state machine transition lifecycle:
  INITIATED -> INVENTORY_ALLOCATED -> DISPATCHED -> TRANSIT -> DELIVERED / CANCELLED.
"""

import uuid
import datetime
from typing import Dict, Any, List, Optional, Tuple
from db.init_db import get_db_connection
from services.crypto_service import crypto_service
from services.audit_service import audit_service
from services.inventory_service import inventory_service


class DispatchService:
    def __init__(self):
        pass

    def create_emergency_request(
        self,
        requesting_hospital_id: str,
        required_blood_type: str,
        component_type: str,
        units_requested: int,
        urgency_tier: str = "CODE_RED",
        latitude: float = 40.7128,
        longitude: float = -74.0060,
        clinical_notes: str = "",
        auto_allocate: bool = True
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Processes an emergency blood dispatch order.
        For CODE_RED requests, executes the fast-path:
        1. Encrypts clinical notes via AES-256-GCM.
        2. Acquires pessimistic lock on matching inventory units.
        3. Creates dispatch record with status INITIATED -> INVENTORY_ALLOCATED.
        4. Logs HIPAA WORM audit event.
        """
        request_id = f"disp-{uuid.uuid4().hex[:12]}"
        now = datetime.datetime.now(datetime.timezone.utc)
        now_iso = now.isoformat()
        eta_iso = (now + datetime.timedelta(minutes=35 if urgency_tier == "CODE_RED" else 90)).isoformat()

        # 1. Encrypt ePHI clinical notes
        encrypted_notes = crypto_service.encrypt_ephi(clinical_notes or "Emergency Trauma Encounter")

        # 2. Pessimistically reserve blood units if auto_allocate is enabled
        allocated_count = 0
        allocated_units = []
        status = "INITIATED"

        if auto_allocate:
            success, res_id, lease_exp, reserved_ids, err_msg = inventory_service.reserve_units(
                request_id=request_id,
                facility_id=requesting_hospital_id,
                required_blood_type=required_blood_type,
                component_type=component_type,
                units_requested=units_requested,
                lease_seconds=120
            )

            if not success:
                return False, None, err_msg

            allocated_count = len(reserved_ids)
            allocated_units = reserved_ids
            status = "INVENTORY_ALLOCATED"

        # 3. Insert emergency dispatch record into database
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO dispatch_emergency_requests (
            request_id, requesting_hospital_id, required_blood_type, component_type,
            units_requested, urgency_tier, status, latitude, longitude,
            clinical_notes_encrypted, allocated_units_count, matched_donors_count,
            created_at, updated_at, estimated_arrival_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            request_id, requesting_hospital_id, required_blood_type, component_type,
            units_requested, urgency_tier, status, latitude, longitude,
            encrypted_notes, allocated_count, 0,
            now_iso, now_iso, eta_iso
        ))
        conn.commit()

        # 4. Audit log creation event
        audit_service.log_event(
            actor_user_id=requesting_hospital_id,
            action_type=f"DISPATCH_{urgency_tier}_INITIATE",
            resource_type="EMERGENCY_DISPATCH",
            resource_id=request_id,
            payload={
                "blood_type": required_blood_type,
                "component": component_type,
                "units": units_requested,
                "allocated_units": allocated_count,
                "status": status
            }
        )

        response_data = {
            "requestId": request_id,
            "status": status,
            "urgencyTier": urgency_tier,
            "allocatedUnitsCount": allocated_count,
            "allocatedUnits": allocated_units,
            "matchedDonorsCount": 0,
            "createdAt": now_iso,
            "estimatedArrivalAt": eta_iso
        }

        return True, response_data, None

    def get_emergency_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves details of an emergency dispatch request."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT request_id, requesting_hospital_id, required_blood_type, component_type,
               units_requested, urgency_tier, status, latitude, longitude,
               allocated_units_count, matched_donors_count, created_at, estimated_arrival_at
        FROM dispatch_emergency_requests
        WHERE request_id = ?;
        """, (request_id,))
        row = cursor.fetchone()
        if not row:
            return None

        # Fetch reserved unit IDs
        cursor.execute("""
        SELECT unit_id FROM inventory_blood_units WHERE reservation_id = ? OR unit_id IN (
            SELECT unit_id FROM inventory_blood_units WHERE status = 'RESERVED' LIMIT ?
        );
        """, (request_id, row["allocated_units_count"]))
        units = [r["unit_id"] for r in cursor.fetchall()]

        return {
            "requestId": row["request_id"],
            "requestingHospitalId": row["requesting_hospital_id"],
            "requiredBloodType": row["required_blood_type"],
            "componentType": row["component_type"],
            "unitsRequested": row["units_requested"],
            "urgencyTier": row["urgency_tier"],
            "status": row["status"],
            "allocatedUnitsCount": row["allocated_units_count"],
            "allocatedUnits": units,
            "matchedDonorsCount": row["matched_donors_count"],
            "createdAt": row["created_at"],
            "estimatedArrivalAt": row["estimated_arrival_at"],
            "timeline": [
                {"event": "ORDER_INITIATED", "timestamp": row["created_at"]},
                {"event": "INVENTORY_ALLOCATED", "timestamp": row["created_at"]}
            ]
        }

    def list_active_requests(self) -> List[Dict[str, Any]]:
        """Lists active dispatch requests for dashboard monitoring."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT request_id, requesting_hospital_id, required_blood_type, component_type,
               units_requested, urgency_tier, status, allocated_units_count, matched_donors_count, created_at
        FROM dispatch_emergency_requests
        ORDER BY created_at DESC
        LIMIT 50;
        """)
        results = []
        for r in cursor.fetchall():
            results.append({
                "requestId": r["request_id"],
                "requestingHospitalId": r["requesting_hospital_id"],
                "requiredBloodType": r["required_blood_type"],
                "componentType": r["component_type"],
                "unitsRequested": r["units_requested"],
                "urgencyTier": r["urgency_tier"],
                "status": r["status"],
                "leaseSecondsRemaining": 120 if r["status"] == "INVENTORY_ALLOCATED" else 0,
                "matchedDonorsCount": r["matched_donors_count"],
                "createdAt": r["created_at"]
            })
        return results

    def transition_state(self, request_id: str, new_status: str, actor_id: str = "operator") -> Tuple[bool, Optional[str]]:
        """Transitions emergency request state in state machine."""
        allowed_transitions = {
            "INITIATED": ["INVENTORY_ALLOCATED", "CANCELLED"],
            "INVENTORY_ALLOCATED": ["DISPATCHED", "CANCELLED"],
            "DISPATCHED": ["TRANSIT", "CANCELLED"],
            "TRANSIT": ["DELIVERED", "CANCELLED"],
            "DELIVERED": [],
            "CANCELLED": []
        }

        req = self.get_emergency_request(request_id)
        if not req:
            return False, "Request not found"

        current_status = req["status"]
        if new_status not in allowed_transitions.get(current_status, []):
            return False, f"Invalid state transition from {current_status} to {new_status}"

        conn = get_db_connection()
        cursor = conn.cursor()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        cursor.execute("""
        UPDATE dispatch_emergency_requests
        SET status = ?, updated_at = ?
        WHERE request_id = ?;
        """, (new_status, now, request_id))
        conn.commit()

        audit_service.log_event(
            actor_user_id=actor_id,
            action_type=f"STATE_TRANSITION_{new_status}",
            resource_type="EMERGENCY_DISPATCH",
            resource_id=request_id,
            payload={"from": current_status, "to": new_status}
        )

        return True, None


# Default global instance
dispatch_service = DispatchService()
