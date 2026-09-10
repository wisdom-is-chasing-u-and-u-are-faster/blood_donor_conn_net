"""
Dispatch Service - Emergency Dispatch API, State Machine & SQS / Notification Worker
Implements Emergency Dispatch Lifecycle, FIFO Asynchronous SQS Queue, DLQ Redrive,
and Multi-Channel FCM / SMS Notification Gateways.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import uuid
from services.audit_service import audit_ledger


class DispatchStateMachine:
    VALID_TRANSITIONS = {
        "INITIATED": ["MATCHING", "CANCELLED"],
        "MATCHING": ["DISPATCHED", "CANCELLED", "EXPIRED"],
        "DISPATCHED": ["ACCEPTED", "FULFILLED", "EXPIRED", "CANCELLED"],
        "ACCEPTED": ["IN_TRANSIT", "CANCELLED", "EXPIRED"],
        "IN_TRANSIT": ["FULFILLED", "CANCELLED"],
        "FULFILLED": [],
        "EXPIRED": [],
        "CANCELLED": []
    }

    def __init__(self):
        self._dispatches: Dict[str, Dict[str, Any]] = {}
        self._sqs_queue: List[Dict[str, Any]] = []
        self._dlq_queue: List[Dict[str, Any]] = []
        self._notifications: List[Dict[str, Any]] = []

    def create_dispatch(
        self,
        hospital_id: str,
        severity: str,
        required_abo: str,
        required_rh: str,
        units_requested: int,
        initiated_by: str,
        search_radius_km: float = 15.0,
        target_lat: float = 37.7749,
        target_lon: float = -122.4194
    ) -> Dict[str, Any]:
        dispatch_id = f"disp-{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow()
        expires_at = now + timedelta(minutes=180)

        dispatch = {
            "dispatch_id": dispatch_id,
            "hospital_id": hospital_id,
            "severity": severity,
            "required_abo": required_abo,
            "required_rh": required_rh,
            "units_requested": units_requested,
            "units_confirmed": 0,
            "search_radius_km": search_radius_km,
            "target_lat": target_lat,
            "target_lon": target_lon,
            "status": "INITIATED",
            "initiated_by": initiated_by,
            "created_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "expires_at": expires_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "candidates": []
        }
        self._dispatches[dispatch_id] = dispatch

        # Audit log
        audit_ledger.record_mutation(
            entity_name="emergency_dispatches",
            entity_id=dispatch_id,
            action_type="INSERT",
            performed_by=initiated_by,
            new_state=dispatch
        )

        return dispatch

    def transition_status(self, dispatch_id: str, next_status: str, updated_by: str) -> Tuple[bool, Optional[str]]:
        dispatch = self._dispatches.get(dispatch_id)
        if not dispatch:
            return False, "DISPATCH_NOT_FOUND"

        current_status = dispatch["status"]
        allowed = self.VALID_TRANSITIONS.get(current_status, [])
        if next_status not in allowed:
            return False, f"INVALID_STATE_TRANSITION from {current_status} to {next_status}"

        old_state = {"status": current_status}
        dispatch["status"] = next_status

        audit_ledger.record_mutation(
            entity_name="emergency_dispatches",
            entity_id=dispatch_id,
            action_type="UPDATE",
            performed_by=updated_by,
            old_state=old_state,
            new_state={"status": next_status}
        )
        return True, None

    def enqueue_sqs_message(self, message: Dict[str, Any]):
        msg_id = f"msg-{uuid.uuid4().hex[:8]}"
        payload = {
            "message_id": msg_id,
            "body": message,
            "retry_count": 0,
            "enqueued_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        }
        self._sqs_queue.append(payload)
        return msg_id

    def process_sqs_worker(self, fail_simulation: bool = False) -> Dict[str, Any]:
        """
        Simulates SQS Async worker consumption with Dead-Letter-Queue (DLQ) retry policy.
        """
        if not self._sqs_queue:
            return {"processed": 0, "dlq_count": len(self._dlq_queue)}

        msg = self._sqs_queue.pop(0)
        if fail_simulation:
            msg["retry_count"] += 1
            if msg["retry_count"] >= 3:
                # Max retries reached, route to DLQ
                self._dlq_queue.append(msg)
                return {"status": "DLQ_ROUTED", "message_id": msg["message_id"]}
            else:
                self._sqs_queue.append(msg)
                return {"status": "RETRYING", "retry_count": msg["retry_count"]}

        # Process successful delivery via Multi-Channel Notification Gateways
        body = msg["body"]
        self.send_multi_channel_notification(
            recipient_id=body.get("donor_id", "unknown"),
            phone=body.get("phone", "+15550100"),
            message_text=body.get("text", "Emergency blood donation alert!")
        )
        return {"status": "PROCESSED", "message_id": msg["message_id"]}

    def redrive_dlq(self) -> int:
        count = len(self._dlq_queue)
        for msg in list(self._dlq_queue):
            msg["retry_count"] = 0
            self._sqs_queue.append(msg)
        self._dlq_queue.clear()
        return count

    def send_multi_channel_notification(self, recipient_id: str, phone: str, message_text: str) -> Dict[str, Any]:
        """
        Multi-Channel Notification Gateway (FCM Push + Twilio SMS).
        """
        notif_id = f"notif-{uuid.uuid4().hex[:8]}"
        notif_record = {
            "notification_id": notif_id,
            "recipient_id": recipient_id,
            "phone": phone,
            "message_text": message_text,
            "channels": ["FCM_PUSH", "TWILIO_SMS"],
            "status": "DELIVERED",
            "delivered_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        }
        self._notifications.append(notif_record)
        return notif_record

    def get_dispatch(self, dispatch_id: str) -> Optional[Dict[str, Any]]:
        return self._dispatches.get(dispatch_id)


dispatch_engine = DispatchStateMachine()
