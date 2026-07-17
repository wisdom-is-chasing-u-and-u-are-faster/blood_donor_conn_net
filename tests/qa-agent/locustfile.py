"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   performance
Source:  test_strategy/plans/cloned_repo__performance.json
Generated: 2024-05-24T15:11:14.123456Z
"""
import os
from locust import HttpUser, events, task, between

# Performance thresholds from environment variables or defaults
SERVICE_URL = os.environ.get("SERVICE_URL", "http://127.0.0.1:5000").strip()
P95_MS_THRESHOLD = float(os.environ.get("PERF_P95_MS_THRESHOLD", "2000")) # Default to 2s for the slower admin queue endpoint
FAIL_RATIO_THRESHOLD = float(os.environ.get("PERF_FAIL_RATIO_THRESHOLD", "0.01")) # 1% failure rate

class HospitalUser(HttpUser):
    """
    User profile for a hospital staff member.
    Logs in and creates blood demand requests.
    Corresponds to test_id: cloned_repo__performance__001
    """
    host = SERVICE_URL
    wait_time = between(0.5, 2.5)

    def on_start(self):
        """Logs in as a hospital user at the start of the test."""
        self.client.post("/login/hospital", {
            "username": "perf-hospital-user",
            "password": "password"
        })

    @task
    def create_hospital_demand(self):
        """Submits a new blood demand request."""
        file_content = b"This is a dummy compliance document for performance testing."
        files = {
            "document": ("compliance.pdf", file_content, "application/pdf")
        }
        data = {
            "blood_type": "A+",
            "units": "3",
            "notes": "Performance test submission from Locust."
        }
        self.client.post(
            "/hospital/create-demand",
            data=data,
            files=files,
            name="/hospital/create-demand  [POST]"
        )

class AdminUser(HttpUser):
    """
    User profile for an administrator.
    Logs in and views the pending demand queue.
    Corresponds to test_id: cloned_repo__performance__002
    """
    host = SERVICE_URL
    wait_time = between(1.0, 3.0)

    def on_start(self):
        """Logs in as an admin user at the start of the test."""
        self.client.post("/login/admin", {
            "username": "perf-admin-user",
            "password": "password"
        })

    @task
    def view_admin_queue(self):
        """Fetches the admin verification queue page."""
        self.client.get("/admin/queue", name="/admin/queue [GET]")


@events.test_stop.add_listener
def enforce_thresholds(environment, **kwargs):
    """
    Checks final stats against performance thresholds.
    If thresholds are breached, sets a non-zero exit code to fail the test run.
    """
    stats = environment.stats.total
    fail_ratio = stats.fail_ratio
    p95_ms = stats.get_response_time_percentile(0.95)

    print(f"\n--- Performance Thresholds ---")
    print(f"P95 Response Time: {p95_ms:.2f}ms (Threshold: {P95_MS_THRESHOLD}ms)")
    print(f"Failure Ratio: {fail_ratio:.2%} (Threshold: {FAIL_RATIO_THRESHOLD:.2%})")

    if fail_ratio > FAIL_RATIO_THRESHOLD:
        print("\n*** Test failed: Failure ratio exceeded threshold.")
        environment.process_exit_code = 1

    if p95_ms and p95_ms > P95_MS_THRESHOLD:
        print("\n*** Test failed: P95 response time exceeded threshold.")
        environment.process_exit_code = 1

    if environment.process_exit_code == 0:
        print("\n--- Test passed: All thresholds met. ---")
