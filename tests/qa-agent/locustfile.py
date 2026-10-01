import os
from locust import HttpUser, task, between, events
import datetime

# --- Performance Thresholds ---
# SERVICE_URL will be provided by the test environment.
SERVICE_URL = os.environ.get("SERVICE_URL", "").strip()
# P95 latency threshold in milliseconds. Test 'cloned_repo__performance__001' requires sub-100ms.
P95_MS_THRESHOLD = float(os.environ.get("PERF_P95_MS_THRESHOLD", "100"))
# Maximum acceptable failure rate (e.g., 0.01 = 1% of requests).
FAIL_RATIO_THRESHOLD = float(os.environ.get("PERF_FAIL_RATIO_THRESHOLD", "0.01"))


class TargetUser(HttpUser):
    """
    Simulates a user interacting with the BDCN API endpoints.
    """
    host = SERVICE_URL
    # Wait time between tasks, simulating realistic user pacing.
    wait_time = between(0.5, 1.5)

    @task(3)
    def get_spatial_candidates(self):
        """
        Task for test_id: cloned_repo__performance__001
        Verifies P95 latency for geospatial queries.
        """
        self.client.get(
            "/v1/spatial/candidates?latitude=37.7749&longitude=-122.4194&radius_km=25&abo_type=O&rh_factor=NEGATIVE",
            name="/v1/spatial/candidates"
        )

    @task(1)
    def create_emergency_dispatch(self):
        """
        Task for test_id: cloned_repo__performance__002
        Measures the end-to-end cycle time for emergency dispatches.
        """
        payload = {
            "hospital_id": "hosp-perf-test",
            "severity": "LEVEL_1_CATASTROPHIC",
            "required_abo": "O",
            "required_rh": "NEGATIVE",
            "units_requested": 2,
            "initiated_by": "locust_perf_agent"
        }
        self.client.post("/v1/emergency/dispatch", json=payload, name="/v1/emergency/dispatch")

    def on_start(self):
        """on_start is called when a Locust start before any task is scheduled"""
        # In a real-world scenario, this could handle login to get a session token.
        pass


@events.test_stop.add_listener
def enforce_thresholds(environment, **kwargs):
    """
    This function is called when the test run stops. It checks the final stats
    against the defined performance thresholds and sets the process exit code
    to 1 (failure) if any threshold is breached.
    """
    stats = environment.stats.total
    fail_ratio = stats.fail_ratio
    p95_ms = stats.get_response_time_percentile(0.95)

    print(f"\n--- Performance Threshold Report ---")
    print(f"P95 Response Time: {p95_ms:.2f}ms (Threshold: {P95_MS_THRESHOLD}ms)")
    print(f"Failure Ratio: {fail_ratio:.4f} (Threshold: {FAIL_RATIO_THRESHOLD})")

    if fail_ratio > FAIL_RATIO_THRESHOLD:
        print(f"\n[FAILURE] Failure ratio ({fail_ratio:.4f}) exceeded threshold ({FAIL_RATIO_THRESHOLD}).")
        environment.process_exit_code = 1

    if p95_ms is not None and p95_ms >= P95_MS_THRESHOLD:
        print(f"\n[FAILURE] P95 response time ({p95_ms:.2f}ms) exceeded threshold ({P95_MS_THRESHOLD}ms).")
        environment.process_exit_code = 1

    if environment.process_exit_code == 0:
        print("\n[SUCCESS] All performance thresholds met.")
