"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   performance
Source:  test_strategy/plans/cloned_repo__performance.json
Generated: 2024-05-23T10:36:07.512141Z
"""
import os
import io
from locust import HttpUser, events, task, between

# --- Performance Thresholds ---
# These values are configurable via environment variables.
# The P95 response time threshold in milliseconds.
SERVICE_URL = os.environ.get("SERVICE_URL", "http://127.0.0.1:5000").strip()
P95_MS_THRESHOLD = float(os.environ.get("PERF_P95_MS_THRESHOLD", "500"))
# The maximum acceptable failure ratio (e.g., 0.01 for 1%).
FAIL_RATIO_THRESHOLD = float(os.environ.get("PERF_FAIL_RATIO_THRESHOLD", "0.01"))

class TargetUser(HttpUser):
    """Represents a virtual user targeting the service."""
    host = SERVICE_URL
    wait_time = between(0.5, 1.5)

    def on_start(self):
        """Log in as a hospital user to establish a session for subsequent tasks."""
        self.client.post("/login/hospital", {
            "username": "hospital_user",
            "password": "password"
        })

    @task(3)
    def create_blood_demand(self):
        """Load test POST /hospital/create-demand for high ingestion throughput.

        test_id: cloned_repo__performance__001
        target: POST /hospital/create-demand
        requirement_id: REQ-N-006
        ac_ids: REQ-N-006-AC-1
        """
        # Use io.BytesIO to create a file in memory, avoiding filesystem I/O.
        file_content = io.BytesIO(b"This is a dummy compliance document for performance testing.")
        
        self.client.post(
            "/hospital/create-demand",
            data={
                "blood_type": "A+",
                "units": "3",
                "notes": "Performance test submission"
            },
            files={
                "document": ("compliance.pdf", file_content, "application/pdf")
            },
            name="/hospital/create-demand"  # Group stats under a clean name
        )

    @task(1)
    def view_dashboard(self):
        """Simulates a logged-in user viewing the hospital dashboard."""
        self.client.get("/hospital/dashboard", name="/hospital/dashboard")

@events.test_stop.add_listener
def enforce_thresholds(environment, **kwargs):
    """Check performance statistics against defined thresholds after the test run."""
    stats = environment.stats.total
    fail_ratio = stats.fail_ratio
    p95_ms = stats.get_response_time_percentile(0.95)

    print(f"\n--- Performance Summary ---")
    print(f"Total requests: {stats.num_requests}")
    print(f"Total failures: {stats.num_failures} ({fail_ratio:.2%})")
    if p95_ms is not None:
        print(f"P95 response time: {p95_ms:.2f} ms")
    else:
        print("P95 response time: N/A (not enough data)")
    print(f"-------------------------")

    exit_code = 0
    if fail_ratio > FAIL_RATIO_THRESHOLD:
        print(f"[FAIL] Failure ratio ({fail_ratio:.2%}) exceeded threshold ({FAIL_RATIO_THRESHOLD:.2%}).")
        exit_code = 1
    
    if p95_ms is not None and p95_ms >= P95_MS_THRESHOLD:
        print(f"[FAIL] P95 response time ({p95_ms:.2f} ms) exceeded threshold ({P95_MS_THRESHOLD:.2f} ms).")
        exit_code = 1

    if exit_code == 0:
        print("\n[PASS] All performance thresholds met.")
    else:
        print("\n[FAIL] One or more performance thresholds were not met.")

    environment.process_exit_code = exit_code
