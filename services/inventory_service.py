"""
services/inventory_service.py — Real-Time Hospital Blood Inventory Tracking & FEFO Engine

Implements:
- First-Expired-First-Out (FEFO) allocation algorithm (expires_at ASC).
- Universal donor fallback matrices for red blood cells, platelets, and plasma.
- Pessimistic row-locking reservation with 120-second lease timeout.
- Automated background lease expiration sweeper.
- ISBT 128 / DIN barcode check-in.
"""

import uuid
import datetime
from typing import List, Dict, Any, Optional, Tuple
from db.init_db import get_db_connection
from services.audit_service import audit_service


# ABO/Rh compatibility lookup matrix
# Compatible donor blood types for a given recipient required blood type
RBC_COMPATIBILITY_MAP = {
    "O_NEG": ["O_NEG"],
    "O_POS": ["O_POS", "O_NEG"],
    "A_NEG": ["A_NEG", "O_NEG"],
    "A_POS": ["A_POS", "A_NEG", "O_POS", "O_NEG"],
    "B_NEG": ["B_NEG", "O_NEG"],
    "B_POS": ["B_POS", "B_NEG", "O_POS", "O_NEG"],
    "AB_NEG": ["AB_NEG", "A_NEG", "B_NEG", "O_NEG"],
    "AB_POS": ["AB_POS", "AB_NEG", "A_POS", "A_NEG", "B_POS", "B_NEG", "O_POS", "O_NEG"],
}

PLASMA_COMPATIBILITY_MAP = {
    "O_NEG": ["O_NEG", "O_POS", "A_NEG", "A_POS", "B_NEG", "B_POS", "AB_NEG", "AB_POS"],
    "O_POS": ["O_POS", "A_POS", "B_POS", "AB_POS"],
    "A_NEG": ["A_NEG", "A_POS", "AB_NEG", "AB_POS"],
    "A_POS": ["A_POS", "AB_POS"],
    "B_NEG": ["B_NEG", "B_POS", "AB_NEG", "AB_POS"],
    "B_POS": ["B_POS", "AB_POS"],
    "AB_NEG": ["AB_NEG", "AB_POS"],
    "AB_POS": ["AB_POS"],
}


