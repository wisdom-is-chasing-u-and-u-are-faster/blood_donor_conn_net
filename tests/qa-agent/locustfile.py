import os
import io
from locust import HttpUser, events, task, between

# QA Persona v2 -- auto-generated tests
# Service: cloned_repo
# Suite:   performance
# Source:  test_strategy/plans/cloned_repo__performance.json
# Generated: 2024-05-23T12:34:56Z

SERVICE_URL = os.environ.get("SERVICE_URL", "").strip()
P95_MS_THRESHOLD = float(os.environ.get("PERF_P95_MS_THRESHOLD", "1000"))
FAIL_RATIO_THRESHOLD = 0.01

class HospitalUser(HttpUser):
    """User persona for hospital staff creating blood demands."""
    host = SERVICE_URL
    wait_time = between(0.5, 2.0)

    def on_start(self):
        """Logs in as a hospital user to establish a session."""
        if not self.host:
            print("SERVICE_URL not set, skipping login")
            return
        self.client.post("/login/hospital", {"username": "hospital_user", "password": "password"})

    @task(3)
    def create_demand(self):
        """Simulates a hospital creating a new blood demand.

        test_id: cloned_repo__performance__001
        target: POST /hospital/create-demand
        ac_ids: REQ-N-006-AC-1
        """
        # Create a dummy file in memory for the upload
        dummy_file = io.BytesIO(b"This is a dummy compliance document.")
        dummy_file.name = "compliance.pdf"

        self.client.post(
            "/hospital/create-demand",
            files={"document": dummy_file},
            data={
                "blood_type": "A+",
                "units": "2",
                "notes": "Performance test submission"
            }
        )

    @task(1)
    def view_dashboard(self):
        """Simulates a hospital user viewing their dashboard."""
        self.client.get("/hospital/dashboard", name="/hospital/dashboard")

class AdminUser(HttpUser):
    """User persona for an administrator verifying demands and checking logs."""
    host = SERVICE_URL
    wait_time = between(0.5, 2.0)

    def on_start(self):
        """Logs in as an admin user to establish a session."""
        if not self.host:
            print("SERVICE_URL not set, skipping login")
            return
        self.client.post("/login/admin", {"username": "admin_user", "password": "password"})

    @task(1)
    def verify_demand(self):
        """Simulates an admin approving a pending demand.

        test_id: cloned_repo__performance__002
        target: POST /admin/verify/<int:demand_id>
        ac_ids: REQ-F-017-AC-1
        """
        # The mock data includes a pending demand with id=2
        self.client.post("/admin/verify/2", data={"action": "approve"}, name="/admin/verify/[id]")

    @task(3)
    def get_audit_log(self):
        """Simulates an admin retrieving the audit log.

        test_id: cloned_repo__performance__003
        target: GET /admin/audit-log
        ac_ids: REQ-N-011-AC-1
        """
        self.client.get("/admin/audit-log", name="/admin/audit-log")

    @task(1)
    def view_queue(self):
        """Simulates an admin viewing the verification queue."""
        self.client.get("/admin/queue", name="/admin/queue")

@events.test_stop.add_listener
def enforce_thresholds(environment, **kwargs):
    """Checks if performance thresholds were met and fails the run if not."""
    stats = environment.stats.total
    fail_ratio = stats.fail_ratio
    p95_ms = stats.get_response_time_percentile(0.95)

    print(f"\n--- Performance Summary ---")
    print(f"Total Requests: {stats.num_requests}")
    print(f"Failure Ratio: {fail_ratio:.4f} (Threshold: {FAIL_RATIO_THRESHOLD})")
    if p95_ms is not None:
        print(f"P95 Response Time: {p95_ms:.2f} ms (Threshold: {P95_MS_THRESHOLD:.2f} ms)")
    else:
        print("P95 Response Time: N/A (No successful requests)")
    print("-------------------------\n")

    if fail_ratio > FAIL_RATIO_THRESHOLD:
        print(f"FAIL: Error rate {fail_ratio:.4f} exceeded threshold {FAIL_RATIO_THRESHOLD}")
        environment.process_exit_code = 1

    if p95_ms and p95_ms >= P95_MS_THRESHOLD:
        print(f"FAIL: P95 response time {p95_ms:.2f} ms exceeded threshold {P95_MS_THRESHOLD:.2f} ms")
        environment.process_exit_code = 1

    if environment.process_exit_code == 0:
        print("PASS: All performance thresholds met.")
