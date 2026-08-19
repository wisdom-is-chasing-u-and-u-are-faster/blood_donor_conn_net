import os
import io
import datetime
from locust import HttpUser, events, task, between

"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   performance
Source:  test_strategy/plans/cloned_repo__performance.json
Generated: 2024-05-29T12:00:00Z
"""

# --- Performance Thresholds ---
# These values are configurable via environment variables.
# The test will fail if the P95 response time is higher than this value (in ms).
P95_MS_THRESHOLD = float(os.environ.get("PERF_P95_MS_THRESHOLD", "500"))
# The test will fail if the failure ratio is higher than this value.
FAIL_RATIO_THRESHOLD = float(os.environ.get("PERF_FAIL_RATIO_THRESHOLD", "0.01"))
# --- Test Configuration ---
# The base URL for the service under test.
SERVICE_URL = os.environ.get("SERVICE_URL", "").strip()

class TargetUser(HttpUser):
    """
    Simulates user traffic against the main application endpoints.
    This user covers the following tests:
    - cloned_repo__performance__001: Load test hospital demand creation endpoint
    - cloned_repo__performance__002: Stress test audit log retrieval endpoint
    
    Assumes authentication is handled at the environment level (e.g., via headers)
    or is not required for the performance test environment.
    """
    host = SERVICE_URL
    wait_time = between(0.5, 2.5)

    def on_start(self):
        """Logs in both a hospital and admin user to ensure sessions are available for tasks."""
        # Since tasks require different roles, we perform both logins.
        # The session cookie from the last login will be used by default,
        # but this setup is primarily to avoid initial auth errors if the app
        # is stateful and requires any valid session to exist.
        self.client.post("/login/hospital", {"username": "perf_hospital", "password": "password"})
        self.client.post("/login/admin", {"username": "perf_admin", "password": "password"})

    @task(3)
    def create_hospital_demand(self):
        """
        Task for test_id: cloned_repo__performance__001
        Sends a POST request to create a hospital demand.
        """
        dummy_file = io.BytesIO(b"dummy compliance data for performance test")
        dummy_file.name = "compliance.pdf"
        with self.client.post(
            "/hospital/create-demand",
            files={"document": dummy_file},
            data={
                "blood_type": "O-",
                "units": "2",
                "notes": "Performance test load"
            },
            name="/hospital/create-demand",
            catch_response=True
        ) as response:
            if response.status_code >= 400:
                response.failure(f"Request failed with status {response.status_code}")

    @task(1)
    def get_audit_log(self):
        """
        Task for test_id: cloned_repo__performance__002
        Sends a GET request to retrieve the admin audit log.
        """
        with self.client.get("/admin/audit-log", name="/admin/audit-log", catch_response=True) as response:
            if response.status_code >= 400:
                response.failure(f"Request failed with status {response.status_code}")

@events.test_stop.add_listener
def enforce_thresholds(environment, **kwargs):
    """
    Event handler that checks performance thresholds when the test is stopped.
    If thresholds are exceeded, the Locust process will exit with a non-zero code,
    signaling a failure in CI/CD pipelines.
    """
    if environment.stats.total.num_requests == 0:
        print("No requests were made. Skipping threshold checks.")
        return

    stats = environment.stats.total
    fail_ratio = stats.fail_ratio
    p95_ms = stats.get_response_time_percentile(0.95)

    print("--- Performance Summary ---")
    print(f"Total requests: {stats.num_requests}")
    print(f"Failure ratio: {fail_ratio:.4f} (Threshold: {FAIL_RATIO_THRESHOLD})")
    if p95_ms is not None:
        print(f"P95 response time: {p95_ms:.2f} ms (Threshold: {P95_MS_THRESHOLD} ms)")
    else:
        print("P95 response time: N/A (not enough data)")
    print("---------------------------")

    # Check against thresholds
    if fail_ratio > FAIL_RATIO_THRESHOLD:
        print(f"FAIL: Failure ratio ({fail_ratio:.4f}) exceeded threshold ({FAIL_RATIO_THRESHOLD}).")
        environment.process_exit_code = 1

    if p95_ms is not None and p95_ms > P95_MS_THRESHOLD:
        print(f"FAIL: P95 response time ({p95_ms:.2f} ms) exceeded threshold ({P95_MS_THRESHOLD} ms).")
        environment.process_exit_code = 1

    if environment.process_exit_code == 0:
        print("PASS: All performance thresholds met.")
