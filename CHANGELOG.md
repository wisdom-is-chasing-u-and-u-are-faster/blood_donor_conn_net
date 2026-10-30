# Changelog

## [Unreleased]

### Added

- **feat(ARCH-6455): User Authentication, OAuth2 Session Management & Role-Based Request Filtering**
  - Dedicated unified portal login screen at `/login` supporting username/password, role selection, and OAuth2 social login (Google, Apple, Facebook).
  - REST API authentication and OAuth2 session management endpoints (`/api/v1/auth/login`, `/api/v1/auth/oauth2`, `/health`).
  - Role-based blood request filtering API (`/api/v1/requests`) dynamically delivering compatible requests for Donors, own requisitions for Recipients, and complete supply chain demand ledgers for Hospital Administrators.
  - Dedicated Donor Dashboard (`/donor/dashboard`) displaying personalized blood group compatibility matching and responsive donation callout.
  - Dedicated Recipient Dashboard (`/recipient/dashboard`) enabling patient requisition tracking and fast submission.
  - Comprehensive Hospital Administrator Dashboard (`/admin/dashboard`, `/hospital/admin-dashboard`) with supply chain metrics and rapid verification controls.
  - 10 new pytest verification tests covering all acceptance criteria with 100% legacy backward compatibility.

### Added

- **feat(ARCH-3357): UI Pages + Requirements: Blood Donor Connection Network (BDCN) Core Platform**

  This change introduces the initial front-end implementation of the Blood Donor Connection Network (BDCN) Core Platform. The key deliverables of this PR are:

  - A Flask-based Python application (`app.py`) to handle routing, session management, and the core application logic.
  - A set of HTML templates using Bootstrap 5 for various user interfaces, including:
    - Hospital and administrator login portals.
    - A dashboard for hospital staff to view and manage blood demands.
    - A form for creating new blood demand requests.
    - An administrative queue for verifying and processing pending requests.
    - Pages for managing alerts and viewing audit logs.
  - The `requirements.txt` file, specifying the project's dependencies (Flask and pytest).
  - A suite of verification tests (`tests/test_app.py`) to ensure the basic functionality of the application.
