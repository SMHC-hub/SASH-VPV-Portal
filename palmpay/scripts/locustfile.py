"""Locust load test for PalmPay health + wallet reads (Day 9).

Run (backend must be up):
  pip install locust
  locust -f scripts/locustfile.py --host http://127.0.0.1:8001
"""
from __future__ import annotations

from locust import HttpUser, between, task


class PalmPayHealthUser(HttpUser):
    wait_time = between(0.05, 0.2)

    @task(10)
    def health(self) -> None:
        self.client.get("/api/palmpay/health", name="GET /health")

    @task(1)
    def docs(self) -> None:
        self.client.get("/docs", name="GET /docs")
