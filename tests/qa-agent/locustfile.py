"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   performance
Source:  test_strategy/plans/cloned_repo__performance.json
Generated: 2024-07-12T13:45:00Z
"""

import os
import io
from locust import HttpUser, task, between, events

# --- Constants from environment or defaults ---
SERVICE_URL = os.environ.get("SERVICE_URL", "").strip()
P95_MS_THRESHOLD = float(os.environ.get("PERF_P95_MS_THRESHOLD", "500"))
FAIL_RATIO_THRESHOLD = float(os.environ.get("PERF_FAIL_RATIO_THRESHOLD", "0.01"))

class HospitalUser(HttpUser):
    """Simulates a hospital user who logs in and creates blood demands.

    test_id: cloned_repo__performance__001
    target: POST /hospital/create-demand
    requirement_id: REQ-N-006
    ac_ids: none
    """
    wait_time = between(5, 10)  # Based on plan: 'every 5-10 seconds'
    host = SERVICE_URL

    def on_start(self):
        """Logs in as a hospital user to establish a session."""
        self.client.post("/login/hospital", {
            "username": f"perf_user_{self.environment.runner.user_greenlet_id}",
            "password": "password"
        })

    @task
    def create_blood_demand(self):
        """Creates a new blood demand by submitting the form with a file."""
        file_content = b"This is a dummy compliance document for performance testing."
        file_obj = io.BytesIO(file_content)
        file_obj.name = "compliance_perf_test.pdf"

        self.client.post(
            "/hospital/create-demand",
            data={
                "blood_type": "O+",
                "units": "2",
                "notes": "Performance test demand"
            },
            files={"document": file_obj},
            name="/hospital/create-demand"  # Group stats under this name
        )

class AdminUser(HttpUser):
    """Simulates an admin user who logs in and verifies demands.

    test_id: cloned_repo__performance__002
    target: POST /admin/verify/<int:demand_id>
    requirement_id: REQ-F-017
    ac_ids: none
    """
    wait_time = between(1, 5)
    host = SERVICE_URL

    def on_start(self):
        """Logs in as an admin user to establish a session."""
        self.client.post("/login/admin", {
            "username": f"perf_admin_{self.environment.runner.user_greenlet_id}",
            "password": "password"
        })

    @task
    def verify_blood_demand(self):
        """Verifies a pending blood demand. The mock data has a pending demand with id=2."""
        self.client.post(
            "/admin/verify/2",
            data={"action": "approve"},
            name="/admin/verify/<int:demand_id>"  # Group stats under this name
        )

@events.test_stop.add_listener
def enforce_thresholds(environment, **kwargs):
    """
    Checks if performance thresholds were met and sets the exit code on failure.
    This allows the CI/CD pipeline to fail the test run based on performance.
    """
    if environment.stats.total.num_requests == 0:
        print("No requests made. Skipping threshold checks.")
        return

    stats = environment.stats.total
    fail_ratio = stats.fail_ratio
    p95_ms = stats.get_response_time_percentile(0.95)

    print(f"\n--- Performance Summary ---")
    print(f"Total Requests: {stats.num_requests}")
    print(f"Failure Ratio: {fail_ratio:.2%}")
    if p95_ms is not None:
        print(f"P95 Response Time: {p95_ms:.2f} ms")
    print("-------------------------\n")

    if fail_ratio > FAIL_RATIO_THRESHOLD:
        print(f"Test failed: Failure ratio {fail_ratio:.2%} exceeded threshold {FAIL_RATIO_THRESHOLD:.2%}")
        environment.process_exit_code = 1

    if p95_ms and p95_ms > P95_MS_THRESHOLD:
        print(f"Test failed: P95 response time {p95_ms:.2f}ms exceeded threshold {P95_MS_THRESHOLD:.2f}ms")
        environment.process_exit_code = 1

    if environment.process_exit_code == 0:
        print("Performance thresholds met successfully.")
