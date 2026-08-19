"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   performance
Source:  test_strategy/plans/cloned_repo__performance.json
Generated: 2024-05-23T10:30:00Z
"""
import os
import random
from locust import HttpUser, events, task, between
from io import BytesIO

SERVICE_URL = os.environ.get("SERVICE_URL", "").strip()
P95_MS_THRESHOLD = float(os.environ.get("PERF_P95_MS_THRESHOLD", "500"))
FAIL_RATIO_THRESHOLD = float(os.environ.get("PERF_FAIL_RATIO_THRESHOLD", "0.01"))

class HospitalUser(HttpUser):
    """
    User persona for a hospital staff member who creates blood demands.
    This user logs in once and then repeatedly calls the create-demand endpoint.
    """
    host = SERVICE_URL
    wait_time = between(1, 3)

    def on_start(self):
        """Logs in as a hospital user to establish a session."""
        self.client.post("/login/hospital", {
            "username": "hospital_perf_user",
            "password": "password"
        })

    @task
    def create_demand_task(self):
        """
        Load test demand creation endpoint.

        test_id: cloned_repo__performance__001
        target: POST /hospital/create-demand
        requirement_id: no requirement
        ac_ids: none
        """
        dummy_file = BytesIO(b"fake compliance document content for performance test")
        
        self.client.post(
            "/hospital/create-demand",
            data={
                "blood_type": random.choice(["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]),
                "units": random.randint(1, 5),
                "notes": "Performance test demand"
            },
            files={"document": ("compliance.pdf", dummy_file, "application/pdf")},
            name="/hospital/create-demand"
        )

class AdminUser(HttpUser):
    """
    User persona for an administrator who verifies blood demands.
    This user logs in once and then repeatedly verifies demands.
    """
    host = SERVICE_URL
    wait_time = between(0.5, 2)

    def on_start(self):
        """Logs in as an admin user to establish a session."""
        self.client.post("/login/admin", {
            "username": "admin_perf_user",
            "password": "password"
        })

    @task
    def verify_demand_task(self):
        """
        Load test demand verification endpoint.

        test_id: cloned_repo__performance__002
        target: POST /admin/verify/<int:demand_id>
        requirement_id: no requirement
        ac_ids: none
        """
        # The mock app has demands with IDs 1 (Approved) and 2 (Pending).
        # We target ID 2 to have a valid target for approve/reject actions.
        demand_id_to_verify = 2
        action = random.choice(["approve", "reject"])

        self.client.post(
            f"/admin/verify/{demand_id_to_verify}",
            data={"action": action},
            name="/admin/verify/[demand_id]"
        )

@events.test_stop.add_listener
def enforce_thresholds(environment, **kwargs):
    """
    Checks if the performance thresholds were met and sets the exit code accordingly.
    This allows the test run to fail in a CI/CD pipeline if performance degrades.
    """
    stats = environment.stats.total
    fail_ratio = stats.fail_ratio
    p95_ms = stats.get_response_time_percentile(0.95)

    if fail_ratio > FAIL_RATIO_THRESHOLD:
        print(f"Test failed: Failure ratio {fail_ratio:.2f} > {FAIL_RATIO_THRESHOLD:.2f}")
        environment.process_exit_code = 1

    if p95_ms and p95_ms > P95_MS_THRESHOLD:
        print(f"Test failed: P95 response time {p95_ms:.2f}ms > {P95_MS_THRESHOLD:.2f}ms")
        environment.process_exit_code = 1

    if environment.process_exit_code == 0:
        print("Performance thresholds met successfully.")
