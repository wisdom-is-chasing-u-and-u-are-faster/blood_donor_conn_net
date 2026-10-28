"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   performance
Source:  test_strategy/plans/cloned_repo__performance.json
Generated: 2026-10-28T06:38:00Z
"""
import os
import time
from locust import HttpUser, events, task, between

SERVICE_URL = os.environ.get("SERVICE_URL", "").strip()
P95_MS_THRESHOLD = float(os.environ.get("PERF_P95_MS_THRESHOLD", "500"))
FAIL_RATIO_THRESHOLD = 0.01


class TargetUser(HttpUser):
    """Load test user for cloned_repo.

    test_id: cloned_repo__performance__001
    target: GET /v1/spatial/candidates
    requirement_id: BO-2, NFR-PERF-01
    ac_ids: BO-2-AC-2, NFR-PERF-01-AC-1, NFR-PERF-01-AC-2
    """
    host = SERVICE_URL
    wait_time = between(0.5, 1.5)

    @task(3)
    def get_spatial_candidates(self):
        self.client.get("/v1/spatial/candidates?latitude=37.7749&longitude=-122.4194&radius_km=15")

    @task(3)
    def get_donor_eligibility(self):
        self.client.get("/v1/donors/marcus_vance/eligibility?donation_type=WHOLE_BLOOD")

    @task(1)
    def get_login_hospital(self):
        self.client.get("/login/hospital")


@events.test_stop.add_listener
def enforce_thresholds(environment, **kwargs):
    stats = environment.stats.total
    fail_ratio = stats.fail_ratio
    p95_ms = stats.get_response_time_percentile(0.95)
    if fail_ratio > FAIL_RATIO_THRESHOLD:
        environment.process_exit_code = 1
    if p95_ms and p95_ms >= P95_MS_THRESHOLD:
        environment.process_exit_code = 1
