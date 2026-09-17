"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   performance
Source:  test_strategy/plans/cloned_repo__performance.json
Generated: 2024-07-12T17:01:23.123456Z
"""
import os
import io
from locust import HttpUser, task, between, events

# --- Performance Test Configuration ---
# These values are configurable via environment variables.
SERVICE_URL = os.environ.get("SERVICE_URL", "").strip()
P95_MS_THRESHOLD = float(os.environ.get("PERF_P95_MS_THRESHOLD", "500"))
FAIL_RATIO_THRESHOLD = 0.01

class TargetUser(HttpUser):
    """Simulates a hospital user creating blood demands."""
    host = SERVICE_URL
    wait_time = between(0.5, 1.5)

    def on_start(self):
        """Log in as a hospital user to establish a session."""
        self.client.post("/login/hospital", {
            "username": "performance_user",
            "password": "password"
        })

    @task(3)
    def create_blood_demand(self):
        """
        test_id: cloned_repo__performance__001
        target: POST /hospital/create-demand
        requirement_id: REQ-F-001,REQ-F-007
        ac_ids: REQ-F-001-AC-1,REQ-F-007-AC-1
        """
        # Create an in-memory file for the upload
        file_content = b'This is a dummy compliance document for performance testing.'
        file_obj = io.BytesIO(file_content)
        file_obj.name = 'compliance.pdf'

        self.client.post(
            "/hospital/create-demand",
            data={
                "blood_type": "A+",
                "units": "2",
                "notes": "Performance test submission"
            },
            files={
                "document": file_obj
            },
            name="/hospital/create-demand"
        )

    @task(1)
    def view_dashboard(self):
        """Simulates a user viewing their main dashboard."""
        self.client.get("/hospital/dashboard", name="/hospital/dashboard")

@events.test_stop.add_listener
def enforce_thresholds(environment, **kwargs):
    """Check performance statistics against defined thresholds after the test run."""
    stats = environment.stats.total
    fail_ratio = stats.fail_ratio
    p95_ms = stats.get_response_time_percentile(0.95)

    print(f"\n--- Performance Thresholds ---")
    print(f"P95 Response Time: {p95_ms:.2f}ms (Threshold: < {P95_MS_THRESHOLD}ms)")
    print(f"Failure Ratio: {fail_ratio:.2%} (Threshold: < {FAIL_RATIO_THRESHOLD:.2%})")

    if fail_ratio > FAIL_RATIO_THRESHOLD:
        print("\n*** TEST FAILED: Failure ratio exceeded threshold. ***")
        environment.process_exit_code = 1

    if p95_ms and p95_ms >= P95_MS_THRESHOLD:
        print("\n*** TEST FAILED: P95 response time exceeded threshold. ***")
        environment.process_exit_code = 1

    if environment.process_exit_code == 0:
        print("\n--- TEST PASSED: All performance thresholds met. ---")
