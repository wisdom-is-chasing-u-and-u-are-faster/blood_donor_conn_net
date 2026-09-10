"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   performance
Source:  test_strategy/plans/cloned_repo__performance.json
Generated: 2024-07-12T13:01:21.052934Z
"""
import os
from locust import HttpUser, events, task, between

# --- Performance Thresholds ---
# SERVICE_URL is provided by the test execution environment.
SERVICE_URL = os.environ.get("SERVICE_URL", "").strip()

# P95 latency threshold in milliseconds. Fails the test if the 95th percentile response time is higher.
# This value is based on the requirement in test_id cloned_repo__performance__001.
P95_MS_THRESHOLD = float(os.environ.get("PERF_P95_MS_THRESHOLD", "100"))

# Failure ratio threshold. Fails the test if the percentage of failed requests exceeds this.
FAIL_RATIO_THRESHOLD = float(os.environ.get("PERF_FAIL_RATIO_THRESHOLD", "0.01"))


class TargetUser(HttpUser):
    """
    Simulates a user interacting with the service's main endpoints.
    """
    host = SERVICE_URL
    wait_time = between(0.5, 1.5)  # Wait 0.5-1.5s between tasks

    @task(3)
    def get_spatial_candidates(self):
        """
        Load test the geospatial candidates endpoint.
        test_id: cloned_repo__performance__001
        target: GET /v1/spatial/candidates
        requirement_id: BO-5
        ac_ids: BO-5-AC-2
        """
        self.client.get(
            "/v1/spatial/candidates?latitude=37.7749&longitude=-122.4194&radius_km=15",
            name="/v1/spatial/candidates"
        )

    @task(1)
    def create_emergency_dispatch(self):
        """
        Load test the emergency dispatch creation endpoint.
        test_id: cloned_repo__performance__002
        target: POST /v1/emergency/dispatch
        requirement_id: BO-1
        ac_ids: BO-1-AC-1
        """
        payload = {
            "hospital_id": "hosp-perf-test",
            "severity": "LEVEL_1_CATASTROPHIC",
            "required_abo": "O",
            "required_rh": "NEGATIVE",
            "units_requested": 2
        }
        self.client.post("/v1/emergency/dispatch", json=payload, name="/v1/emergency/dispatch")


@events.test_stop.add_listener
def enforce_thresholds(environment, **kwargs):
    """
    This function is called when the Locust test run stops. It checks the final
    statistics against the predefined thresholds and sets the exit code to 1 (failure)
    if any threshold is breached.
    """
    stats = environment.stats.total
    fail_ratio = stats.fail_ratio
    p95_ms = stats.get_response_time_percentile(0.95)

    print(f"\n--- Performance Thresholds ---")
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
        print("INFO: P95 response time not available (no successful requests).")

    if environment.process_exit_code == 1:
        print("\n--- Test run failed ---")
    else:
        print("\n--- Test run passed ---")
