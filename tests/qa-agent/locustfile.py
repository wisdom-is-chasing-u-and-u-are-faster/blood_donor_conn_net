"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   performance
Source:  test_strategy/plans/cloned_repo__performance.json
Generated: 2024-07-31T13:01:27.531303Z
"""
import os
from locust import HttpUser, events, task, between

SERVICE_URL = os.environ.get("SERVICE_URL", "").strip()
P95_MS_THRESHOLD = float(os.environ.get("PERF_P95_MS_THRESHOLD", "500"))
FAIL_RATIO_THRESHOLD = 0.01

class TargetUser(HttpUser):
    host = SERVICE_URL
    wait_time = between(0.5, 1.5)

    @task(1)
    def post_emergency_dispatch(self):
        """Measures emergency dispatch notification cycle time.

        test_id: cloned_repo__performance__001
        target: POST /v1/emergency/dispatch
        requirement_id: BO-1
        ac_ids: BO-1-AC-1
        """
        payload = {
            "hospital_id": "hosp-1",
            "severity": "LEVEL_1_CATASTROPHIC",
            "required_abo": "O",
            "required_rh": "NEGATIVE",
            "units_requested": 4
        }
        self.client.post(
            "/v1/emergency/dispatch",
            json=payload,
            name="/v1/emergency/dispatch"
        )

    @task(3)
    def get_spatial_candidates(self):
        """Measures P95 latency for geospatial queries.

        test_id: cloned_repo__performance__002
        target: GET /v1/spatial/candidates
        requirement_id: BO-5
        ac_ids: BO-5-AC-2
        """
        params = {
            "latitude": 37.7749,
            "longitude": -122.4194,
            "radius_km": 15.0
        }
        self.client.get(
            "/v1/spatial/candidates",
            params=params,
            name="/v1/spatial/candidates"
        )

@events.test_stop.add_listener
def enforce_thresholds(environment, **kwargs):
    stats = environment.stats.total
    fail_ratio = stats.fail_ratio
    p95_ms = stats.get_response_time_percentile(0.95)
    if fail_ratio > FAIL_RATIO_THRESHOLD:
        environment.process_exit_code = 1
    if p95_ms and p95_ms >= P95_MS_THRESHOLD:
        environment.process_exit_code = 1
