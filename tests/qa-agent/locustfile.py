"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   performance
Source:  test_strategy/plans/cloned_repo__performance.json
Generated: 2024-05-21T17:34:01.123456Z
"""
import os
import io
from locust import HttpUser, task, between, events

# --- Test Parameters ---
# These can be overridden by environment variables.
SERVICE_URL = os.environ.get("SERVICE_URL", "").strip()
P95_MS_THRESHOLD = float(os.environ.get("PERF_P95_MS_THRESHOLD", "500"))
FAIL_RATIO_THRESHOLD = float(os.environ.get("PERF_FAIL_RATIO_THRESHOLD", "0.01"))

class TargetUser(HttpUser):
    """User that logs in and interacts with the hospital portal."""
    host = SERVICE_URL
    wait_time = between(0.5, 2.5)

    def on_start(self):
        """Logs in as a hospital user to establish a session."""
        # The app uses a simple auth check, so any non-empty user/pass works.
        self.client.post("/login/hospital", {
            "username": f"perf-user-{self.environment.runner.user_greenlet_id}",
            "password": "password"
        }, name="/login/hospital")

    @task(5)
    def create_hospital_demand(self):
        """
        test_id: cloned_repo__performance__001
        target: POST /hospital/create-demand
        requirement_id: REQ-N-006
        ac_ids: REQ-N-006-AC-1
        """
        # Create a dummy file in memory for the upload
        dummy_file = io.BytesIO(b"This is a dummy compliance document for performance testing.")
        
        # The endpoint expects a multipart/form-data payload with a file.
        self.client.post(
            "/hospital/create-demand",
            files={"document": ("compliance.pdf", dummy_file, "application/pdf")},
            data={
                "blood_type": "A+",
                "units": "3",
                "notes": "Automated performance test submission."
            },
            name="/hospital/create-demand"
        )

    @task(2)
    def view_dashboard(self):
        """Simulates a user viewing their dashboard."""
        self.client.get("/hospital/dashboard", name="/hospital/dashboard")

    @task(1)
    def view_home_redirect(self):
        """Accesses the root, which should redirect."""
        self.client.get("/", name="/")

@events.test_stop.add_listener
def enforce_thresholds(environment, **kwargs):
    """Checks if performance thresholds were met and fails the run if not."""
    stats = environment.stats.total
    fail_ratio = stats.fail_ratio
    p95_ms = stats.get_response_time_percentile(0.95)

    print(f"\n--- Performance Summary ---")
    print(f"Total requests: {stats.num_requests}")
    print(f"Failure ratio: {fail_ratio:.4f} (Threshold: {FAIL_RATIO_THRESHOLD})")
    if p95_ms is not None:
        print(f"P95 response time: {p95_ms:.2f} ms (Threshold: {P95_MS_THRESHOLD} ms)")
    else:
        print("P95 response time: N/A (not enough requests)")
    print("-------------------------\n")

    if fail_ratio > FAIL_RATIO_THRESHOLD:
        print(f"FAIL: Failure ratio ({fail_ratio:.4f}) exceeded threshold ({FAIL_RATIO_THRESHOLD}).")
        environment.process_exit_code = 1

    if p95_ms and p95_ms > P95_MS_THRESHOLD:
        print(f"FAIL: P95 response time ({p95_ms:.2f} ms) exceeded threshold ({P95_MS_THRESHOLD} ms).")
        environment.process_exit_code = 1

    if environment.process_exit_code == 0:
        print("PASS: All performance thresholds met.")
