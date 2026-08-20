"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   performance
Source:  test_strategy/plans/cloned_repo__performance.json
Generated: 2024-05-23T11:00:00.000000Z
"""
import os
import io
from locust import HttpUser, events, task, between

# --- Performance Thresholds ---
# These values are configurable via environment variables.
# P95 response time threshold in milliseconds.
SERVICE_URL = os.environ.get("SERVICE_URL", "").strip()
P95_MS_THRESHOLD = float(os.environ.get("PERF_P95_MS_THRESHOLD", "1000"))
# Maximum acceptable failure ratio (e.g., 0.01 for 1%).
FAIL_RATIO_THRESHOLD = float(os.environ.get("PERF_FAIL_RATIO_THRESHOLD", "0.01"))

class TargetUser(HttpUser):
    """Simulates a user browsing the service."""
    host = SERVICE_URL
    wait_time = between(0.5, 1.5)

    def on_start(self):
        """Log in as an admin user to get a session cookie."""
        self.client.post("/login/admin", {"username": "perf_admin", "password": "password"})

    @task(1)
    def create_hospital_demand(self):
        """Simulates a hospital creating a blood demand.

        test_id: cloned_repo__performance__001
        """
        # This task requires a separate 'hospital' login. For simplicity in this
        # combined locust file, we will log in as a hospital user before this task.
        with self.client.post("/login/hospital", {"username": "perf_hospital", "password": "password"}, catch_response=True) as login_response:
            if login_response.status_code != 302:
                login_response.failure("Could not log in as hospital user")
                return

        # The form expects a file upload. We send a minimal in-memory file.
        file_data = io.BytesIO(b"dummy compliance document content")
        self.client.post(
            "/hospital/create-demand",
            data={
                "blood_type": "A+",
                "units": "2",
                "notes": "Performance test demand"
            },
            files={"document": ("compliance.pdf", file_data, "application/pdf")},
            name="/hospital/create-demand"
        )

    @task(1)
    def verify_demand(self):
        """Simulates an admin verifying a pending demand.

        test_id: cloned_repo__performance__002
        """
        # Assumes demand with ID 2 exists and is pending from mock data
        self.client.post("/admin/verify/2", data={"action": "approve"}, name="/admin/verify/[demand_id]")

    @task(3)
    def get_audit_log(self):
        """Simulates an admin retrieving the audit log.

        test_id: cloned_repo__performance__003
        """
        self.client.get("/admin/audit-log")

@events.test_stop.add_listener
def enforce_thresholds(environment, **kwargs):
    """Checks if performance thresholds were met and sets exit code.

    This hook runs at the end of the test and fails the run if the
    P95 response time or failure ratio exceeds the defined thresholds.
    """
    stats = environment.stats.total
    fail_ratio = stats.fail_ratio
    p95_ms = stats.get_response_time_percentile(0.95)

    print(f"\n--- Performance Thresholds ---")
    print(f"P95 Response Time: {p95_ms:.2f}ms (Threshold: {P95_MS_THRESHOLD}ms)")
    print(f"Failure Ratio: {fail_ratio:.2%} (Threshold: {FAIL_RATIO_THRESHOLD:.2%})")

    if fail_ratio > FAIL_RATIO_THRESHOLD:
        print("\n*** Test failed: Failure ratio exceeded threshold. ***")
        environment.process_exit_code = 1

    if p95_ms and p95_ms > P95_MS_THRESHOLD:
        print("\n*** Test failed: P95 response time exceeded threshold. ***")
        environment.process_exit_code = 1

    if environment.process_exit_code == 0:
        print("\n--- Performance thresholds met. ---")
