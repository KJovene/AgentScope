from __future__ import annotations

from datetime import datetime
from fastapi.testclient import TestClient
import pytest

from agentscope.application.ports.metrics import (
    Page,
    Paginated,
    SessionDetail,
    SessionListItem,
    TimelineEntry,
)
from agentscope.interfaces.api.app import create_app
from agentscope.interfaces.api.dependencies import get_metrics_service


class DummyMetricsServiceForSessions:
    def sessions(self, f, page: Page):
        sample_item = SessionListItem(
            session_id=1,
            source_name="TraceLab",
            agent_name="swe-agent",
            repository_name="django/django",
            started_at=datetime(2026, 9, 8, 10, 0, 0),
            duration_ms=12000,
            model_call_count=3,
            tool_call_count=5,
            total_tokens=1400,
            total_cost_usd=0.042,
            error_count=0,
        )
        return Paginated(
            items=(sample_item,),
            total=1,
            limit=page.limit,
            offset=page.offset,
        )

    def session_detail(self, session_id: int):
        if session_id != 1:
            return None
        return SessionDetail(
            session_id=1,
            source_name="TraceLab",
            external_id="ext-sess-001",
            agent_name="swe-agent",
            repository_name="django/django",
            started_at=datetime(2026, 9, 8, 10, 0, 0),
            ended_at=datetime(2026, 9, 8, 10, 0, 12),
            duration_ms=12000,
            total_tokens=1400,
            total_cost_usd=0.042,
            error_count=0,
            has_raw_record=True,
            timeline=(
                TimelineEntry(
                    kind="model_call",
                    sequence=1,
                    name="claude-3-5-sonnet",
                    status="success",
                    error_type=None,
                    started_at=datetime(2026, 9, 8, 10, 0, 1),
                    ended_at=datetime(2026, 9, 8, 10, 0, 3),
                    duration_ms=2000,
                    prompt_tokens=800,
                    completion_tokens=200,
                    total_tokens=1000,
                    cost_usd=0.03,
                ),
                TimelineEntry(
                    kind="tool_call",
                    sequence=2,
                    name="bash",
                    status="success",
                    error_type=None,
                    started_at=datetime(2026, 9, 8, 10, 0, 3),
                    ended_at=datetime(2026, 9, 8, 10, 0, 4),
                    duration_ms=1000,
                    prompt_tokens=None,
                    completion_tokens=None,
                    total_tokens=None,
                    cost_usd=None,
                ),
            ),
        )


@pytest.fixture
def client():
    app = create_app()
    app.dependency_overrides[get_metrics_service] = lambda: DummyMetricsServiceForSessions()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_list_sessions_paginated(client):
    response = client.get("/api/v1/sessions?limit=10&offset=0&sources=TraceLab")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["limit"] == 10
    assert data["offset"] == 0
    assert len(data["items"]) == 1
    assert data["items"][0]["session_id"] == 1
    assert data["items"][0]["source_name"] == "TraceLab"


def test_get_session_detail_success(client):
    response = client.get("/api/v1/sessions/1")
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == 1
    assert data["external_id"] == "ext-sess-001"
    assert data["has_raw_record"] is True
    assert len(data["timeline"]) == 2
    assert data["timeline"][0]["kind"] == "model_call"
    assert data["timeline"][1]["kind"] == "tool_call"


def test_get_session_detail_not_found(client):
    response = client.get("/api/v1/sessions/999")
    assert response.status_code == 404
    assert "introuvable" in response.json()["detail"]
