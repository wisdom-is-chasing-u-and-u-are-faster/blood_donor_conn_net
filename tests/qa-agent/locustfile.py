"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   performance
Source:  test_strategy/plans/cloned_repo__performance.json
Generated: 2024-07-12T13:01:21.051915Z
"""
import os
from locust import HttpUser, task, between, events

# --- Constants read from environment variables with defaults ---
SERVICE_URL = os.environ.get("SERVICE_URL", "").strip()
# Default P95 threshold set to the most lenient value from the plan.
P95_MS_THRESHOLD = float(os.environ.get("PERF_P95_MS_THRESHOLD", "1000"))
# Default failure ratio threshold set to the most lenient value from the plan.
FAIL_RATIO_THRESHOLD = float(os.environ.get("PERF_FAIL_RATIO_THRESHOLD", "0.01"))

class TargetUser(HttpUser):
    """Simulates a user interacting with the BDCN application."""
    host = SERVICE_URL
    wait_time = between(0.5, 1.5)

    def on_start(self):
        """Log in a user at the start of a session to enable authenticated tasks."""
        # This ensures that endpoints requiring a session cookie will work.
        self.client.post("/login", data={
            "username": "perf_user",
            "password": "password",
            "role": "donor"
        }, name="/login[session_setup]")

    @task(3)
    def task_login(self):
        """
        Load test the login endpoint.
        test_id: cloned_repo__performance__001
        """
        self.client.post("/login", data={
            "username": "test_donor_user",
            "password": "a_password",
            "role": "donor"
        }, name="/login")

    @task(2)
    def task_donor_dashboard(self):
        """
        Load test the donor dashboard.
        test_id: cloned_repo__performance__002
        """
        self.client.get("/donor/dashboard", name="/donor/dashboard")

    @task(1)
    def task_map_hotspots(self):
        """
        Load test the map hotspots endpoint.
        test_id: cloned_repo__performance__003
        """
        self.client.get("/map/hotspots", name="/map/hotspots")

    @task(1)
    def task_home(self):
        """Hits the home page as a baseline."""
        self.client.get("/", name="/")

@events.test_stop.add_listener
def enforce_thresholds(environment, **kwargs):
    """
    Check overall statistics against defined thresholds at the end of the test.
    If thresholds are exceeded, set the process exit code to 1 to fail the run.
    """
    stats = environment.stats.total
    fail_ratio = stats.fail_ratio
    p95_ms = stats.get_response_time_percentile(0.95)

    if fail_ratio > FAIL_RATIO_THRESHOLD:
        environment.process_exit_code = 1

    if p95_ms and p95_ms >= P95_MS_THRESHOLD:
        environment.process_exit_code = 1
