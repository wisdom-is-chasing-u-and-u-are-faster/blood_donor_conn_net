import os
from locust import HttpUser, task, between, events

# --- Performance Thresholds ---
# Service URL is read from the environment where the locust runner executes.
SERVICE_URL = os.environ.get("SERVICE_URL", "").strip()

# P95 latency threshold in milliseconds. The test will fail if the 95th percentile
# response time is higher than this value.
P95_MS_THRESHOLD = float(os.environ.get("PERF_P95_MS_THRESHOLD", "100"))

# Failure rate threshold. The test will fail if the percentage of failed requests
# exceeds this ratio (e.g., 0.01 is a 1% failure rate).
FAIL_RATIO_THRESHOLD = float(os.environ.get("PERF_FAIL_RATIO_THRESHOLD", "0.01"))


class ClonedRepoUser(HttpUser):
    """
    Simulates user behavior for the cloned_repo service.

    This Locust user class defines tasks that represent typical API interactions.
    The weights determine the frequency of each task.
    """
    host = SERVICE_URL
    wait_time = between(0.5, 1.5)  # Wait 0.5-1.5s between tasks

    @task(3)
    def get_spatial_candidates(self):
        """Simulates a high-frequency geospatial query for nearby candidates."""
        self.client.get(
            "/v1/spatial/candidates?latitude=37.7749&longitude=-122.4194&radius_km=15&abo_type=O&rh_factor=NEGATIVE",
            name="/v1/spatial/candidates"
        )

    @task(1)
    def create_emergency_dispatch(self):
        """Simulates creating a new emergency dispatch request."""
        payload = {
            "hospital_id": "hosp-perf-test",
            "severity": "LEVEL_1_CATASTROPHIC",
            "required_abo": "O",
            "required_rh": "NEGATIVE",
            "units_requested": 2
        }
        self.client.post("/v1/emergency/dispatch", json=payload, name="/v1/emergency/dispatch")

    @task(1)
    def get_home(self):
        """A baseline task to hit the root endpoint."""
        self.client.get("/", name="/")


@events.test_stop.add_listener
def enforce_thresholds(environment, **kwargs):
    """
    This function is called when the Locust test run stops. It checks the
    final statistics against the predefined performance thresholds.
    If any threshold is breached, it sets the process exit code to 1,
    causing the CI/CD pipeline to fail.
    """
    stats = environment.stats.total
    fail_ratio = stats.fail_ratio
    p95_ms = stats.get_response_time_percentile(0.95)

    print(f"\n--- Performance Threshold Check ---")
    print(f"95th percentile response time: {p95_ms:.2f}ms (Threshold: {P95_MS_THRESHOLD}ms)")
    print(f"Failure ratio: {fail_ratio:.4f} (Threshold: {FAIL_RATIO_THRESHOLD})")

    if fail_ratio > FAIL_RATIO_THRESHOLD:
        print(f"\n[FAILED] Failure ratio ({fail_ratio:.4f}) exceeded threshold ({FAIL_RATIO_THRESHOLD}).")
        environment.process_exit_code = 1

    if p95_ms and p95_ms > P95_MS_THRESHOLD:
        print(f"\n[FAILED] P95 response time ({p95_ms:.2f}ms) exceeded threshold ({P95_MS_THRESHOLD}ms).")
        environment.process_exit_code = 1

    if environment.process_exit_code == 0:
        print(f"\n[PASSED] All performance thresholds met.")
