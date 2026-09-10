"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   performance
Source:  test_strategy/plans/cloned_repo__performance.json
Generated: 2024-07-25T13:01:42.589115Z
"""
import os
import random
from locust import HttpUser, events, task, between

# --- Performance Thresholds ---
# These values are configurable via environment variables.
# The P95 threshold for response time in milliseconds.
P95_MS_THRESHOLD = float(os.environ.get("PERF_P95_MS_THRESHOLD", "500"))
# The maximum acceptable failure ratio (e.g., 0.01 for 1%).
FAIL_RATIO_THRESHOLD = float(os.environ.get("PERF_FAIL_RATIO_THRESHOLD", "0.01"))
# The target service URL.
SERVICE_URL = os.environ.get("SERVICE_URL", "").strip()

if not SERVICE_URL:
    print("ERROR: SERVICE_URL environment variable not set. Locust will not run.")
    # Exiting here would be ideal, but Locust loads the file first.
    # The HttpUser will fail without a host.

class TargetUser(HttpUser):
    """
    Simulates a user interacting with the BDCN service.
    This user will perform actions related to emergency dispatch and spatial queries.
    """
    host = SERVICE_URL
    wait_time = between(0.5, 1.5)  # Wait 0.5-1.5s between tasks

    @task(1)
    def create_emergency_dispatch(self):
        """Simulates creating an emergency dispatch request.

        test_id: cloned_repo__performance__001
        target: POST /v1/emergency/dispatch
        requirement_id: REQ-001
        ac_ids: REQ-001-AC-1
        """
        payload = {
            "hospital_id": "hosp-perf-test",
            "severity": "LEVEL_1_CATASTROPHIC",
            "required_abo": random.choice(["A", "B", "O", "AB"]),
            "required_rh": random.choice(["POSITIVE", "NEGATIVE"]),
            "units_requested": random.randint(1, 5)
        }
        self.client.post(
            "/v1/emergency/dispatch",
            json=payload,
            name="/v1/emergency/dispatch"  # Group stats under this name
        )

    @task(3)
    def find_spatial_candidates(self):
        """Simulates searching for nearby donors using geospatial queries.

        test_id: cloned_repo__performance__002
        target: GET /v1/spatial/candidates
        requirement_id: REQ-002
        ac_ids: REQ-002-AC-2
        """
        # Use coordinates around San Francisco
        lat = 37.7749 + random.uniform(-0.1, 0.1)
        lon = -122.4194 + random.uniform(-0.1, 0.1)
        radius_km = random.uniform(5.0, 25.0)

        self.client.get(
            f"/v1/spatial/candidates?latitude={lat}&longitude={lon}&radius_km={radius_km}",
            name="/v1/spatial/candidates"  # Group stats under this name
        )

    @task(2)
    def get_home(self):
        """A simple baseline task to hit the homepage."""
        self.client.get("/")


@events.test_stop.add_listener
def enforce_thresholds(environment, **kwargs):
    """
    This function is called when the Locust test run stops. It checks if the
    performance thresholds for failure ratio and P95 response time were met.
    If not, it sets the process exit code to 1, causing the CI/CD pipeline to fail.
    """
    stats = environment.stats.total
    fail_ratio = stats.fail_ratio
    p95_ms = stats.get_response_time_percentile(0.95)

    print("--- Performance Threshold Check ---")
    print(f"Total requests: {stats.num_requests}")
    print(f"Total failures: {stats.num_failures}")

    # Check Fail Ratio
    if fail_ratio > FAIL_RATIO_THRESHOLD:
        print(f"FAIL: Failure ratio ({fail_ratio:.2%}) exceeded threshold ({FAIL_RATIO_THRESHOLD:.2%})")
        environment.process_exit_code = 1
    else:
        print(f"PASS: Failure ratio ({fail_ratio:.2%}) is within threshold ({FAIL_RATIO_THRESHOLD:.2%})")

    # Check P95 Response Time
    if p95_ms is not None:
        print(f"P95 response time: {p95_ms:.2f} ms")
        if p95_ms > P95_MS_THRESHOLD:
            print(f"FAIL: P95 response time ({p95_ms:.2f} ms) exceeded threshold ({P95_MS_THRESHOLD} ms)")
            environment.process_exit_code = 1
        else:
            print(f"PASS: P95 response time ({p95_ms:.2f} ms) is within threshold ({P95_MS_THRESHOLD} ms)")
    else:
        print("WARN: P95 response time could not be calculated (no successful requests).")
        if stats.num_requests > 0:
            environment.process_exit_code = 1

    print("---------------------------------")
