import os
import random
import io
from locust import HttpUser, task, between, events

"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   performance
Source:  test_strategy/plans/cloned_repo__performance.json
Generated: 2024-07-25T17:04:47.348123Z
"""

SERVICE_URL = os.environ.get("SERVICE_URL", "").strip()
P95_MS_THRESHOLD = float(os.environ.get("PERF_P95_MS_THRESHOLD", "500"))
FAIL_RATIO_THRESHOLD = 0.01

class HospitalUser(HttpUser):
    host = SERVICE_URL
    wait_time = between(0.5, 1.5)
    weight = 3

    def on_start(self):
        """Log in as a hospital user to establish a session."""
        self.client.post("/login/hospital", data={"username": "hospital_user", "password": "password"})

    @task
    def create_hospital_demand(self):
        """Load test the hospital demand creation endpoint.

        test_id: cloned_repo__performance__001
        target: POST /hospital/create-demand
        requirement_id: REQ-N-006
        ac_ids: none
        """
        blood_types = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
        dummy_file = io.BytesIO(b"dummy compliance document content")
        dummy_file.name = "compliance.pdf"

        self.client.post(
            "/hospital/create-demand",
            data={
                "blood_type": random.choice(blood_types),
                "units": random.randint(1, 5),
                "notes": "Performance test submission"
            },
            files={
                "document": dummy_file
            },
            name="/hospital/create-demand"
        )

class AdminUser(HttpUser):
    host = SERVICE_URL
    wait_time = between(0.5, 1.5)
    weight = 1

    def on_start(self):
        """Log in as an admin user to establish a session."""
        self.client.post("/login/admin", data={"username": "admin_user", "password": "password"})

    @task
    def verify_hospital_demand(self):
        """Load test the demand verification endpoint.

        test_id: cloned_repo__performance__002
        target: POST /admin/verify/<int:demand_id>
        requirement_id: REQ-N-003
        ac_ids: none
        """
        # Assuming demands with IDs 1-10 exist for verification
        demand_id = random.randint(1, 10)
        self.client.post(
            f"/admin/verify/{demand_id}",
            data={"action": "approve"},
            name="/admin/verify/[demand_id]"
        )

@events.test_stop.add_listener
def enforce_thresholds(environment, **kwargs):
    """Check performance thresholds at the end of the test run."""
    stats = environment.stats.total
    fail_ratio = stats.fail_ratio
    p95_ms = stats.get_response_time_percentile(0.95)

    print(f"P95 response time: {p95_ms:.2f}ms")
    print(f"Failure ratio: {fail_ratio:.2%}")

    if fail_ratio > FAIL_RATIO_THRESHOLD:
        print(f"Test failed: Failure ratio {fail_ratio:.2%} exceeded threshold {FAIL_RATIO_THRESHOLD:.2%}")
        environment.process_exit_code = 1

    if p95_ms and p95_ms >= P95_MS_THRESHOLD:
        print(f"Test failed: P95 response time {p95_ms:.2f}ms exceeded threshold {P95_MS_THRESHOLD:.2f}ms")
        environment.process_exit_code = 1

    if environment.process_exit_code == 0:
        print("Performance thresholds met.")
