"""I4.3 — routes ``POST /analyze`` et ``POST /mappings/{id}/preview`` branchées
sur ``MappingWorkbenchService`` (service simulé + conteneur réel).
"""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from agentscope.application.ports.llm_provider import (
    FieldExplanation,
    MappingProposal,
)
from agentscope.application.use_cases.analyze_unknown_file import AnalysisResult
from agentscope.application.use_cases.preview_mapping import PreviewReport
from agentscope.application.mapping.normalizer import NormalizationResult
from agentscope.domain import (
    FieldProfile,
    FieldProfileSet,
    Provenance,
    Session as SessionEntity,
)
from agentscope.infrastructure.config.settings import Settings
from agentscope.interfaces.api.app import create_app
from agentscope.interfaces.api.dependencies import get_workbench_service

_DEFINITION = {
    "name": "demo",
    "version": 1,
    "source_format": "jsonl",
    "constants": {"source_name": "Demo"},
    "entities": {
        "session": {
            "iterate": {"path": "", "where": []},
            "identity": {"key_fields": ["session_id"]},
            "fields": {"external_id": {"from": "session_id", "transform": "identity"}},
        }
    },
}


class StubWorkbench:
    def analyze(self, filename: str, content: bytes) -> AnalysisResult:
        return AnalysisResult(
            proposal=MappingProposal(
                definition=_DEFINITION,
                explanations=[
                    FieldExplanation(
                        target_field="session.external_id",
                        source_field="session_id",
                        rationale="clé naturelle",
                        confidence=0.9,
                    )
                ],
                ambiguities=["`agent` ambigu"],
                unmapped_fields=["debug"],
            ),
            profile=FieldProfileSet(
                record_count=2,
                fields=(
                    FieldProfile(
                        path="session_id",
                        inferred_type="string",
                        null_ratio=0.0,
                        distinct_count=2,
                        sample_values=("s1", "s2"),
                    ),
                ),
            ),
        )

    def preview(self, filename, content, definition, sample_size=50) -> PreviewReport:
        session = SessionEntity(
            source_name="Demo",
            external_id="s1",
            provenance=Provenance(record_index=0, record_sha256="a"),
        )
        return PreviewReport(
            sampled_count=2,
            result=NormalizationResult(sessions=(session,), missing_info={}),
        )


@pytest.fixture
def client():
    app = create_app()
    app.dependency_overrides[get_workbench_service] = lambda: StubWorkbench()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_analyze_returns_profile_and_proposal(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/analyze",
        files={"file": ("unknown.jsonl", b'{"session_id": "s1"}\n', "application/jsonl")},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["profile"]["record_count"] == 2
    assert body["profile"]["fields"][0]["path"] == "session_id"
    assert body["proposal"]["definition"]["name"] == "demo"
    assert body["proposal"]["ambiguities"] == ["`agent` ambigu"]
    assert body["proposal"]["explanations"][0]["confidence"] == 0.9


def test_preview_returns_rows_and_rejects(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/mappings/draft/preview",
        data={"definition": json.dumps(_DEFINITION), "sample_size": "10"},
        files={"file": ("sample.jsonl", b'{"session_id": "s1"}\n', "application/jsonl")},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["rows"][0]["entity"] == "session"
    assert body["rows"][0]["row"]["external_id"] == "s1"
    assert body["rejects"] == []


def test_preview_rejects_invalid_definition_json(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/mappings/draft/preview",
        data={"definition": "{not json"},
        files={"file": ("sample.jsonl", b"{}", "application/jsonl")},
    )
    assert resp.status_code == 422


def test_analyze_with_real_container_and_fake_provider_is_400() -> None:
    """Sans clé ni fournisseur réel : le FakeLLMProvider produit un mapping non
    conforme → erreur métier explicite (problem+json)."""
    app = create_app(Settings(llm_provider="fake"))
    with TestClient(app) as c:
        resp = c.post(
            "/api/v1/analyze",
            files={"file": ("unknown.jsonl", b'{"session_id": "s1"}\n', "application/jsonl")},
        )
    assert resp.status_code == 400
    assert resp.headers["content-type"] == "application/problem+json"
