"""Generated performance tests for cloned_repo."""
import os
from locust import HttpUser, task, between, events

_DEFAULT_HOST = os.environ.get("SERVICE_URL", "").strip() or "http://localhost:8000"


class ClonedRepoLoadUser(HttpUser):
    """
    test_id: cloned_repo__performance__001
    target: GET /v1/spatial/candidates
    requirement_id: NFR-PERF-01
    ac_ids: NFR-PERF-01-AC-1
    """
    wait_time = between(1, 3)
    host = _DEFAULT_HOST

    @task(3)
    def get_spatial_candidates(self):
        """
        test_id: cloned_repo__performance__001
        target: GET /v1/spatial/candidates
        requirement_id: NFR-PERF-01
        ac_ids: NFR-PERF-01-AC-1
        """
        with self.client.get(
            "/v1/spatial/candidates?latitude=37.7749&longitude=-122.4194&radius_km=15.0&abo_type=O&rh_factor=NEGATIVE",
            name="GET /v1/spatial/candidates",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()

    @task(1)
    def post_emergency_dispatch(self):
        """
        test_id: cloned_repo__performance__002
        target: POST /v1/emergency/dispatch
        requirement_id: BO-1, BR-003
        ac_ids: BO-1-AC-1, BR-003-AC-1
        """
        with self.client.post(
            "/v1/emergency/dispatch",
            json={
                "hospital_id": "hosp-1",
                "severity": "LEVEL_1_CATASTROPHIC",
                "required_abo": "O",
                "required_rh": "NEGATIVE",
                "units_requested": 1,
            },
            name="POST /v1/emergency/dispatch",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 201, 404):
                resp.success()


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    total = environment.stats.total
    if total.num_requests == 0:
        environment.process_exit_code = 1
        return
    err_ratio = total.num_failures / max(total.num_requests, 1)
    if err_ratio > 0.01:
        environment.process_exit_code = 1
