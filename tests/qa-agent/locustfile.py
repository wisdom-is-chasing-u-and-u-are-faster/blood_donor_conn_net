"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   performance
Source:  test_strategy/plans/cloned_repo__performance.json
Generated: 2024-07-31T14:59:33Z
"""
import os
from locust import HttpUser, events, task, between

# --- Configuration ---
SERVICE_URL = os.environ.get("SERVICE_URL", "http://127.0.0.1:5000").strip()
P95_MS_THRESHOLD = float(os.environ.get("PERF_P95_MS_THRESHOLD", "500"))
FAIL_RATIO_THRESHOLD = 0.01

class TargetUser(HttpUser):
    """
    Simulates a hospital user performing key actions: logging in and creating demands.
    This user covers the high and medium priority performance tests from the plan.
    """
    host = SERVICE_URL
    wait_time = between(0.5, 1.5)

    @task(1)
    def login_hospital(self):
        """
        Task for hospital login. Addresses test_id: cloned_repo__performance__002.
        The session cookie is automatically handled by the client for subsequent tasks.
        """
        self.client.post(
            "/login/hospital",
            data={"username": "perf_user", "password": "password"},
            name="/login/hospital"
        )

    @task(3)
    def create_demand(self):
        """
        Task to create a new blood demand. Addresses test_id: cloned_repo__performance__001.
        This task depends on a prior successful login to have a valid session.
        """
        file_content = b"This is a dummy compliance document for performance testing."
        self.client.post(
            "/hospital/create-demand",
            data={"blood_type": "A+", "units": "3", "notes": "Performance test"},
            files={"document": ("compliance.pdf", file_content, "application/pdf")},
            name="/hospital/create-demand"
        )

    @task(2)
    def get_dashboard(self):
        """
        Task to get the hospital dashboard. A simple read operation.
        """
        self.client.get("/hospital/dashboard", name="/hospital/dashboard")


@events.test_stop.add_listener
def enforce_thresholds(environment, **kwargs):
    """
    Checks performance statistics against defined thresholds when the test stops.
    If thresholds are breached, the test run is marked as failed.
    """
    if not environment.stats.total.num_requests:
        return

    stats = environment.stats.total
    fail_ratio = stats.fail_ratio
    p95_ms = stats.get_response_time_percentile(0.95)

    if fail_ratio > FAIL_RATIO_THRESHOLD:
        environment.process_exit_code = 1

    if p95_ms and p95_ms > P95_MS_THRESHOLD:
        environment.process_exit_code = 1
