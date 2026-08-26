"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   performance
Source:  test_strategy/plans/cloned_repo__performance.json
Generated: 2024-05-22T19:27:01.341143Z
"""
import os
import io
import time
import random
from locust import HttpUser, events, task, between

# --- Performance Thresholds ---
# These values are configurable via environment variables.
# The test will fail if the P95 response time is higher than this value (in milliseconds).
P95_MS_THRESHOLD = float(os.environ.get("PERF_P95_MS_THRESHOLD", "500"))
# The test will fail if the failure ratio is higher than this value (e.g., 0.01 for 1%).
FAIL_RATIO_THRESHOLD = float(os.environ.get("PERF_FAIL_RATIO_THRESHOLD", "0.01"))

# The base URL for the service under test. This is required.
SERVICE_URL = os.environ.get("SERVICE_URL", "").strip()
if not SERVICE_URL:
    print("Error: SERVICE_URL environment variable not set.")
    exit(1)

class TargetUser(HttpUser):
    """
    Simulates a hospital user who logs in, creates blood demands, and views the dashboard.
    This user profile is designed to load test the high-priority hospital-facing endpoints.
    """
    host = SERVICE_URL
    wait_time = between(0.5, 1.5)  # Wait 0.5-1.5s between tasks

    BLOOD_TYPES = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

    def on_start(self):
        """Called when a virtual user is started. Performs login."""
        self.client.post("/login/hospital", data={
            "username": f"user_{self.environment.runner.user_greenlet_id}",
            "password": "password"
        })

    @task(3) # This task will be executed 3 times more often than view_dashboard
    def create_blood_demand(self):
        """
        Simulates a hospital creating a new blood demand.
        test_id: cloned_repo__performance__001
        target: POST /hospital/create-demand
        requirement_id: REQ-N-006
        ac_ids: none
        """
        blood_type = random.choice(self.BLOOD_TYPES)
        units = random.randint(1, 5)
        
        # Create a dummy file in memory for the upload
        file_content = b"dummy file content for compliance document"
        dummy_file = io.BytesIO(file_content)
        
        self.client.post(
            "/hospital/create-demand",
            data={
                "blood_type": blood_type,
                "units": units,
                "notes": "Performance test submission"
            },
            files={
                "document": ("compliance.pdf", dummy_file, "application/pdf")
            },
            name="/hospital/create-demand" # Group stats for this endpoint
        )

    @task(1)
    def view_dashboard(self):
        """
        Simulates a hospital user viewing their main dashboard.
        This provides a baseline read-only load on the system.
        """
        self.client.get("/hospital/dashboard", name="/hospital/dashboard")

# --- Threshold Enforcement ---
@events.test_stop.add_listener
def enforce_thresholds(environment, **kwargs):
    """
    This function is called when the test run stops. It checks the final stats
    against the defined thresholds and sets the process exit code to 1 (failure)
    if any threshold is breached.
    """
    stats = environment.stats.total
    fail_ratio = stats.fail_ratio
    p95_ms = stats.get_response_time_percentile(0.95)

    print(f"\n--- Performance Thresholds Check ---")
    print(f"P95 Response Time: {p95_ms:.2f}ms (Threshold: {P95_MS_THRESHOLD}ms)")
    print(f"Failure Ratio: {fail_ratio:.2%} (Threshold: {FAIL_RATIO_THRESHOLD:.2%})")

    if fail_ratio > FAIL_RATIO_THRESHOLD:
        print("\n*** Test failed: Failure ratio exceeded threshold. ***")
        environment.process_exit_code = 1

    if p95_ms is not None and p95_ms > P95_MS_THRESHOLD:
        print("\n*** Test failed: P95 response time exceeded threshold. ***")
        environment.process_exit_code = 1

    if environment.process_exit_code == 0:
        print("\n--- Test passed: All performance thresholds met. ---")
