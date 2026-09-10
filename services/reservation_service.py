"""
Reservation Service - 120-Minute Reservation Lease Engine & Auto-Release Worker
Enforces strict 120-minute reservation leases, atomic row-level locking,
and background expiration restitution.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import threading
from services.audit_service import audit_ledger


class ReservationEngine:
    def __init__(self):
        self._lock = threading.Lock()
        self._inventory: Dict[str, Dict[str, Any]] = {}  # din -> item
        self._reservations: Dict[str, Dict[str, Any]] = {}  # res_id -> res

    def seed_item(self, din_number: str, component_type: str, abo_type: str, rh_factor: str, hospital_id: str):
        with self._lock:
            self._inventory[din_number] = {
                "item_id": f"item-{din_number}",
                "hospital_id": hospital_id,
                "din_number": din_number,
                "component_type": component_type,
                "abo_type": abo_type,
                "rh_factor": rh_factor,
                "status": "AVAILABLE",
                "collection_date": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "expiration_date": (datetime.utcnow() + timedelta(days=35)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "storage_temp_celsius": 4.0
            }

    def get_available_count(self, hospital_id: str, abo_type: str, rh_factor: str) -> int:
        with self._lock:
            return sum(
                1 for item in self._inventory.values()
                if item["hospital_id"] == hospital_id and
                   item["abo_type"] == abo_type and
                   item["rh_factor"] == rh_factor and
                   item["status"] == "AVAILABLE"
            )

    def create_reservation(
        self,
        hospital_id: str,
        clinical_encounter_id: str,
        din_number: str,
        reserved_by: str = "Dr. Sarah Lin",
        reserved_at: Optional[datetime] = None
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Creates an active reservation with an immutable 120-minute lease.
        Decrements available stock atomically.
        """
        with self._lock:
            item = self._inventory.get(din_number)
            if not item:
                return False, None, "ITEM_NOT_FOUND"

            if item["status"] != "AVAILABLE":
                return False, None, f"ITEM_NOT_AVAILABLE (Status: {item['status']})"

            res_time = reserved_at or datetime.utcnow()
            expires_at = res_time + timedelta(minutes=120)
            res_id = f"res-{clinical_encounter_id}-{din_number}"

            # Atomically lock & reserve
            item["status"] = "RESERVED"

            reservation = {
                "reservation_id": res_id,
                "hospital_id": hospital_id,
                "clinical_encounter_id": clinical_encounter_id,
                "din_number": din_number,
                "status": "ACTIVE",
                "reserved_at": res_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "expires_at": expires_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "released_at": None,
                "reserved_by": reserved_by
            }
            self._reservations[res_id] = reservation

            # Audit log
            audit_ledger.record_mutation(
                entity_name="inventory_reservations",
                entity_id=res_id,
                action_type="INSERT",
                performed_by=reserved_by,
                new_state=reservation
            )

            return True, reservation, None

    def confirm_consumption(self, reservation_id: str, confirmed_by: str) -> bool:
        with self._lock:
            res = self._reservations.get(reservation_id)
            if not res or res["status"] != "ACTIVE":
                return False

            res["status"] = "CONSUMED"
            item = self._inventory.get(res["din_number"])
            if item:
                item["status"] = "CONSUMED"

            audit_ledger.record_mutation(
                entity_name="inventory_reservations",
                entity_id=reservation_id,
                action_type="UPDATE",
                performed_by=confirmed_by,
                old_state={"status": "ACTIVE"},
                new_state={"status": "CONSUMED"}
            )
            return True

    def reconcile_expired_leases(self, current_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Background Worker: Releases unconsumed reservations past their 120-min lease
        back to AVAILABLE inventory and writes audit entries.
        """
        now = current_time or datetime.utcnow()
        expired_records = []

        with self._lock:
            for res_id, res in self._reservations.items():
                if res["status"] == "ACTIVE":
                    expires_dt = datetime.strptime(res["expires_at"], "%Y-%m-%dT%H:%M:%SZ")
                    if now >= expires_dt:
                        # Transition to EXPIRED
                        res["status"] = "EXPIRED"
                        res["released_at"] = now.strftime("%Y-%m-%dT%H:%M:%SZ")

                        # Restore unit to AVAILABLE
                        item = self._inventory.get(res["din_number"])
                        if item:
                            item["status"] = "AVAILABLE"

                        audit_ledger.record_mutation(
                            entity_name="compliance_log",
                            entity_id=res_id,
                            action_type="AUTO_LEASE_EXPIRED",
                            performed_by="system_reconciliation_worker",
                            old_state={"status": "ACTIVE", "din": res["din_number"]},
                            new_state={"status": "EXPIRED", "returned_to_stock": True}
                        )
                        expired_records.append(res)

        return expired_records


reservation_engine = ReservationEngine()
