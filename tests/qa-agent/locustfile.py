"""qa-agent forkfirst smoke - locustfile. Safe to delete."""
from locust import HttpUser, task, between


class SmokeUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def hello(self):
        pass
