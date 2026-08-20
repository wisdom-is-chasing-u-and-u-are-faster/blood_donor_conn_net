"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   performance
Source:  test_strategy/plans/cloned_repo__performance.json
Generated: 2024-07-25T15:01:23.123456Z
"""
import os
import io
from locust import HttpUser, events, task, between

# --- Performance Thresholds ---
# These values can be overridden by environment variables.
SERVICE_URL = os.environ.get("SERVICE_URL", "").strip()
P95_MS_THRESHOLD = float(os.environ.get("PERF_P95_MS_THRESHOLD", "500"))
FAIL_RATIO_THRESHOLD = float(os.environ.get("PERF_FAIL_RATIO_THRESHOLD", "0.01"))

class TargetUser(HttpUser):
    """Simulates a hospital user who logs in, views the dashboard, and creates demand requests."""
    host = SERVICE_URL
    wait_time = between(0.5, 1.5)

    def on_start(self):
        """Log in as a hospital user to establish a session for subsequent tasks."""
        if not self.host:
            print("SERVICE_URL environment variable not set. Skipping login.")
            return

        self.client.post("/login/hospital", {
            "username": f"perf_user_{self.environment.runner.user_greenlet_id}",
            "password": "password"
        }, name="/login/hospital")

    @task(1)
    def create_demand(self):
        """Task for test_id: cloned_repo__performance__001

        Submits a new blood demand request, which is the primary write operation to test.
        This includes a file upload to simulate a realistic payload.
        """
        # Create a dummy file in memory for the upload
        file_content = b"This is a fake compliance document for performance testing."
        dummy_file = ("compliance.pdf", file_content, "application/pdf")

        self.client.post(
            "/hospital/create-demand",
            data={
                "blood_type": "A+",
                "units": "2",
                "notes": "Performance test submission"
            },
            files={"document": dummy_file},
            name="/hospital/create-demand"
        )

    @task(3)
    def view_dashboard(self):
        """Simulates a user viewing their main dashboard, a common read operation."""
        self.client.get("/hospital/dashboard", name="/hospital/dashboard")

@events.test_stop.add_listener
def enforce_thresholds(environment, **kwargs):
    """Check final stats against performance thresholds and fail the run if they are not met."""
    stats = environment.stats.total
    fail_ratio = stats.fail_ratio
    p95_ms = stats.get_response_time_percentile(0.95)

    print(f"\n--- Performance Summary ---")
    print(f"Total requests: {stats.num_requests}")
    print(f"Failure ratio: {fail_ratio:.4f} (Threshold: {FAIL_RATIO_THRESHOLD:.4f})")
    if p95_ms is not None:
        print(f"P95 response time: {p95_ms:.2f} ms (Threshold: {P95_MS_THRESHOLD:.2f} ms)")
    else:
        print("P95 response time: N/A (not enough data)")
    print("-------------------------\n")

    if fail_ratio > FAIL_RATIO_THRESHOLD:
        print(f"FAIL: Failure ratio ({fail_ratio:.4f}) exceeded threshold ({FAIL_RATIO_THRESHOLD:.4f}).")
        environment.process_exit_code = 1

    if p95_ms and p95_ms >= P95_MS_THRESHOLD:
        print(f"FAIL: P95 response time ({p95_ms:.2f} ms) exceeded threshold ({P95_MS_THRESHOLD:.2f} ms).")
        environment.process_exit_code = 1

    if environment.process_exit_code == 0:
        print("PASS: All performance thresholds met.")
