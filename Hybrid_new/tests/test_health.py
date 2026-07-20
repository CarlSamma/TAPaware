"""Tests for /health, /metrics, and /api/events endpoints (v3.0)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client without running the full lifespan."""
    from tap.api import app
    return TestClient(app, raise_server_exceptions=False)


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_has_version(self, client):
        resp = client.get("/health")
        data = resp.json()
        assert data["version"] == "3.0.0"

    def test_health_has_components(self, client):
        resp = client.get("/health")
        data = resp.json()
        assert "components" in data
        assert "database" in data["components"]
        assert "llm_client" in data["components"]

    def test_health_has_status(self, client):
        resp = client.get("/health")
        data = resp.json()
        assert data["status"] in ("healthy", "degraded", "unhealthy")


class TestMetricsEndpoint:
    def test_metrics_returns_200(self, client):
        resp = client.get("/metrics")
        assert resp.status_code == 200

    def test_metrics_is_text(self, client):
        resp = client.get("/metrics")
        assert "text/plain" in resp.headers.get("content-type", "")

    def test_metrics_has_help_lines(self, client):
        resp = client.get("/metrics")
        text = resp.text
        assert "# HELP" in text
        assert "# TYPE" in text

    def test_metrics_has_cycle_count(self, client):
        resp = client.get("/metrics")
        assert "tap_cycle_count" in resp.text

    def test_metrics_has_ws_clients(self, client):
        resp = client.get("/metrics")
        assert "tap_ws_clients" in resp.text


class TestEventsEndpoint:
    def test_events_returns_200_or_error(self, client):
        resp = client.get("/api/events")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, (list, dict))
