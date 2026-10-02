# Changelog

## [Unreleased]

### Added

- **feat(ARCH-2099): Blood Donor Connection Network (BDCN) Core Modular Monolith Platform**

  Comprehensive full-stack clinical healthcare dispatch and inventory management ecosystem delivering relational ACID guarantees and PostGIS spatial capabilities across 4 core user stories and 16 child tasks:

  - **Emergency Blood Dispatch (ARCH-2100 / ARCH-S1)**:
    - Code Red fast-path dispatch engine with sub-45 second processing and HTTP 201 Created SLA (`services/dispatch_service.py`, `ARCH-2105`).
    - DDL schema authoring for `dispatch.emergency_requests` table with UUID keys and state tracking (`db/schema.sql`, `ARCH-2108`).
    - Emergency Dispatch UI Console with Code Red Modal component and 120s countdown timers (`templates/dispatch_dashboard.html`, `static/js/dispatch.js`, `ARCH-2104`).
    - Multi-tier E2E automated test suite verifying Code Red fast path and 422 concurrency rejection (`tests/test_dispatch_e2e.py`, `ARCH-2106`).

  - **Hospital Blood Inventory & FEFO Engine (ARCH-2102 / ARCH-S2)**:
    - Real-time First-Expired-First-Out (FEFO) allocation algorithm with `SELECT FOR UPDATE` pessimistic row locking and 120s lease timeout (`services/inventory_service.py`, `ARCH-2115`).
    - Database schema for `inventory.blood_units` with partial index `idx_blood_units_fefo_lookup` on `(blood_type, component_type, expires_at ASC)` (`db/schema.sql`, `ARCH-2117`).
    - Regional blood inventory console with stock gauge cards and 42-day expiration timeline (`templates/inventory_management.html`, `static/js/inventory.js`, `ARCH-2116`).
    - Automated stress test suite verifying FEFO ordering and background lease sweeper (`tests/test_inventory_fefo.py`, `ARCH-2114`).

  - **Donor Geolocation Proximity & Mobile Push Broadcast (ARCH-2101 / ARCH-S3)**:
    - PostGIS spherical Haversine radial distance query on `GEOMETRY(Point, 4326)` with 56-day donation interval filter (`services/proximity_service.py`, `ARCH-2110`).
    - PostGIS GiST spatial indexing on `donor.donor_profiles.current_location` for sub-200ms query latency (`db/schema.sql`, `ARCH-2107`).
    - Dynamic geofence visualizer map with 15-mile radial buffer slider and broadcast dispatcher (`templates/donor_matching.html`, `static/js/donors.js`, `ARCH-2109`).
    - Multi-channel notification router delivering APNs/FCM push alerts with automatic 5s Twilio SMS fallback (`services/notification_service.py`, `tests/test_proximity_broadcast.py`, `ARCH-2111`).

  - **HIPAA ePHI Field Encryption & WORM Audit Ledger (ARCH-2103 / ARCH-S4)**:
    - AES-256-GCM field-level encryption with unique 96-bit IVs per record (`services/crypto_service.py`, `ARCH-2120`).
    - Immutable Write-Once-Read-Many (WORM) audit ledger `audit.hipaa_access_ledger` with SHA-256 cryptographic hash chaining (`services/audit_service.py`, `db/schema.sql`, `ARCH-2113`).
    - HIPAA compliance audit log viewer and cryptographic hash chain verification portal (`templates/audit_viewer.html`, `static/js/audit.js`, `ARCH-2121`).
    - Security and cryptographic verification test suite verifying zero plaintext leakage and WORM immutability (`tests/test_crypto_audit.py`, `ARCH-2112`).

  - **12-Factor Environment & Local Infrastructure**:
    - Root `.env.example`, `.gitignore`, and minimal `docker-compose.yml` for local PostgreSQL 16 + PostGIS and Redis dependencies.
    - Dual-engine compatibility in `db/init_db.py` supporting SQLite in-memory testing and PostgreSQL 16 production.

- **feat(ARCH-3357): UI Pages + Requirements: Blood Donor Connection Network (BDCN) Core Platform**
  - Initial front-end implementation with basic Flask routing and mock data structures.
