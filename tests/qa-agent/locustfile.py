import os
import random
from locust import HttpUser, events, task, between
from io import BytesIO

SERVICE_URL = os.environ.get("SERVICE_URL", "").strip()
P95_MS_THRESHOLD = float(os.environ.get("PERF_P95_MS_THRESHOLD", "500"))
FAIL_RATIO_THRESHOLD = 0.01

class TargetUser(HttpUser):
    """
    User persona for a hospital staff member who creates blood demands.
    This covers the primary write path for the application under test.
    """
    host = SERVICE_URL
    wait_time = between(1, 3)

    def on_start(self):
        """
        Called when a Locust user starts. This user logs in as a hospital staff member
        to establish a session for subsequent authenticated requests.
        """
        self.client.post("/login/hospital", {
            "username": f"perf_user_{random.randint(1, 10000)}",
            "password": "password"
        })

    @task(3)
    def create_blood_demand(self):
        """
        Simulates creating a new blood demand request, which is the main write action.
        This task corresponds to test_id: cloned_repo__performance__001
        """
        dummy_file = BytesIO(b"mock compliance document content for performance test")
        self.client.post(
            "/hospital/create-demand",
            data={
                "blood_type": random.choice(["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]),
                "units": random.randint(1, 10),
                "notes": "Performance test submission"
            },
            files={"document": ("compliance.pdf", dummy_file, "application/pdf")}
        )

    @task(1)
    def view_dashboard(self):
        """
        Simulates viewing the hospital dashboard, a common read operation.
        """
        self.client.get("/hospital/dashboard")

    # The admin task (cloned_repo__performance__002) is not included here because
    # it requires a different user role ('admin'). A separate Locust user class
    # would be needed to model that persona correctly without generating auth errors.
    # This file focuses on the 'hospital' user journey.

@events.test_stop.add_listener
def enforce_thresholds(environment, **kwargs):
    """
    Checks performance statistics against defined thresholds when the test stops.
    If thresholds are breached, the test run is marked as failed by setting a non-zero exit code.
    """
    stats = environment.stats.total
    fail_ratio = stats.fail_ratio
    p95_ms = stats.get_response_time_percentile(0.95)

    if fail_ratio > FAIL_RATIO_THRESHOLD:
        environment.process_exit_code = 1

    if p95_ms and p95_ms >= P95_MS_THRESHOLD:
        environment.process_exit_code = 1
