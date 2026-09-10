"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   performance
Source:  test_strategy/plans/cloned_repo__performance.json
Generated: 2024-07-12T12:00:00Z
"""
import os
import random
from locust import HttpUser, task, between, events

# --- Performance Thresholds ---
# These values can be overridden by environment variables.
# P95 latency threshold in milliseconds.
# The test will fail if the 95th percentile response time exceeds this value.
P95_MS_THRESHOLD = float(os.environ.get("PERF_P95_MS_THRESHOLD", "500"))

# Failure rate threshold as a ratio (0.0 to 1.0).
# The test will fail if the ratio of failed requests to total requests exceeds this value.
FAIL_RATIO_THRESHOLD = float(os.environ.get("PERF_FAIL_RATIO_THRESHOLD", "0.01"))

# --- Test Configuration ---
# The base URL of the service under test.
# This is expected to be set in the environment by the test runner.
SERVICE_URL = os.environ.get("SERVICE_URL", "").strip()

class TargetUser(HttpUser):
    """Defines the behavior of a simulated user for the performance test."""
    host = SERVICE_URL
    # Wait time between tasks for each user, in seconds.
    wait_time = between(0.5, 2.5)

    @task(3)
    def get_spatial_candidates(self):
        """Simulates a user searching for spatial candidates."""
        # Test ID: cloned_repo__performance__001
        # Target: GET /v1/spatial/candidates
        lat = random.uniform(37.70, 37.80)
        lon = random.uniform(-122.40, -122.50)
        radius = random.uniform(5, 25)
        self.client.get(
            "/v1/spatial/candidates",
            params={"latitude": lat, "longitude": lon, "radius_km": radius},
            name="/v1/spatial/candidates"
        )

    @task(1)
    def create_emergency_dispatch(self):
        """Simulates a user creating an emergency dispatch request."""
        # Test ID: cloned_repo__performance__002
        # Target: POST /v1/emergency/dispatch
        payload = {
            "hospital_id": "hosp-perf-test",
            "severity": "LEVEL_1_CATASTROPHIC",
            "required_abo": random.choice(["O", "A", "B", "AB"]),
            "required_rh": random.choice(["POSITIVE", "NEGATIVE"]),
            "units_requested": random.randint(1, 5)
        }
        self.client.post(
            "/v1/emergency/dispatch",
            json=payload,
            name="/v1/emergency/dispatch"
        )

    def on_start(self):
        """Called when a user starts, checks if the host is set."""
        if not self.host:
            print("ERROR: SERVICE_URL environment variable not set. Aborting.")
            self.environment.runner.quit()

@events.test_stop.add_listener
def enforce_thresholds(environment, **kwargs):
    """
    Checks the final stats against the defined performance thresholds.
    If thresholds are breached, the Locust process will exit with a non-zero code,
    signaling a test failure to the CI/CD pipeline.
    """
    stats = environment.stats.total
    fail_ratio = stats.fail_ratio
    p95_ms = stats.get_response_time_percentile(0.95)

    print(f"\n--- Performance Threshold Check ---")
    print(f"Total requests: {stats.num_requests}")
    print(f"Total failures: {stats.num_failures}")
    
    # Check failure ratio
    if fail_ratio > FAIL_RATIO_THRESHOLD:
        print(f"FAIL: Failure ratio ({fail_ratio:.2%}) exceeded threshold ({FAIL_RATIO_THRESHOLD:.2%})")
        environment.process_exit_code = 1
    else:
        print(f"PASS: Failure ratio ({fail_ratio:.2%}) is within threshold ({FAIL_RATIO_THRESHOLD:.2%})")

    # Check P95 response time
    if p95_ms is not None:
        if p95_ms > P95_MS_THRESHOLD:
            print(f"FAIL: P95 response time ({p95_ms:.2f} ms) exceeded threshold ({P95_MS_THRESHOLD:.2f} ms)")
            environment.process_exit_code = 1
        else:
            print(f"PASS: P95 response time ({p95_ms:.2f} ms) is within threshold ({P95_MS_THRESHOLD:.2f} ms)")
    else:
        print("WARN: P95 response time could not be calculated (no successful requests?).")

    if environment.process_exit_code == 1:
        print("\nOverall result: TEST FAILED")
    else:
        print("\nOverall result: TEST PASSED")
