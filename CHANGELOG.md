# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - ARCH-9061
- Mounted Variant-A self-contained HTML pages: `admin-dashboard.html`, `create-request.html`, `dashboard.html`, `login.html`, `profile.html`, and `request-feed.html` under `public/pages/`.
- Integrated full Variant-A showcase preview into `public/index.html` with responsive theme styling.
- Added client-side API helper in `public/js/api.js` wired with active event listeners for blood requisition submissions and admin verification approval/rejections.
- Scaffolded cross-platform mobile shells for iOS (`ios/BDCN/Info.plist`, `ios/BDCN/AppDelegate.swift`) and Android (`android/app/src/main/AndroidManifest.xml`, `android/app/src/main/java/com/bdcn/MainActivity.kt`).
- Added comprehensive unit tests in `tests/test_mobile_shells.py` and updated `tests/test_api_v1.py`.

## [1.0.0] - 2026-11-16
### Added - ARCH-7789
- Mounted 9 self-contained Variant-A UI pages under `/pages/` and `public/index.html`.
- Implemented RESTful API endpoints (`/health`, `/api/v1/auth/social`, `/api/v1/donors/hotspots`, `/api/v1/requests`, `/api/v1/admin/requests/<id>/verify`).
- Scaffolded 12-factor configuration (`.env.example`, `docker-compose.yml`, `db/schema.sql`, `db/seed.sql`, `db/init_db.py`).