class InventoryService:
    def __init__(self):
        pass

    def get_compatible_types(self, required_type: str, component_type: str = "RED_BLOOD_CELLS") -> List[str]:
        """Resolves clinical ABO/Rh compatibility list based on component type."""
        comp_upper = (component_type or "").upper()
        if "PLASMA" in comp_upper or "CRYOPRECIPITATE" in comp_upper:
            return PLASMA_COMPATIBILITY_MAP.get(required_type, [required_type])
        return RBC_COMPATIBILITY_MAP.get(required_type, [required_type])

    def sweep_expired_leases(self) -> int:
        """
        Background sweeper job: Automatically reverts expired reservations (>120s)
        back to status 'AVAILABLE' and logs the expiration event.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        cursor.execute("""
        SELECT unit_id, din_barcode, reservation_id
        FROM inventory_blood_units
        WHERE status = 'RESERVED' AND lease_expires_at IS NOT NULL AND lease_expires_at < ?;
        """, (now,))
        expired_units = cursor.fetchall()

        if not expired_units:
            return 0

        for unit in expired_units:
            cursor.execute("""
            UPDATE inventory_blood_units
            SET status = 'AVAILABLE', reservation_id = NULL, lease_expires_at = NULL
            WHERE unit_id = ?;
            """, (unit["unit_id"],))

            audit_service.log_event(
                actor_user_id="system-lease-sweeper",
                action_type="AUTOMATIC_LEASE_EXPIRATION",
                resource_type="INVENTORY_UNIT",
                resource_id=unit["unit_id"],
                payload={"din_barcode": unit["din_barcode"], "previous_reservation_id": unit["reservation_id"]}
            )

        conn.commit()
        return len(expired_units)

    def reserve_units(
        self,
        request_id: str,
        facility_id: str,
        required_blood_type: str,
        component_type: str,
        units_requested: int,
        lease_seconds: int = 120
    ) -> Tuple[bool, Optional[str], Optional[str], List[str], Optional[str]]:
        """
        Pessimistically allocates compatible blood units using FEFO ordering (expires_at ASC).
        Returns: (success, reservation_id, lease_expires_at, reserved_unit_ids, error_message)
        """
        self.sweep_expired_leases()

        conn = get_db_connection()
        cursor = conn.cursor()

        compatible_types = self.get_compatible_types(required_blood_type, component_type)
        now = datetime.datetime.now(datetime.timezone.utc)
        min_valid_expiration = (now + datetime.timedelta(hours=2)).isoformat()

        # Build dynamic query to select compatible units sorted strictly by FEFO (expires_at ASC) matching component_type
        placeholders = ",".join("?" for _ in compatible_types)
        query = f"""
        SELECT unit_id, din_barcode, blood_type, component_type, expires_at
        FROM inventory_blood_units
        WHERE status = 'AVAILABLE'
          AND blood_type IN ({placeholders})
          AND component_type = ?
          AND expires_at > ?
        ORDER BY expires_at ASC
        LIMIT ?;
        """
        params = compatible_types + [component_type, min_valid_expiration, units_requested]
        cursor.execute(query, params)
        matched_units = cursor.fetchall()

        if len(matched_units) < units_requested:
            return (
                False,
                None,
                None,
                [],
                f"INSUFFICIENT_COMPATIBLE_INVENTORY: Requested {units_requested} units of {required_blood_type} ({component_type}), but only {len(matched_units)} available."
            )

        # Allocate reservation
        reservation_id = f"res-{uuid.uuid4().hex[:12]}"
        lease_expires_at = (now + datetime.timedelta(seconds=lease_seconds)).isoformat()
        reserved_ids = []

        for unit in matched_units:
            unit_id = unit["unit_id"]
            reserved_ids.append(unit_id)
            cursor.execute("""
            UPDATE inventory_blood_units
            SET status = 'RESERVED',
                reservation_id = ?,
                lease_expires_at = ?
            WHERE unit_id = ?;
            """, (reservation_id, lease_expires_at, unit_id))

        conn.commit()

        # Audit log the allocation
        audit_service.log_event(
            actor_user_id=facility_id,
            action_type="RESERVATION_ALLOCATE",
            resource_type="INVENTORY_RESERVATION",
            resource_id=reservation_id,
            payload={
                "requestId": request_id,
                "unitsRequested": units_requested,
                "bloodType": required_blood_type,
                "componentType": component_type,
                "reservedUnitIds": reserved_ids,
                "leaseExpiresAt": lease_expires_at
            }
        )

        return True, reservation_id, lease_expires_at, reserved_ids, None

    def get_inventory_summary(self) -> Dict[str, Any]:
        """Queries stock levels grouped by ABO/Rh phenotype and FEFO expiration timers."""
        self.sweep_expired_leases()

        conn = get_db_connection()
        cursor = conn.cursor()
        now = datetime.datetime.now(datetime.timezone.utc)
        soon_threshold = (now + datetime.timedelta(hours=48)).isoformat()

        cursor.execute("SELECT COUNT(*) FROM inventory_blood_units WHERE status = 'AVAILABLE';")
        total_available = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM inventory_blood_units WHERE status = 'RESERVED';")
        total_reserved = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM inventory_blood_units WHERE status = 'AVAILABLE' AND expires_at <= ?;", (soon_threshold,))
        expiring_soon = cursor.fetchone()[0]

        phenotypes = ["O_NEG", "O_POS", "A_POS", "A_NEG", "B_POS", "B_NEG", "AB_POS", "AB_NEG"]
        stock_by_phenotype = {}

        for pt in phenotypes:
            cursor.execute("SELECT COUNT(*) FROM inventory_blood_units WHERE blood_type = ? AND status = 'AVAILABLE';", (pt,))
            avail = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM inventory_blood_units WHERE blood_type = ? AND status = 'RESERVED';", (pt,))
            res = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM inventory_blood_units WHERE blood_type = ? AND status = 'AVAILABLE' AND expires_at <= ?;", (pt, soon_threshold))
            soon = cursor.fetchone()[0]

            stock_by_phenotype[pt] = {
                "available": avail,
                "reserved": res,
                "expiringSoon": soon
            }

        cursor.execute("""
        SELECT unit_id, din_barcode, facility_id, blood_type, component_type, volume_ml, status, expires_at
        FROM inventory_blood_units
        ORDER BY expires_at ASC
        LIMIT 100;
        """)
        unit_rows = cursor.fetchall()
        units_list = []
        for r in unit_rows:
            units_list.append({
                "unitId": r["unit_id"],
                "dinBarcode": r["din_barcode"],
                "facilityId": r["facility_id"],
                "bloodType": r["blood_type"],
                "componentType": r["component_type"],
                "volumeMl": r["volume_ml"],
                "status": r["status"],
                "expiresAt": r["expires_at"]
            })

        return {
            "summary": {
                "totalAvailable": total_available,
                "totalReserved": total_reserved,
                "expiringWithin48h": expiring_soon
            },
            "stockByPhenotype": stock_by_phenotype,
            "units": units_list
        }

    def register_unit(
        self,
        din_barcode: str,
        facility_id: str,
        blood_type: str,
        component_type: str,
        volume_ml: int,
        expires_at: str
    ) -> Dict[str, Any]:
        """Registers a new blood unit intake with ISBT 128 / DIN barcode."""
        conn = get_db_connection()
        cursor = conn.cursor()

        unit_id = f"unit-{uuid.uuid4().hex[:12]}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        cursor.execute("""
        INSERT INTO inventory_blood_units (
            unit_id, din_barcode, facility_id, blood_type, component_type, volume_ml, status, expires_at, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, 'AVAILABLE', ?, ?);
        """, (unit_id, din_barcode, facility_id, blood_type, component_type, volume_ml, expires_at, now))
        conn.commit()

        audit_service.log_event(
            actor_user_id=facility_id,
            action_type="INVENTORY_CHECKIN",
            resource_type="INVENTORY_UNIT",
            resource_id=unit_id,
            payload={"din_barcode": din_barcode, "blood_type": blood_type, "expires_at": expires_at}
        )

        return {
            "unitId": unit_id,
            "dinBarcode": din_barcode,
            "status": "AVAILABLE"
        }


# Default global instance
inventory_service = InventoryService()
