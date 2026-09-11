from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from agentscope.application.ports.metrics import Indicators, TimeseriesPoint
from agentscope.interfaces.api.app import create_app
from agentscope.interfaces.api.dependencies import get_metrics_service


class DummyMetricsService:
    def indicators(self, f):
        return Indicators(
            session_count=12,
            model_call_count=20,
            tool_call_count=15,
            error_count=1,
            total_tokens=None if "no_tokens" in f.sources else 1500,
            prompt_tokens=1000 if "no_tokens" not in f.sources else None,
            completion_tokens=500 if "no_tokens" not in f.sources else None,
            cached_tokens=None,
            total_cost_usd=None,
            cost_is_estimated=False,
            error_rate=0.05,
            cache_hit_ratio=None,
            median_session_duration_ms=4500.0,
        )

    def timeseries(self, f, metric, granularity):
        return [
            TimeseriesPoint(period="2026-09-08", value=10.0),
            TimeseriesPoint(period="2026-09-09", value=None),
        ]

    def tool_usage(self, f):
        return [{"tool_name": "bash", "n_calls": 50, "n_errors": 2, "avg_duration_ms": 1200.0}]


@pytest.fixture
def client():
    app = create_app()
    app.dependency_overrides[get_metrics_service] = lambda: DummyMetricsService()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_get_indicators_filtering_and_null_preservation(client):
    response = client.get("/api/v1/metrics/indicators?sources=no_tokens&sources=tracelab")
    assert response.status_code == 200
    data = response.json()
    assert data["session_count"] == 12
    assert data["total_tokens"] is None
    assert data["total_cost_usd"] is None


def test_get_timeseries_returns_points(client):
    response = client.get("/api/v1/metrics/timeseries?metric=tokens&granularity=day")
    assert response.status_code == 200
    data = response.json()
    assert data["metric"] == "tokens"
    assert data["granularity"] == "day"
    assert len(data["points"]) == 2
    assert data["points"][1]["value"] is None


def test_get_tool_usage(client):
    response = client.get("/api/v1/metrics/tool-usage")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["tool_name"] == "bash"
