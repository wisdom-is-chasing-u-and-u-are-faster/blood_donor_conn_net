"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   performance
Source:  test_strategy/plans/cloned_repo__performance.json
Generated: 2026-10-28T14:50:00Z
"""
import os
import time
from locust import HttpUser, events, task, between

SERVICE_URL = os.environ.get("SERVICE_URL", "").strip()
P95_MS_THRESHOLD = float(os.environ.get("PERF_P95_MS_THRESHOLD", "500"))
FAIL_RATIO_THRESHOLD = 0.01


class TargetUser(HttpUser):
    host = SERVICE_URL
    wait_time = between(0.5, 1.5)

    @task(3)
    def get_login_hospital(self):
        self.client.get("/login/hospital")

    @task(2)
    def get_spatial_candidates(self):
        self.client.get("/v1/spatial/candidates")

    @task(1)
    def get_map_hotspots(self):
        self.client.get("/map/hotspots")


@events.test_stop.add_listener
def enforce_thresholds(environment, **kwargs):
    stats = environment.stats.total
    fail_ratio = stats.fail_ratio
    p95_ms = stats.get_response_time_percentile(0.95)
    if fail_ratio > FAIL_RATIO_THRESHOLD:
        environment.process_exit_code = 1
    if p95_ms and p95_ms >= P95_MS_THRESHOLD:
        environment.process_exit_code = 1
